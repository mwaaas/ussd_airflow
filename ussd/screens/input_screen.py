from ussd.core import UssdHandlerAbstract, UssdResponse
from ussd.screens.serializers import UssdContentBaseSerializer, \
    UssdTextSerializer, NextUssdScreenSerializer, MenuOptionSerializer
from django.utils.encoding import force_text
import re
from rest_framework import serializers
from ussd.screens.menu_screen import MenuScreen
from ussd.graph import Link, Vertex
import typing


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
    options = serializers.ListField(
        child=MenuOptionSerializer(),
        required=False
    )


class InputScreen(MenuScreen):
    """

    This screen prompts the user to enter an input

    Fields required:
        - text: this the text to display to the user.
        - input_identifier: input amount entered by users will be saved
                            with this key. To access this in the input
                            anywhere {{ input_identifier }}
        - next_screen: The next screen to go after the user enters
                        input
        - validators:
            - text: This is the message to display when the validation fails
              regex: regex used to validate ussd input. Its mutually exclusive
              with expression
            - expression: if regex is not enough you can use a jinja expression
             will be called ussd request object
              text: This the message thats going to be displayed if expression
              returns False
        - options (This field is optional):
            This is a list of options to display to the user
            each option is a key value pair of option text to display
            and next_screen to redirect if option is selected.
            Example of option:

            .. code-block:: yaml

                   options:
                    - text: option one
                      next_screen: screen_one
                    - text: option two
                      next_screen: screen_two

    Example:
        .. literalinclude:: .././ussd/tests/sample_screen_definition/valid_input_screen_conf.yml
    """

    screen_type = "input_screen"
    serializer = InputSerializer

    def handle_invalid_input(self):
        # validate input
        validation_rules = self.screen_content.get("validators", {})
        for validation_rule in validation_rules:

            if 'regex' in validation_rule:
                regex_expression = validation_rule['regex']
                regex = re.compile(regex_expression)
                is_valid = bool(
                    regex.search(
                        force_text(self.ussd_request.input)
                    ))
            else:
                is_valid = self.evaluate_jija_expression(
                    validation_rule['expression'],
                    session=self.ussd_request.session
                )

            # show error message if validation failed
            if not is_valid:
                return UssdResponse(
                    self.get_text(
                        validation_rule['text']
                    )
                )

        self.ussd_request.session[
            self.screen_content['input_identifier']
        ] = self.ussd_request.input

        return self.route_options()

    def get_next_screens(self) -> typing.List[Link]:
        # generate validators links
        links = []
        screen_vertex = Vertex(self.handler)
        for index, validation_screen in enumerate(self.screen_content.get("validators", [])):
            validator_screen_name = self.handler + "_validator_" + str(index + 1)
            validation_vertex = Vertex(validator_screen_name,
                                       self.get_text(validation_screen['text']))
            if 'regex' in validation_screen:
                validation_command = 'regex: ' + validation_screen['regex']
            else:
                validation_command = 'expression: ' + validation_screen['expression']
            links.append(
                Link(screen_vertex,
                     validation_vertex,
                     "validation",
                     "arrow",
                     "dotted"
                     )
            )

            links.append(
                Link(
                    validation_vertex,
                    screen_vertex,
                    validation_command,
                    "arrow",
                    "dotted"
                )
            )

        if isinstance(self.screen_content.get("next_screen"), list):
            for i in self.screen_content.get("next_screen", []):
                links.append(
                    Link(screen_vertex,
                         Vertex(i['next_screen'], ""),
                         i['condition'])
            )
        elif self.screen_content.get('next_screen'):
            links.append(
                Link(
                    screen_vertex,
                    Vertex(self.screen_content['next_screen']),
                    self.screen_content['input_identifier']
                )
            )

        if self.screen_content.get('default_next_screen'):
            links.append(
                Link(
                    screen_vertex,
                    Vertex(self.screen_content['default_next_screen'], ""),
                    self.screen_content['input_identifier']
                )
            )
        return links + super(InputScreen, self).get_next_screens()
