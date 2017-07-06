"""
Comming soon
"""
from urllib.parse import unquote
from copy import copy, deepcopy
from rest_framework.views import APIView
from django.http import HttpResponse
from structlog import get_logger
import staticconf
from django.conf import settings
from importlib import import_module
from django.contrib.sessions.backends import signed_cookies
from django.contrib.sessions.backends.base import CreateError
from jinja2 import Template, Environment, TemplateSyntaxError
from .screens.serializers import UssdBaseSerializer
from rest_framework.serializers import SerializerMetaclass
import re
import json
import os
from configure import Configuration
from datetime import datetime
from ussd.models import SessionLookup
from annoying.functions import get_object_or_None
from ussd import defaults as ussd_airflow_variables
from django.utils import timezone
import requests
import inspect
from ussd.tasks import report_session
from ussd import utilities

_registered_ussd_handlers = {}
_registered_filters = {}
_customer_journey_files = []
_built_in_functions = {}

# initialize jinja2 environment
env = Environment(keep_trailing_newline=True)
env.filters.update(_registered_filters)


class MissingAttribute(Exception):
    pass


class InvalidAttribute(Exception):
    pass


class DuplicateSessionId(Exception):
    pass


def register_filter(func_name, *args, **kwargs):
    filter_name = func_name.__name__
    _registered_filters[filter_name] = func_name


def register_function(func_name, *args, **kwargs):
    function_name = func_name.__name__
    _built_in_functions[function_name] = func_name


def get_session_engine():
    session_engine = import_module(getattr(settings, "USSD_SESSION_ENGINE",
                                           settings.SESSION_ENGINE))
    if session_engine is signed_cookies:
        raise ValueError("You cannot use channels session "
                         "functionality with signed cookie sessions!")
    return session_engine


def ussd_session(session_id):
    session = get_session_engine().SessionStore(session_key=session_id)
    session._session.keys()
    session._session_key = session_id

    # If the session does not already exist, save to force our
    # session key to be valid.
    if not session.exists(session.session_key):
        try:
            session.save(must_create=True)
        except CreateError:
            # Session wasn't unique, so another consumer is doing the same thing
            raise DuplicateSessionId("another sever is working"
                                     "on this session id")
    return session


def generate_session_id():
    session_store = get_session_engine().SessionStore()
    session_store.save()  # generate session_key
    return session_store.session_key


def load_yaml(file_path, namespace):
    file_path = Template(file_path).render(os.environ)
    yaml_dict = Configuration.from_file(
            os.path.abspath(file_path),
            configure=False
        )
    staticconf.DictConfiguration(
        yaml_dict,
        namespace=namespace,
        flatten=False)


