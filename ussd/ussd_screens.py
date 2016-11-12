"""
In ussd airflow ussd customer journey is created and defined by
yaml

Each section in yaml is a ussd screen. Each section must have an
key of value pair of screen_type: screen_type

The screen type defines the logic and how the screen is going to be
rendered.

The following are the  supported screen types:

"""


class InputScreen(object):
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


