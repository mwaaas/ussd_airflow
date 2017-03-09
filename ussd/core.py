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

_registered_ussd_handlers = {}
_registered_filters = {}


class MissingAttribute(Exception):
    pass


class InvalidAttribute(Exception):
    pass


class DuplicateSessionId(Exception):
    pass


def register_filter(func_name, *args, **kwargs):
    filter_name = func_name.__name__
    _registered_filters[filter_name] = func_name


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

            # check inactivity or if session has been closed
            inactivity_duration = (datetime.now() - session.get(
                ussd_airflow_variables.last_update,
                timezone.make_naive(session_mapping.updated_at))
                                   ).total_seconds()
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


class UssdHandlerMetaClass(type):

    def __init__(cls, name, bases, attr, **kwargs):
        super(UssdHandlerMetaClass, cls).__init__(
            name, bases, attr)

        abstract = attr.get('abstract', False)

        if not abstract:
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
                 initial_screen: dict, template_namespace=None,
                 logger=None):
        self.ussd_request = ussd_request
        self.handler = handler
        self.screen_content = screen_content

        self.SINGLE_VAR = re.compile(r"^%s\s*(\w*)\s*%s$" % (
            '{{', '}}'))
        self.clean_regex = re.compile(r'^{{\s*(\S*)\s*}}$')
        self.logger = logger or get_logger(__name__).bind(
            **ussd_request.all_variables())
        self.template_namespace = template_namespace
        self.initial_screen = initial_screen

        if template_namespace is not None:
            self.template_namespace = staticconf.config.\
                configuration_namespaces[self.template_namespace].\
                configuration_values

        # initialize jinja2 environment
        self.env = Environment(keep_trailing_newline=True)
        self.env.filters.update(_registered_filters)

    def handle(self):
        if not self.ussd_request.input:
            ussd_response = self.show_ussd_content()
            return ussd_response if isinstance(ussd_response, UssdResponse) \
                else UssdResponse(str(ussd_response))
        return self.handle_ussd_input(self.ussd_request.input)

    def get_text_limit(self):
        return self.initial_screen.get("ussd_text_limit",
                                       ussd_airflow_variables.ussd_text_limit)

    def show_ussd_content(self, **kwargs):
        raise NotImplementedError

    def handle_ussd_input(self, ussd_input):
        raise NotImplementedError

    def _get_session_items(self) -> dict:
        return dict(iter(self.ussd_request.session.items()))

    def _get_context(self, extra_context=None):
        context = self._get_session_items()
        context.update(
            dict(
                ussd_request=self.ussd_request.all_variables()
            )
        )
        context.update(
            dict(os.environ)
        )
        if self.template_namespace:
            context.update(self.template_namespace)
        if extra_context is not None:
            context.update(extra_context)

        # add timestamp in the context
        context.update(
            dict(now=datetime.now())
        )
        return context

    def _render_text(self, text, context=None, extra=None, encode=None):
        if context is None:
            context = self._get_context()

        if extra:
            context.update(extra)

        template = self.env.from_string(text or '')
        text = template.render(context)
        return json.dumps(text) if encode is 'json' else text

    def get_text(self, text_context=None):
        text_context = self.screen_content.get('text')\
                       if text_context is None \
                       else text_context

        if isinstance(text_context, dict):
            language = self.ussd_request.language \
                   if self.ussd_request.language \
                          in text_context.keys() \
                   else self.ussd_request.default_language

            text_context = text_context[language]

        return self._render_text(
            text_context
        )

    def evaluate_jija_expression(self, expression, extra_context=None,
                                 lazy_evaluating=False):
        if not isinstance(expression, str) or \
                (lazy_evaluating and not self._contains_vars(expression)):
            return expression

        context = self._get_context(extra_context=extra_context)
        expression = expression.replace("{{", "").replace("}}", "")
        try:
            expr = self.env.compile_expression(
                expression
            )
        except TemplateSyntaxError:
            return []
        return expr(context)

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

    def get_loop_items(self):
        loop_items = self.evaluate_jija_expression(
            self.screen_content["with_items"]
        ) if self.screen_content.get("with_items") else [0] or [0]
        return loop_items


class UssdView(APIView):
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
    template_namespace = None

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

        ussd_request.session.update(ussd_request.all_variables())

        self.logger.debug('gateway_request', text=ussd_request.input)

        # Invoke handlers
        ussd_response = self.run_handlers(ussd_request)
        ussd_request.session[ussd_airflow_variables.last_update] = \
            datetime.now()
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
            start_time = ussd_request.session["ussd_interaction"][-1][
                "start_time"]
            end_time = datetime.now()
            # Report in milliseconds
            duration = (end_time - start_time).total_seconds() * 1000
            ussd_request.session["ussd_interaction"][-1].update(
                {
                    "input": ussd_request.input,
                    "end_time": end_time,
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
                template_namespace=ussd_request.session.get(
                    'template_namespace', None
                ),
                initial_screen=self.initial_screen,
                logger=self.logger
            ).handle()

        ussd_request.session['_ussd_state']['next_screen'] = handler

        ussd_request.session['ussd_interaction'].append(
            {
                "screen_name": handler,
                "screen_text": str(ussd_response),
                "input": ussd_request.input,
                "start_time": datetime.now()
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