class UssdRequest(object):
    """
    :param session_id:
        used to get session or create session if does not
        exits.

        If session is less than 8 we add *s* to make the session
        equal to 8

    :param phone_number:
        This the user identifier

    :param input:
        This ussd input the user has entered.

    :param language:
        Language to use to display ussd

    :param kwargs:
        Extra arguments.
        All the extra arguments will be set to the self attribute

        For instance:

        .. code-block:: python

            from ussd.core import UssdRequest

            ussdRequest = UssdRequest(
                '12345678', '702729654', '1', 'en',
                name='mwas'
            )

            # accessing kwarg argument
            ussdRequest.name
    """
    def __init__(self, session_id, phone_number,
                 ussd_input, language, default_language=None,
                 use_built_in_session_management=False,
                 expiry=180,
                 **kwargs):
        """
        :param session_id: Used to maintain session 
        :param phone_number: user dialing in   
        :param ussd_input: input entered by user
        :param language: language to be used
        :param default_language: language to used
        :param use_built_in_session_management: Used to enable ussd_airflow to 
            manage its own session, by default its set to False, is set to true 
        then the session_id should be None and expiry can't be None. 
        :param expiry: Its only used if use_built_in_session_management has
        been enabled. 
        :param kwargs: All other extra arguments
        """

        self.expiry = expiry
        # A bit of defensive programming to make sure
        # session_built_in_management has been initiated
        if use_built_in_session_management and session_id is not None:
            raise InvalidAttribute("When using built_in_session_management "
                                   "has been enabled session_id should "
                                   "be None")
        if use_built_in_session_management and expiry is None:
            raise InvalidAttribute("When built_in_session_management has been"
                                   "enabled expiry should not be None")
        # session id should not be None if built in session management
        # has not been enabled
        if session_id is None and not use_built_in_session_management:
            raise InvalidAttribute(
                "Session id should not be None if built in session management "
                "has not been enabled"
            )

        if use_built_in_session_management:
            session_id = self.get_or_create_session_id(phone_number)
        else:
            # if session id is less than 8 should provide the
            # suplimentary characters with 's'
            if len(str(
                    session_id)) < 8 and not use_built_in_session_management:
                session_id = 's' * (8 - len(str(session_id))) + session_id

        self.phone_number = phone_number
        self.input = unquote(ussd_input)
        self.language = language
        self.default_language = default_language or 'en'
        self.session_id = session_id
        self.session = ussd_session(self.session_id)

        for key, value in kwargs.items():
            setattr(self, key, value)


    def forward(self, handler_name):
        """
        Forwards a copy of the current request to a new
        handler. Clears any input, as it is assumed this was meant for
        the previous handler. If you need to pass info between
        handlers, do it through the USSD session.
        """
        new_request = copy(self)
        new_request.input = ''
        return new_request, handler_name

    def all_variables(self):
        all_variables = copy(self.__dict__)

        # delete session if it exist
        all_variables.pop("session", None)

        return all_variables

    def get_or_create_session_id(self, user_id):
        session_mapping = get_object_or_None(SessionLookup, user_id=user_id)

        # if its missing create a new one.
        if session_mapping is None:
            session_mapping = SessionLookup.objects.create(
                user_id=user_id,
                session_id=generate_session_id()
            )
        else:
            session = ussd_session(session_mapping.session_id)

            # get last time session was updated
            if session.get(ussd_airflow_variables.last_update):
                last_updated = utilities.string_to_datetime(
                    session[ussd_airflow_variables.last_update])
            else:
                last_updated = timezone.make_naive(session_mapping.updated_at)

            # check inactivity or if session has been closed
            inactivity_duration = (datetime.now() - last_updated).total_seconds()
            if inactivity_duration > self.expiry or \
                    session.get(ussd_airflow_variables.expiry):

                # update session_mapping with the new session_id
                session_mapping.session_id = generate_session_id()
                session_mapping.save()

        return session_mapping.session_id




class UssdResponse(object):
    """
    :param text:
        This is the ussd text to display to the user
    :param status:
        This shows the status of ussd session.

        True -> to continue with the session

        False -> to end the session
    :param session:
        This is the session object of the ussd session
    """
    def __init__(self, text, status=True, session=None):
        self.text = text
        self.status = status
        self.session = session

    def dumps(self):
        return self.text

    def __str__(self):
        return self.dumps()


class UssdViewMetaClass(type):
    def __init__(cls,name,bases,attr,**kwargs):
        super(UssdViewMetaClass,cls).__init__(
            name,bases,attr)
        path = getattr(cls,'customer_journey_conf')
        if path is not None:
            _customer_journey_files.append(getattr(cls,'customer_journey_conf'))


class UssdHandlerMetaClass(type):

    def __init__(cls, name, bases, attr, **kwargs):
        super(UssdHandlerMetaClass, cls).__init__(
            name, bases, attr)

        abstract = attr.get('abstract', False)

        if not abstract or attr.get('screen_type', '') == 'custom_screen':
            required_attributes = ('screen_type', 'serializer', 'handle')

            # check all attributes have been defined
            for attribute in required_attributes:
                if attribute not in attr and not hasattr(cls, attribute):
                    raise MissingAttribute(
                        "{0} is required in class {1}".format(
                            attribute, name)
                    )

            if not isinstance(attr['serializer'], SerializerMetaclass):
                raise InvalidAttribute(
                    "serializer should be a "
                    "instance of {serializer}".format(
                        serializer=SerializerMetaclass)
                )
            _registered_ussd_handlers[attr['screen_type']] = cls


