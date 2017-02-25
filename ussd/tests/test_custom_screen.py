from ussd.core import UssdHandlerAbstract
from ussd.screens.serializers import UssdBaseSerializer, \
    NextUssdScreenSerializer
from rest_framework import serializers
from ussd.tests import UssdTestCase
from ussd.core import UssdResponse


class InvalidCustomHandler(object):
    pass


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


class TestCustomHandler(UssdTestCase.BaseUssdTestCase):
    validation_error_message = dict(
        custom_screen_0=dict(
            screen_obj=['This field is required.']
        ),
        custom_screen_1=dict(
            screen_obj=["Screen object should be of type UssdHandlerAbstract"]
        ),
        custom_screen_2=dict(
            screen_obj=['Class does not exist']
        ),
        custom_screen_3=dict(
            next_screen=['This field is required.'],
            input_identifier=['This field is required.']
        )
    )

    def test(self):
        ussd_client = self.ussd_client()

        self.assertEqual(
            "This is a custom Handler1",
            ussd_client.send('')  # dial in
        )

        self.assertEqual(
            "Enter a digit and it will be doubled on your behalf",
            ussd_client.send('1')  # goes to the next screen
        )

        self.assertEqual(
            "Your custom screen has modified your input to 18",
            ussd_client.send('9')  # enter number to double
        )