from ussd.core import UssdHandlerAbstract
from ussd.screens.serializers import NextUssdScreenSerializer
from rest_framework import serializers
import importlib


class FunctionScreenSerializer(NextUssdScreenSerializer):
    """
    Fields used to create this screen:

    1. function
        This is the function that will be called at this screen.
    2. session_key
        Once your function has been called the output of your function
        will be saved in ussd session using session_key
    3. next_screen
        Once your function has been called this it goes to the
        screen specified in next_screen
    """
    session_key = serializers.CharField()
    function = serializers.CharField()

    @staticmethod
    def validate_function(value):
        split_path = value.split('.')
        if len(split_path) <= 1:
            raise serializers.ValidationError(
                "Module name where function is located not given"
            )
        function_name = split_path[-1]
        module_name = '.'.join(value.split('.')[:-1])
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            raise serializers.ValidationError(
                "Module {0} does not exist".format(module_name)
            )

        if not hasattr(module, function_name):
            raise serializers.ValidationError(
                "Function {0} does not exist".format(value)
            )


class FunctionScreen(UssdHandlerAbstract):
    """
    This screen is invisible to the user. Its used to if you want to call a function you
    have implemented.

    Its like a complement of http screen. In http screen you make a request to an
    external service to perform some logic.

    This screen on the contrary if the logic that you want to be executed is within
    your application you use this screen to execute it.

    Your function will be called with UssdRequest object.
    And it should return a dictionary that will be saved in ussd session

    Below is the UssdRequest that will be used.
        .. autoclass:: ussd.core.UssdRequest

    Screen specification
        .. autoclass:: ussd.screens.function_screen.FunctionScreenSerializer

    Examples of function screens:
        .. literalinclude:: .././ussd/tests/sample_screen_definition/valid_function_screen_conf.yml
    """
    screen_type = "function_screen"
    serializer = FunctionScreenSerializer

    def handle(self):
        split_path = self.screen_content['function'].split('.')
        function_name = split_path[-1]
        module_name = '.'.join(split_path[:-1])
        module = importlib.import_module(module_name)

        self.ussd_request.session[
            self.screen_content['session_key']
        ] = getattr(module, function_name)(self.ussd_request)

        return self.ussd_request.forward(
            self.screen_content['next_screen']
        )