class UssdHandlerAbstract(object, metaclass=UssdHandlerMetaClass):
    abstract = True

    def __init__(self, ussd_request: UssdRequest,
                 handler: str, screen_content: dict,
                 initial_screen: dict, logger=None):
        self.ussd_request = ussd_request
        self.handler = handler
        self.screen_content = screen_content

        self.SINGLE_VAR = re.compile(r"^%s\s*(\w*)\s*%s$" % (
            '{{', '}}'))
        self.clean_regex = re.compile(r'^{{\s*(\S*)\s*}}$')
        self.logger = logger or get_logger(__name__).bind(
            handler=self.handler,
            screen_type=getattr(self, 'screen_type', 'custom_screen'),
            **ussd_request.all_variables(),
        )
        self.initial_screen = initial_screen

        self.pagination_config = self.initial_screen.get('pagination_config',
                                                         {})

        self.pagination_more_option = self._add_end_line(
            self.get_text(
                self.pagination_config.get('more_option', "more\n")
            )
        )
        self.pagination_back_option = self._add_end_line(
            self.get_text(
                self.pagination_config.get('back_option', "back\n")
            )
        )
        self.ussd_text_limit = self.pagination_config.\
            get("ussd_text_limit", ussd_airflow_variables.ussd_text_limit)

    def handle(self):
        if not self.ussd_request.input:
            ussd_response = self.show_ussd_content()
            return ussd_response if isinstance(ussd_response, UssdResponse) \
                else UssdResponse(str(ussd_response))
        return self.handle_ussd_input(self.ussd_request.input)

    def get_text_limit(self):
        return self.ussd_text_limit

    def show_ussd_content(self, **kwargs):
        raise NotImplementedError

    def handle_ussd_input(self, ussd_input):
        raise NotImplementedError

    def route_options(self, route_options=None):
        """
        iterates all the options executing expression comand.
        """
        if route_options is None:
            route_options = self.screen_content["next_screen"]

        if isinstance(route_options, str):
            return self.ussd_request.forward(route_options)

        loop_items = [0]
        if self.screen_content.get("with_items"):
            loop_items = self.evaluate_jija_expression(
                self.screen_content["with_items"],
                session=self.ussd_request.session
            ) or loop_items

        for item in loop_items:
            extra_context = {
                "item": item
            }
            if isinstance(loop_items, dict):
                extra_context.update(
                    dict(
                        key=item,
                        value=loop_items[item],
                        item={item: loop_items[item]}
                    )
                )

            for option in route_options:
                if self.evaluate_jija_expression(
                        option.get('expression') or option['condition'],
                        session=self.ussd_request.session,
                        extra_context=extra_context
                ):
                    return self.ussd_request.forward(option['next_screen'])
        return self.ussd_request.forward(
            self.screen_content['default_next_screen']
        )
    @staticmethod
    def get_session_items(session) -> dict:
        return dict(iter(session.items()))

    @classmethod
    def get_context(cls, session, extra_context=None):
        context = cls.get_session_items(session)

        context.update(
            dict(os.environ)
        )

        if extra_context is not None:
            context.update(extra_context)

        # add timestamp in the context
        context.update(
            dict(now=datetime.now())
        )

        # add all built in functions
        context.update(
            _built_in_functions
        )
        return context

    @staticmethod
    def render_text(session, text, context=None, extra=None, encode=None):
        if context is None:
            context = UssdHandlerAbstract.get_context(
                session
            )

        if extra:
            context.update(extra)

        template = env.from_string(text or '')
        text = template.render(context)
        return json.dumps(text) if encode is 'json' else text

    def get_text(self, text_context=None):
        text_context = self.screen_content.get('text')\
                       if text_context is None \
                       else text_context

        if isinstance(text_context, dict):
            language = (self.ussd_request.session.get('override_language') or self.ussd_request.language) \
                   if self.ussd_request.language \
                          in text_context.keys() \
                   else self.ussd_request.default_language
            text_context = text_context[language]


        return self.render_text(
            self.ussd_request.session,
            text_context
        )

    @classmethod
    def evaluate_jija_expression(cls, expression, session,
                                 extra_context=None,
                                 lazy_evaluating=False,
                                 default=None):
        if not isinstance(expression, str) or \
                (lazy_evaluating and not cls._contains_vars(
                    expression)):
            return expression

        context = cls.get_context(
            session, extra_context=extra_context)

        try:
            expr = env.compile_expression(
                expression.replace("{{", "").replace("}}", "")
            )
            return expr(context)
        except Exception:
            try:
                return env.from_string(expression or '').render(context)
            except Exception:
                return default

    @classmethod
    def validate(cls, screen_name: str, ussd_content: dict) -> (bool, dict):
        screen_content = ussd_content[screen_name]
        # adding screen name in context might be needed by validator
        ussd_content['screen_name'] = screen_name
        validation = cls.serializer(data=screen_content,
                                     context=ussd_content)
        del ussd_content['screen_name']
        if validation.is_valid():
            return True, {}
        return False, validation.errors

    @staticmethod
    def _contains_vars(data):
        '''
        returns True if the data contains a variable pattern
        '''
        if isinstance(data, str):
            for marker in ('{%', '{{', '{#'):
                if marker in data:
                    return True
        return False

    @staticmethod
    def _add_end_line(text):
        if text and '\n' not in text:
            text += '\n'
        return text

    def get_loop_items(self):
        loop_items = self.evaluate_jija_expression(
            self.screen_content["with_items"],
            session=self.ussd_request.session
        ) if self.screen_content.get("with_items") else [0] or [0]
        return loop_items

    @classmethod
    def render_request_conf(cls, session, data):
        if isinstance(data, str):
            jinja_results = cls.evaluate_jija_expression(data, session)
            return data if jinja_results is None else jinja_results

        elif isinstance(data, list):
            list_data = []
            for i in data:
                list_data.append(cls.render_request_conf(
                    session, i))

            return list_data

        elif isinstance(data, dict):
            dict_data = {}
            for key, value in data.items():
                dict_data.update(
                    {key: cls.render_request_conf(
                        session, value)}
                )
            return dict_data
        else:
            return data

    @staticmethod
    def get_variables_from_response_obj(response):
        response_varialbes = {}

        for i in inspect.getmembers(response):
            # Ignores anything starting with underscore
            # (that is, private and protected attributes)
            if not i[0].startswith('_'):
                # Ignores methods
                if not inspect.ismethod(i[1]) and \
                                type(i[1]) in \
                                (str, dict, int, dict, float, list, tuple):
                    if len(i) == 2:
                        response_varialbes.update(
                            {i[0]: i[1]}
                        )

        try:
            response_content = json.loads(response.content.decode())
        except json.JSONDecodeError:
            response_content = response.content.decode()

        if isinstance(response_content, dict):
            response_varialbes.update(
                response_content
            )

        # update content to save the one that has been decoded
        response_varialbes.update(
            {"content": response_content}
        )

        return response_varialbes
    @classmethod
    def make_request(cls, http_request_conf, response_session_key_save,
                     session, logger=None
                     ):
        logger = logger or get_logger(__name__).bind(
            action="make_request",
            session_id=session.session_key
        )
        logger.info("sending_request", **http_request_conf)
        response = requests.request(**http_request_conf)
        logger.info("response", status_code=response.status_code,
                         content=response.content)

        response_to_save = cls.get_variables_from_response_obj(response)

        # save response in session
        session[response_session_key_save] = response_to_save

        return response

    @staticmethod
    def fire_ussd_report_session_task(initial_screen: dict, session_id: str,
                            support_countdown=True):
        ussd_report_session = initial_screen['ussd_report_session']
        args = (session_id,)
        kwargs = {'screen_content': initial_screen}
        keyword_args = ussd_report_session.get("async_parameters",
                                               {"countdown": 900}).copy()
        if not support_countdown and keyword_args.get('countdown'):
            del keyword_args['countdown']

        report_session.apply_async(
            args=args,
            kwargs=kwargs,
            **keyword_args
        )


