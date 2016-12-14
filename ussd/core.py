"""

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
from jinja2 import Template
from .screens.serializers import UssdBaseSerializer
from rest_framework.serializers import SerializerMetaclass
import re
import json

_registered_ussd_handlers = {}


class MissingAttribute(Exception):
    pass


class InvalidAttribute(Exception):
    pass


class DuplicateSessionId(Exception):
    pass


def ussd_session(session_id):
    # Make a session storage
    session_engine = import_module(getattr(settings, "USSD_SESSION_ENGINE", settings.SESSION_ENGINE))
    if session_engine is signed_cookies:
        raise ValueError("You cannot use channels session functionality with signed cookie sessions!")
    # Force the instance to load in case it resets the session when it does
    session = session_engine.SessionStore(session_key=session_id)
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


class UssdRequest(object):

    def __init__(self, session_id, phone_number,
                 ussd_input, language, **kwargs):
        """Represents a USSD request"""

        self.phone_number = phone_number
        self.input = unquote(ussd_input)
        self.language = language
        # if session id is less than 8 should provide the
        # suplimentary characters with 's'
        if len(str(session_id)) < 8:
            session_id = 's' * (8 - len(str(session_id))) + session_id
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
        all_variables = deepcopy(self.__dict__)

        # delete session if it exist
        all_variables.pop("session", None)

        return all_variables


class UssdResponse(object):
    """Represents a USSD response"""
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
                 handler: str, screen_content: dict, logger=None):
        self.ussd_request = ussd_request
        self.handler = handler
        self.screen_content = screen_content

        self.SINGLE_VAR = re.compile(r"^%s\s*(\w*)\s*%s$" % (
            '{{', '}}'))
        self.logger = logger or get_logger(__name__).bind(**ussd_request.all_variables())

    def _get_session_items(self) -> dict:
        return dict(iter(self.ussd_request.session.items()))

    def _render_text(self, text, context=None, extra=None, encode=None):
        if context is None:
            context = self._get_session_items()
            context.update(self.ussd_request.all_variables())

        if extra:
            context.update(extra)

        template = Template(text or '', keep_trailing_newline=True)
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
                   else text_context['default']

            text_context = text_context[language]

        return self._render_text(
            text_context
        )

    def evaluate_jija_expression(self, expression):
        if not expression.endswith("}}") and \
                not expression.startswith("{{"):
            expression = "{{ " + expression + " }}"

        template = Template(expression)

        context = self._get_session_items()
        context.update(self.ussd_request.all_variables())
        results = template.render(
            ussd_request=self.ussd_request,
            **context
        )

        if results == 'False':
            return False
        return True

    @classmethod
    def validate(cls, screen_name: str, ussd_content: dict) -> (bool, dict):
        screen_content = ussd_content[screen_name]

        validation = cls.serializer(data=screen_content,
                                     context=ussd_content)

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


class UssdView(APIView):
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
            staticconf.YamlConfiguration(self.customer_journey_conf,
                                         namespace=
                                         self.customer_journey_namespace,
                                         flatten=False)

    def finalize_response(self, request, response, *args, **kwargs):

        if isinstance(response, UssdRequest):
            self.logger = get_logger(__name__).bind(**response.all_variables())
            ussd_response = self.ussd_dispatcher(response)
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
            ussd_request.session['steps'] = []
            ussd_request.session['posted'] = False
            ussd_request.session['submit_data'] = {}
            ussd_request.session['session_id'] = ussd_request.session_id
            ussd_request.session['phone_number'] = ussd_request.phone_number

        ussd_request.session.update(ussd_request.all_variables())

        self.logger.debug('gateway_request', text=ussd_request.input)

        # Invoke handlers
        ussd_response = self.run_handlers(ussd_request)
        # Save session
        ussd_request.session.save()
        self.logger.debug('gateway_response', text=ussd_response.dumps(),
                     input="{redacted}")

        return ussd_response

    def run_handlers(self, ussd_request):
        handler = ussd_request.session['_ussd_state']['next_screen'] \
                  if ussd_request.session['_ussd_state']['next_screen'] \
                  else staticconf.read(
            'initial_screen', namespace=self.customer_journey_namespace)

        ussd_response = (ussd_request, handler)

        # Handle any forwarded Requests; loop until a Response is
        # eventually returned.
        while not isinstance(ussd_response, UssdResponse):
            ussd_request, handler = ussd_response

            screen_content = staticconf.read(
                handler,
                namespace=self.customer_journey_namespace)

            ussd_response = _registered_ussd_handlers[screen_content['type']](
                ussd_request,
                handler,
                screen_content,
                logger=self.logger
            ).handle()

        ussd_request.session['_ussd_state']['next_screen'] = handler


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
            if screen_name == "initial_screen":
                # confirm the next screen is in the screen content
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