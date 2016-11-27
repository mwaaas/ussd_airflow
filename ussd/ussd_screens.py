"""
In ussd airflow ussd customer journey is created and defined by
yaml

Each section in yaml is a ussd screen. Each section must have an
key of value pair of screen_type: screen_type

The screen type defines the logic and how the screen is going to be
rendered.

The following are the  supported screen types:

"""

from ussd.core import UssdHandlerAbstract, UssdResponse, UssdBaseSerializer
import datetime
from django.core.validators import RegexValidator
from django.utils.encoding import force_text
import re
from rest_framework import serializers


def ussd_regex_validator(regex_expression, user_input):
    regex = re.compile(regex_expression)
    if not bool(regex.search(force_text(user_input))):
        return False
    return True

class UssdTextSerializer(serializers.Serializer):

    text = serializers.DictField(child=serializers.CharField(max_length=250))

    def validate_text(self, value):
        if not value['default'] in value.keys():
            raise serializers.ValidationError(
                "Text for language {} is missing".format(value['default'])
            )
        return value


class UssdContentBaseSerializer(UssdBaseSerializer, UssdTextSerializer):
    pass

class NextUssdScreenSerializer(serializers.Serializer):
    next_screen = serializers.CharField(max_length=50)

    def validate_next_screen(self, value):
        return value in self.context.keys()


class InputValidatorSerializer(UssdTextSerializer):
    regex = serializers.CharField(max_length=255, required=False)
    expression = serializers.CharField(max_length=255, required=False)

    def validate(self, data):
        return super(InputValidatorSerializer, self).validate(data)


class InputSerializer(UssdContentBaseSerializer, NextUssdScreenSerializer):
    input_identifier = serializers.CharField(max_length=100)
    validators = serializers.ListField(
        child=InputValidatorSerializer(),
        required=False
    )


class InputScreen(UssdHandlerAbstract):
    """

    **Input Screen**

    This screen prompts the user to enter an input

    Fields required:
        - text: this the text to display to the user.
        - input_identifier: input amount entered by users will be saved
                            with this key. To access this in the input
                            anywhere {{ input_identifier }}
        - next_handler: The next screen to go after the user enters
                        input
        - validators:
            - error_message: This is the message to display when the validation fails
              regex: regex used to validate ussd input. Its mutually exclusive with expression
            - expression: if regex is not enough you can use a jinja expression will be called ussd request object
              error_message: This the message thats going to be displayed if expression returns False

    Example:
        .. literalinclude:: ../../ussd/tests/sample_screen_definition/valid_input_screen_conf.yml
    """

    screen_type = "input_screen"

    @staticmethod
    def validate_schema(screen_name: str,
                        ussd_content: dict) -> (bool, dict):
        pass

    def validate_input(self, validate_rules):

        return True

    def handle(self):
        if not self.ussd_request.input:
            response_text = self.get_text()
            ussd_screen = dict(
                name=self.handler,
                start=datetime.datetime.now(),
                screen_text=response_text
            )
            self.ussd_request.session['steps'].append(ussd_screen)

            return UssdResponse(response_text)
        else:
            # validate input
            validation_rules = self.screen_content.get("validators")
            for validation_rule in validation_rules:
                is_valid = True

                if 'regex' in validation_rule:
                    regex_expression = validation_rule['regex']
                    regex = re.compile(regex_expression)
                    is_valid = bool(
                        regex.search(
                            force_text(self.ussd_request.input)
                        ))
                else:
                    is_valid = self.evaluate_jija_expression(
                        validation_rule['expression']
                    )

                # show error message if validation failed
                if not is_valid:
                    return UssdResponse(
                        self.get_text(
                            validation_rule['text']
                        )
                    )



            session_key = self.screen_content['input_identifier']
            next_handler = self.screen_content['next_screen']
            self.ussd_request.session[session_key] = \
                self.ussd_request.input

            self.ussd_request.session['steps'][-1].update(
                end=datetime.datetime.now(),
                selection=self.ussd_request.input
            )
            return self.ussd_request.forward(next_handler)

    @staticmethod
    def validate(screen_name: str, ussd_content: dict) -> (bool, dict):
        screen_content = ussd_content[screen_name]

        validation = InputSerializer(data=screen_content,
                                     context=ussd_content)

        if validation.is_valid():
            return True, {}
        return False, validation.errors
