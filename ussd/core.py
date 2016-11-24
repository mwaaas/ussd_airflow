"""

"""
from urllib.parse import unquote
from copy import copy, deepcopy
from rest_framework.views import APIView
import inspect
from copy import deepcopy
from django.http import HttpResponse
from structlog import get_logger
import staticconf
from django.conf import settings
from importlib import import_module
from django.contrib.sessions.backends import signed_cookies
from django.contrib.sessions.backends.base import CreateError
from jinja2 import Template


_registered_ussd_handlers = {}

class MissingAttribute(Exception):
    pass


class InvalidAttribute(Exception):
    pass


class DuplicateSessionId(Exception):
    pass


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
        self.session = self.create_ussd_session()

        for key, value in kwargs.items():
            setattr(self, key, value)

    def create_ussd_session(self):
        # Make a session storage
        session_engine = import_module(getattr(settings, "USSD_SESSION_ENGINE", settings.SESSION_ENGINE))
        if session_engine is signed_cookies:
            raise ValueError("You cannot use channels session functionality with signed cookie sessions!")
        # Force the instance to load in case it resets the session when it does
        session = session_engine.SessionStore(session_key=self.session_id)
        session._session.keys()
        session._session_key = self.session_id

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
            required_attributes = ('screen_type', 'validate_schema', 'handle')

            # check all attributes have been defined
            for attribute in required_attributes:
                if attribute not in attr and not hasattr(cls, attribute):
                    raise MissingAttribute(
                        "{0} is required in class {1}".format(
                            attribute, name)
                    )

            # # both validate_schema function
            # if not isinstance(attr['validate_schema'], staticmethod):
            #     raise InvalidAttribute('validate_schema should be '
            #                            'a static method')
            #
            # # handle is a class method
            # inspect.isfunction()
            # if not inspect.ismethod(attr['handle']):
            #     raise InvalidAttribute("handle should be a class method")

            _registered_ussd_handlers[attr['screen_type']] = cls


class UssdHandlerAbstract(object, metaclass=UssdHandlerMetaClass):
    abstract = True

    def __init__(self, ussd_request, handler, screen_content):
        self.ussd_request = ussd_request
        self.handler = handler
        self.screen_content = screen_content

    def _get_session_items(self):
        return dict(iter(self.ussd_request.session.items()))

    def _render_text(self, text):
        template = Template(text, keep_trailing_newline=True)
        return template.render(self._get_session_items())

    def get_text(self, text_context=None):
        text_context = self.screen_content.get('text')\
                       if text_context is None \
                       else text_context

        language = self.ussd_request.language \
                   if self.ussd_request.language \
                          in text_context.keys() \
                   else text_context['default']
        return self._render_text(
            text_context[language]
        )

    def evaluate_jija_expression(self, expression):
        if not expression.endswith("}}") and \
                not expression.startswith("{{"):
            expression = "{{ " + expression + " }}"

        template = Template(expression)

        results = template.render(
            ussd_request=self.ussd_request,
            **self._get_session_items()
        )

        if results == 'False':
            return False
        return True





def validate_ussd_journey(ussd_content):
    pass


class UssdView(APIView):
    ussd_customer_journey_file = None
    ussd_customer_journey_namespace = None

    def finalize_response(self, request, response, *args, **kwargs):

        if isinstance(response, UssdRequest):
            response = self.finalize_ussd_response(response)
        return super(UssdView, self).finalize_response(request, response, args, kwargs)

    def finalize_ussd_response(self, ussd_request):

        if self.ussd_customer_journey_file is None or self.ussd_customer_journey_namespace is None:
            raise MissingAttribute("attribute ussd_customer_journey_file and "
                                   "ussd_customer_journey_namespace are required")

        if not self.ussd_customer_journey_namespace in staticconf.config.configuration_namespaces:
            staticconf.YamlConfiguration(self.ussd_customer_journey_file,
                                         namespace=self.ussd_customer_journey_namespace,
                                         flatten=False)
        ussd_response = self.ussd_dispatcher(ussd_request)
        return self.ussd_response_handler(ussd_response)

    def ussd_response_handler(self, ussd_response):
        return HttpResponse(str(ussd_response))

    def ussd_dispatcher(self, ussd_request):

        logger = get_logger(__name__).bind(**ussd_request.all_variables())

        # Clear input and initialize session if we are starting up
        if '_ussd_state' not in ussd_request.session:
            ussd_request.input = ''
            ussd_request.session['_ussd_state'] = {'next_handler': ''}
            ussd_request.session['steps'] = []
            ussd_request.session['posted'] = False
            ussd_request.session['submit_data'] = {}
            ussd_request.session['session_id'] = ussd_request.session_id
            ussd_request.session['phone_number'] = ussd_request.phone_number

        ussd_request.session.update(ussd_request.all_variables())

        logger.debug('gateway_request', text=ussd_request.input)

        # Invoke handlers
        ussd_response = self.run_handlers(ussd_request)
        # Save session
        ussd_request.session.save()
        logger.debug('gateway_response', text=ussd_response.dumps(), input="{redacted}")

        return ussd_response

    def run_handlers(self, ussd_request):
        handler = ussd_request.session['_ussd_state']['next_handler'] \
                  if ussd_request.session['_ussd_state']['next_handler'] \
                  else staticconf.read('initial_screen', namespace=self.ussd_customer_journey_namespace)


        ussd_response = (ussd_request, handler)


        # Handle any forwarded Requests; loop until a Response is
        # eventually returned.
        while not isinstance(ussd_response, UssdResponse):
            ussd_request, handler = ussd_response

            screen_content = staticconf.read(
                handler,
                namespace=self.ussd_customer_journey_namespace)

            ussd_response = _registered_ussd_handlers[screen_content['type']](
                ussd_request,
                handler,
                screen_content
            ).handle()

        ussd_request.session['_ussd_state']['next_handler'] = handler


        # Attach session to outgoing response
        ussd_response.session = ussd_request.session

        return ussd_response

