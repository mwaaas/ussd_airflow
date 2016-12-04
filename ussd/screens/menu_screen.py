"""
**Menu Screen**

This is the screen used to display options to select:

Fields required:
    - text: text to display for the user to choose option
        .. automodule:: ussd.screens.serializers
            :members: UssdBaseSerializer
    - menu_options:
        This is a list of the options to display to the user
        should contain text to show to the user and screen to
        go next if the user selects that option.
"""
from ussd.core import UssdHandlerAbstract, UssdResponse
from .serializers import UssdContentBaseSerializer, \
    MenuSerializer


class MenuScreenSerializer(UssdContentBaseSerializer, MenuSerializer):
    pass


class MenuScreen(UssdHandlerAbstract):

    screen_type = "menu_screen"
    serializer = MenuScreenSerializer

    def handle(self):
        if not self.ussd_request.input:
            ussd_text = self.get_text()

            # if end line character has not been set, set one
            if '\n' not in ussd_text:
                ussd_text = ussd_text + '\n'

            # get options
            menu_options = self.screen_content.get('options', [])

            options_to_apper_last = ''
            for index, option in enumerate(menu_options, start=1):
                menu_text = self.get_text(text_context=option['text'])
                #if end line has not been set, set one
                if '\n' not in menu_text:
                    menu_text = menu_text + '\n'

                # options that have a customized way presenting menu
                # should appear last after the once that are numbered
                if 'input_value' in option or 'input_text' in option:
                    input_display = option.get('input_display')\
                                    if option.get('input_display')\
                                    else option.get('input_value')
                    options_to_apper_last += "{item_display}{text}".format(
                        item_display=input_display,
                        text=menu_text
                    )
                    continue
                ussd_text += "{index}. {text}".format(
                    index=index,
                    text=menu_text
                )

            ussd_text += options_to_apper_last

            return UssdResponse(ussd_text)

        else:
            # get the selected opton
            option = self.get_selected_option()
            if option:
                return self.ussd_request.forward(option["next_screen"])

            error_message = "Please enter a valid choice.\n"\
                            if not self.screen_content.get('error_message')\
                            else self.get_text(
                self.screen_content["error_message"])

            return UssdResponse(error_message)

    def get_selected_option(self):
        try:
            menu_options = self.screen_content.get('options', [])
            if self.ussd_request.input.isdigit() and \
                    not int(self.ussd_request.input) <= 0:
                return menu_options[int(self.ussd_request.input) - 1]
            else:
                for option in menu_options:
                    # input_value = option.get('input_value') \
                    #     if option.get('input_value') \
                    #     else option.get('input_value')
                    if option.get("input_value", "") == self.ussd_request.input:
                        return option
        except IndexError:
            pass

        return False