class UssdView(APIView, metaclass=UssdViewMetaClass):
    """
    To create Ussd View requires the following things:
        - Inherit from **UssdView** (Mandatory)
            .. code-block:: python

                from ussd.core import UssdView

        - Define Http method either **get** or **post** (Mandatory)
            The http method should return Ussd Request

                .. autoclass:: ussd.core.UssdRequest

        - define this varialbe *customer_journey_conf*
            This is the path of the file that has ussd screens
            If you want your file to be dynamic implement the
            following method **get_customer_journey_conf** it
            will be called by request object

        - define this variable *customer_journey_namespace*
            Ussd_airflow uses this namespace to save the
            customer journey content in memory. If you want
            customer_journey_namespace to be dynamic implement
            this method **get_customer_journey_namespace** it
            will be called with request object

        - override HttpResponse
            In ussd airflow the http method return UssdRequest object
            not Http response. Then ussd view gets UssdResponse object
            and convert it to HttpResponse. The default HttpResponse
            returned is a normal HttpResponse with body being ussd text

            To override HttpResponse returned define this method.
            **ussd_response_handler** it will be called with
            **UssdResponse** object.

                .. autoclass:: ussd.core.UssdResponse

    Example of Ussd view

    .. code-block:: python

        from ussd.core import UssdView, UssdRequest


        class SampleOne(UssdView):

            def get(self, req):
                return UssdRequest(
                    phone_number=req.data['phoneNumber'].strip('+'),
                    session_id=req.data['sessionId'],
                    ussd_input=text,
                    service_code=req.data['serviceCode'],
                    language=req.data.get('language', 'en')
                )

    Example of Ussd View that defines its own HttpResponse.

    .. code-block:: python

        from ussd.core import UssdView, UssdRequest


        class SampleOne(UssdView):

            def get(self, req):
                return UssdRequest(
                    phone_number=req.data['phoneNumber'].strip('+'),
                    session_id=req.data['sessionId'],
                    ussd_input=text,
                    service_code=req.data['serviceCode'],
                    language=req.data.get('language', 'en')
                )

            def ussd_response_handler(self, ussd_response):
                    if ussd_response.status:
                        res = 'CON' + ' ' + str(ussd_response)
                        response = HttpResponse(res)
                    else:
                        res = 'END' + ' ' + str(ussd_response)
                        response = HttpResponse(res)
                    return response
    """
    customer_journey_conf = None
    customer_journey_namespace = None

    def initial(self, request, *args, **kwargs):
        # initialize restframework
        super(UssdView, self).initial(request, args, kwargs)

        # initialize ussd
        self.ussd_initial(request)

    def ussd_initial(self, request, *args, **kwargs):
        if hasattr(self, 'get_customer_journey_conf'):
            self.customer_journey_conf = self.get_customer_journey_conf(
                request
            )
        if hasattr(self, 'get_customer_journey_namespace'):
            self.customer_journey_namespace = \
                self.get_customer_journey_namespace(request)

        if self.customer_journey_conf is None \
                or self.customer_journey_namespace is None:
            raise MissingAttribute("attribute customer_journey_conf and "
                                   "customer_journey_namespace are required")

        if not self.customer_journey_namespace in \
                staticconf.config.configuration_namespaces:
            load_yaml(
                self.customer_journey_conf,
                self.customer_journey_namespace
            )

        # confirm variable template has been loaded
        # get initial screen

        initial_screen = staticconf.read(
            "initial_screen",
            namespace=self.customer_journey_namespace)

        if isinstance(initial_screen, dict) and \
                initial_screen.get('variables'):
            variable_conf = initial_screen['variables']
            file_path = variable_conf['file']
            namespace = variable_conf['namespace']
            if not namespace in \
                    staticconf.config.configuration_namespaces:
                load_yaml(file_path, namespace)

        self.initial_screen = initial_screen \
            if isinstance(initial_screen, dict) \
            else {"initial_screen": initial_screen}

    def finalize_response(self, request, response, *args, **kwargs):

        if isinstance(response, UssdRequest):
            self.logger = get_logger(__name__).bind(**response.all_variables())
            try:
                ussd_response = self.ussd_dispatcher(response)
            except Exception as e:
                if settings.DEBUG:
                    ussd_response = UssdResponse(str(e))
            return self.ussd_response_handler(ussd_response)
        return super(UssdView, self).finalize_response(
            request, response, args, kwargs)

    def ussd_response_handler(self, ussd_response):
        return HttpResponse(str(ussd_response))

    def ussd_dispatcher(self, ussd_request):

        # Clear input and initialize session if we are starting up
        if '_ussd_state' not in ussd_request.session:
            ussd_request.input = ''
            ussd_request.session['_ussd_state'] = {'next_screen': ''}
            ussd_request.session['ussd_interaction'] = []
            ussd_request.session['posted'] = False
            ussd_request.session['submit_data'] = {}
            ussd_request.session['session_id'] = ussd_request.session_id
            ussd_request.session['phone_number'] = ussd_request.phone_number

        # update ussd_request variable to session and template variables
        # to be used later for jinja2 evaluation
        ussd_request.session.update(ussd_request.all_variables())

        # for backward compatibility
        # there are some jinja template using ussd_request
        # eg. {{ussd_request.session_id}}
        ussd_request.session.update(
            {"ussd_request": ussd_request.all_variables()}
        )

        self.logger.debug('gateway_request', text=ussd_request.input)

        # Invoke handlers
        ussd_response = self.run_handlers(ussd_request)
        ussd_request.session[ussd_airflow_variables.last_update] = \
            utilities.datetime_to_string(datetime.now())
        # Save session
        ussd_request.session.save()
        self.logger.debug('gateway_response', text=ussd_response.dumps(),
                     input="{redacted}")

        return ussd_response

    def run_handlers(self, ussd_request):

        handler = ussd_request.session['_ussd_state']['next_screen'] \
            if ussd_request.session.get('_ussd_state', {}).get('next_screen') \
            else "initial_screen"


        ussd_response = (ussd_request, handler)

        if handler != "initial_screen":
            # get start time
            start_time = utilities.string_to_datetime(
                ussd_request.session["ussd_interaction"][-1]["start_time"])
            end_time = datetime.now()
            # Report in milliseconds
            duration = (end_time - start_time).total_seconds() * 1000
            ussd_request.session["ussd_interaction"][-1].update(
                {
                    "input": ussd_request.input,
                    "end_time": utilities.datetime_to_string(end_time),
                    "duration": duration
                }
            )

        # Handle any forwarded Requests; loop until a Response is
        # eventually returned.
        while not isinstance(ussd_response, UssdResponse):
            ussd_request, handler = ussd_response

            screen_content = staticconf.read(
                handler,
                namespace=self.customer_journey_namespace)

            screen_type = 'initial_screen' \
                if handler == "initial_screen" and \
                   isinstance(screen_content, str) \
                else screen_content['type']

            ussd_response = _registered_ussd_handlers[screen_type](
                ussd_request,
                handler,
                screen_content,
                initial_screen=self.initial_screen,
                logger=self.logger
            ).handle()

        ussd_request.session['_ussd_state']['next_screen'] = handler

        ussd_request.session['ussd_interaction'].append(
            {
                "screen_name": handler,
                "screen_text": str(ussd_response),
                "input": ussd_request.input,
                "start_time": utilities.datetime_to_string(datetime.now())
            }
        )
        # Attach session to outgoing response
        ussd_response.session = ussd_request.session

        return ussd_response

    @staticmethod
    def validate_ussd_journey(ussd_content: dict) -> (bool, dict):
        errors = {}
        is_valid = True

        # should define initial screen
        if not 'initial_screen' in ussd_content.keys():
            is_valid = False
            errors.update(
                {'hidden_fields': {
                    "initial_screen": ["This field is required."]
                }}
            )
        for screen_name, screen_content in ussd_content.items():
            # all screens should have type attribute
            if screen_name == "initial_screen" and \
                    isinstance(screen_content, str):
                if not screen_content in ussd_content.keys():
                    is_valid = False
                    errors.update(
                        dict(
                            screen_name="Screen not available"
                        )
                    )
                continue

            screen_type = screen_content.get('type')

            # all screen should have type field.
            serialize = UssdBaseSerializer(data=screen_content,
                                           context=ussd_content)
            base_validation = serialize.is_valid()

            if serialize.errors:
                errors.update(
                    {screen_name: serialize.errors}
                )

            if not base_validation:
                is_valid = False
                continue

            # all screen type have their handlers
            handlers = _registered_ussd_handlers[screen_type]

            screen_validation, screen_errors = handlers.validate(
                screen_name,
                ussd_content
            )
            if screen_errors:
                errors.update(
                    {screen_name: screen_errors}
                )

            if not screen_validation:
                is_valid = screen_validation

        return is_valid, errors