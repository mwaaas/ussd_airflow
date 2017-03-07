from ussd.core import UssdHandlerAbstract, UssdHandlerMetaClass
from ussd.screens.serializers import UssdBaseSerializer
from rest_framework import serializers
from ussd.utilities import str_to_class


class CustomScreenSerializer(UssdBaseSerializer):
    screen_obj = serializers.CharField(max_length=255)

    @staticmethod
    def validate_screen_obj(value):
        try:
            screen_obj = str_to_class(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        else:
            if not isinstance(screen_obj, UssdHandlerMetaClass):
                raise serializers.ValidationError(
                    "Screen object should be of type UssdHandlerAbstract"
                )
            return screen_obj

    def validate(self, data):
        data = super(CustomScreenSerializer, self).validate(data)
        screen_obj = data['screen_obj']
        if hasattr(screen_obj, 'serializer'):
            validation = screen_obj.serializer(data=self.initial_data,
                                               context=self.context)
            if not validation.is_valid():
                raise serializers.ValidationError(validation.errors)
        return data


class CustomScreen(UssdHandlerAbstract):
    """
    If you have a particular user case that's not yet covered by
    our existing screens, this is the screen to use.

    This screen allows us to define our own ussd screen.

    To create it you need the following fields.
        1. screen_object
            This is the path to be used to import the class
        2. serializer (optional)
            This if you want to be validating your screen with
            specific fields
        3. You can define any field that you feel
            your custom screen might need.
    EXAMPLE:
        examples of custom screen 
            .. code-block:: python
            
                class SampleCustomHandler1(UssdHandlerAbstract):
                    abstract = True  # don't register custom classes
                    @staticmethod
                    def show_ussd_content():  # This method doesn't have to be static
                        # Do anything custom here.
                        return UssdResponse("This is a custom Handler1")
                
                    def handle_ussd_input(self, ussd_input):
                        # Do anything custom here
                        print(ussd_input)  # pep 8 for the sake of using it.
                        return self.ussd_request.forward('custom_screen_2')
    
    
                class SampleSerializer(UssdBaseSerializer, NextUssdScreenSerializer):
                        input_identifier = serializers.CharField(max_length=100)
                
                
                class SampleCustomHandlerWithSerializer(UssdHandlerAbstract):
                    abstract = True  # don't register custom classes
                    serializer = SampleSerializer
                
                    @staticmethod
                    def show_ussd_content():  # This method doesn't have to be static
                        return "Enter a digit and it will be doubled on your behalf"
                
                    def handle_ussd_input(self, ussd_input):
                        self.ussd_request.session[
                            self.screen_content['input_identifier']
                        ] = int(ussd_input) * 2
                
                        return self.ussd_request.forward(
                            self.screen_content['next_screen']
                        )
        
        example of defining a yaml
            
            .. literalinclude:: .././ussd/tests/sample_screen_definition/valid_menu_screen_conf.yml
    """
    screen_type = "custom_screen"
    serializer = CustomScreenSerializer

    def handle(self):
        # Todo initiate the class in the core. to avoid double changing
        # if the parameter changes.

        # calling the custom screen handler method
        return str_to_class(
            self.screen_content['screen_obj']
        )(
            self.ussd_request,
            self.handler,
            self.screen_content,
            initial_screen={},
            template_namespace=self.ussd_request.session.get(
                'template_namespace', None
            )
        ).handle()
