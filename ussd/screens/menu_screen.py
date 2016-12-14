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
    MenuOptionSerializer, NextUssdScreenSerializer, UssdTextSerializer
from rest_framework.serializers import ListField, ValidationError, \
    CharField


class WithItemField(CharField):
    def to_internal_value(self, data):
        if isinstance(data, list):
            return data
        return super(WithItemField, self).to_internal_value(data)


class WithDictField(CharField):
    def to_internal_value(self, data):
        if isinstance(data, dict):
            return data
        return super(WithDictField, self).to_internal_value(data)


class ItemsSerializer(UssdTextSerializer, NextUssdScreenSerializer):
    value = CharField()
    session_key = CharField()
    with_items = WithItemField(required=False, default=None)
    with_dict = WithDictField(required=False, default=None)

    def to_internal_value(self, data):
        # set data in instance to access later
        self.custom_data = data
        return super(ItemsSerializer, self).to_internal_value(data)

    def validate_with_items(self, value, loop_value='with_dict'):
        if value is None and self.custom_data.get(loop_value, None) is None:
            raise ValidationError(
                "with_items or with_dict field is required"
            )
        return value

    def validate_with_dict(self, value):
        return self.validate_with_items(value, 'with_items')


class MenuScreenSerializer(UssdContentBaseSerializer):
    options = ListField(
        child=MenuOptionSerializer(),
        required=False
    )
    items = ItemsSerializer(required=False)

    def validate(self, data):
        if 'options' not in data and 'items' not in data:
            raise ValidationError(
                'options field is required or items is required'
            )
        return super(MenuScreenSerializer, self).validate(data)


class ListItem(object):
    def __init__(self, text, value):
        self.text = text
        self.value = value


class MenuOption(object):
    def __init__(self, text, next_screen, index_display=None,
                 index_value=None):
        self.text = text
        self.next_screen = next_screen
        self.index_display = index_display or index_value
        self.index_value = index_value or self.index_display


class MenuScreen(UssdHandlerAbstract):
    screen_type = "menu_screen"
    serializer = MenuScreenSerializer

    def __init__(self, ussd_request, handler, screen_content, **kwargs):
        super(MenuScreen, self).__init__(ussd_request, handler, screen_content, **kwargs)
        self.list_options = [] if self.screen_content.get('items') is None \
            else self.get_items()
        self.menu_options = [] if self.screen_content.get('options') is None \
            else self.get_menu_options()
        self.error_message = "Please enter a valid choice.\n" \
            if not self.screen_content.get('error_message') \
            else self.get_text(self.screen_content["error_message"])

    def handle(self):
        # get items
        if not self.ussd_request.input:

            ussd_text = self._add_end_line(self.get_text()) + \
                        self.display_options(self.list_options) + \
                        self.display_options(
                            self.menu_options,
                            start_index=len(self.list_options) + 1
                        )

            return UssdResponse(ussd_text)

        else:
            next_screen = self.evaluate_input()
            if next_screen:
                return self.ussd_request.forward(next_screen)
            return UssdResponse(self.error_message)

    def evaluate_input(self):
        """
        This gets the selected option,
        and returns next_screen, and error message if any
        :return:
        """
        if self.ussd_request.input.isdigit() and \
                not int(self.ussd_request.input) <= 0:
            ussd_input = int(self.ussd_request.input)
            ussd_input_index = ussd_input - 1
            if ussd_input <= len(self.list_options):
                # save input in the session
                selected_item = self.list_options[ussd_input_index]
                self.ussd_request.session[
                    self.screen_content['items']['session_key']] = \
                    selected_item.value
                # forward request to the next screen
                return self.screen_content['items']['next_screen']
            elif ussd_input <= len(self.menu_options):
                return self.menu_options[ussd_input_index].next_screen
        else:
            for option in self.menu_options:
                if option.index_value == self.ussd_request.input:
                    return option.next_screen
        return False

    def get_value_from_variables(self, variable, all_variables: dict):
        if self._contains_vars(variable):
            # Check to see if the string we are trying to
            # render is just referencing a single
            # var.  In this case we don't want to accidentally
            # change the type of the variable
            # to a string by using the jinja template renderer.
            # We just want to pass it.
            only_one = self.SINGLE_VAR.match(variable)
            if only_one:
                return all_variables.get(
                    only_one.group(1)
                )
            # we don't support other jinja syntax a the moment
            return []
        return variable

    def get_items(self) -> list:
        """
        This gets ListItems
        :return:
        """
        items_section = self.screen_content['items']

        text = self.screen_content['items']['text']
        value = self.screen_content['items']['value']

        loop_method = ""
        loop_value = ""
        for key, value_ in items_section.items():
            if key.startswith("with_"):
                loop_method = "_" + key
                loop_value = value_

        items = self.get_value_from_variables(loop_value,
                                              self._get_session_items())

        return getattr(self, loop_method)(
            text, value, items
        )

    def get_menu_options(self) -> list:
        menu_options = []
        for option in self.screen_content.get('options', []):
            menu_options.append(
                MenuOption(
                    self.get_text(text_context=option['text']),
                    option['next_screen'],
                    option.get('input_display'),
                    option.get('input_value')
                )
            )
        return menu_options

    @staticmethod
    def _add_end_line(text):
        if text and '\n' not in text:
            text += '\n'
        return text

    def display_options(self, list_items: list, start_index: int = 1) -> str:
        text = ""
        customized_option = ""
        for index, item in enumerate(list_items, start_index):
            index = "{index}. ".format(index=index) \
                if getattr(item, 'index_display', None) is None \
                else item.index_display

            option_text = "{index}{text}".format(
                index=index,
                text=self._add_end_line(
                    self.get_text(text_context=item.text)
                )
            )

            # options that have a customized way presenting menu
            # should appear last after the once that are numbered
            text = text + option_text \
                if getattr(item, 'index_display', None) is None \
                else text

            customized_option = customized_option + option_text \
                if getattr(item, 'index_display', None) is not None \
                else customized_option

        return text + customized_option

    def _with_items(self, text, value, items):
        list_items = []
        for item in items:
            context = {}
            extra = {
                "item": item
            }
            if isinstance(items, dict):
                extra.update(
                    dict(
                        key=item,
                        value=items[item],
                        item={item: items[item]}
                    )
                )

            context.update(extra)

            list_items.append(
                ListItem(
                    self._render_text(
                        text,
                        extra=context
                    ),
                    self.get_value_from_variables(value, context)
                )
            )
        return list_items

    def _with_dict(self, text, value, items):
        return self._with_items(text, value, items)
