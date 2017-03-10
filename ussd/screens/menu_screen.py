from ussd.core import UssdHandlerAbstract, UssdResponse
from .serializers import UssdContentBaseSerializer, \
    MenuOptionSerializer, NextUssdScreenSerializer, UssdTextSerializer
from rest_framework.serializers import ListField, ValidationError, \
    CharField
from django.core.paginator import Paginator
import textwrap

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
    """
    - text:
        .. autoclass:: UssdContentBaseSerializer

    - options:
        This is a list of options to display to the user
        each option is
            .. autoclass:: MenuOptionSerializer

    - items:
        Sometimes you what to display a list of items and not
        menu options. Item is used for this
            .. autoclass:: ItemsSerializer

    - error_message: This is an optional message to display if the
                     user enters invalid input

    - option and items are mutual exclusive.

    Examples of menu screen:

        .. literalinclude:: .././ussd/tests/sample_screen_definition/valid_menu_screen_conf.yml
    """
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
    """
    This is the screen used to display options to select:

        - text:
            This is the text to display to the user.

        - options:
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

        - items:
            Unlike options where each option has its own screen to redirect
            in items we have a list of items to display and regardless of
            the input user will be redirected to one screen.

                Example of items

                .. code-block:: yaml

                    menu_screen_with_item_example:
                        type: menu_screen
                        text: choose one item
                        items:
                            text: "{{key}} for {{value}}"
                            value: "{{item}}"
                            next_screen: display_option
                            session_key: testing
                            with_dict:
                                a: apple
                                b: boy
                                c: cat

            In the above example if will display the following text

            .. code-block:: text

                    Choose one item
                        1. apple
                        2. boy
                        3. cat

            If the user selects "2", that would be translated by the value
            key, it will result to "b", then "b" will be saved with session_key
            provided and the user will be directed to the next screen which
            is display_option.

            To reference the selected item, use {{your_session_key}}

        - error_message: (optional)
            This is message to display if the user enter the wrong value.

            defaults to "Please enter a valid choice."

        - option and items are mutual exclusive.

    Example:
        .. literalinclude:: .././ussd/tests/sample_screen_definition/valid_menu_screen_conf.yml
    """
    screen_type = "menu_screen"
    serializer = MenuScreenSerializer

    def __init__(self, *args, **kwargs):
        super(MenuScreen, self).__init__(*args, **kwargs)
        self.list_options = [] if self.screen_content.get('items') is None \
            else self.get_items()
        self.menu_options = [] if self.screen_content.get('options') is None \
            else self.get_menu_options()
        self.error_message = "Please enter a valid choice.\n" \
            if not self.screen_content.get('error_message') \
            else self.get_text(self.screen_content["error_message"])

        # all options
        self.options = self.list_options + \
                       ([] if self.screen_content.get('options') is None else
                        self.get_menu_options(
                            start_index=len(self.list_options) + 1))

        self.paginator = self.get_paginator()

    def show_ussd_content(self):
        self.ussd_request.session['_ussd_state']['page'] = 1
        return self._render_django_page(1)

    def _render_django_page(self, index):
        return self.paginator.page(index).object_list[0]

    def get_paginator(self):
        pages = []
        ussd_title = self._add_end_line(self.get_text())

        # get ussd text limit
        ussd_text_limit = self.get_text_limit()

        # paginate menu screen text
        while len(ussd_title) > ussd_text_limit:
            # Lets create pages
            text = ""
            if len(pages) > 0:
                text += "00. {back_option}".format(
                    back_option=self.pagination_back_option)
            text += "98. {more_option}".format(
                more_option=self.pagination_more_option
            )

            # update ussd_text_limit to the one that considers pages
            ussd_text_limit = ussd_text_limit - len(text) - 1

            ussd_text_subsets = textwrap.wrap(
                ussd_title, width=ussd_text_limit
            )

            pages.append(
                self._add_end_line(ussd_text_subsets[0]) + text
            )

            ussd_title = self._add_end_line(' '.join(ussd_text_subsets[1:]))

        self.paginate_options(ussd_title, pages, self.options[:])

        return Paginator(pages, 1)

    def paginate_options(self, ussd_text, pages, options):
        """
        Assumptions:
            - ussd_text is within the limit
        """
        # Todo use back off strategy to generate the pages
        text = ""
        if len(pages) > 0:
            text += "00. {back_option}".format(
                back_option=self.pagination_back_option)

        if not options:
            pages.append(
                ussd_text + text
            )
            return pages

        ussd_text_cadidate = ussd_text + options[0].text
        # detect if there might be more optoins
        text += "98. {more_option}".format(more_option=
                                           self.pagination_more_option) \
            if len(ussd_text_cadidate) > self.get_text_limit() - len(text) \
            else ''
        if len(ussd_text_cadidate) <= self.get_text_limit() - len(text):
            ussd_text = ussd_text + options[0].text
        else:
            pages.append(
                ussd_text + text
            )
            ussd_text = options[0].text
        return self.paginate_options(
                ussd_text,
                pages,
                options[1:]
            )

    def handle_ussd_input(self, ussd_input):
        # check if input is for previous or next page
        if self.ussd_request.input.strip() in ("98", "00"):
            page = self.paginator.page(
                self.ussd_request.session['_ussd_state']['page']
            )
            if self.ussd_request.input.strip() == "98" and page.has_next():
                new_page_number = page.next_page_number()
                self.ussd_request.session['_ussd_state']['page'] = \
                    new_page_number
                return UssdResponse(self._render_django_page(new_page_number))
            elif self.ussd_request.input.strip() == '00' and \
                    page.has_previous():
                new_page_number = page.previous_page_number()
                self.ussd_request.session['_ussd_state']['page'] = \
                    new_page_number
                return UssdResponse(self._render_django_page(new_page_number))
        next_screen = self.evaluate_input()
        if next_screen:
            return self.ussd_request.forward(next_screen)
        return self.handle_invalid_input()

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

    def get_items(self, start_index: int = 1) -> list:
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

        items = self.evaluate_jija_expression(loop_value)

        return getattr(self, loop_method)(
            text, value, items, start_index
        )

    def get_menu_options(self, start_index: int = 1) -> list:
        menu_options = []
        for i, option in enumerate(self.screen_content.get('options', []),
                                   start_index):
            input_value = option.get('input_value') or i
            input_display = option.get('input_display') or \
                            "{index}. ".format(index=input_value)
            text = "{display_option}{text}".format(
                display_option=input_display,
                text=self._add_end_line(
                    self.get_text(text_context=option['text'])
                )
            )
            menu_options.append(
                MenuOption(
                    text,
                    option['next_screen'],
                    input_display,
                    input_value
                )
            )
        return menu_options

    def handle_invalid_input(self):
        return UssdResponse(
            self._add_end_line(
                self.get_text(self.error_message)) +
            self._render_django_page(1)
        )

    def _with_items(self, text, value, items, start_index):
        list_items = []
        for index, item in enumerate(items, start_index):
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
                    self._add_end_line("{index}. {text}".format(
                        index=index,
                        text=self._render_text(
                            text,
                            extra=context
                        )
                    )
                    ),
                    self.evaluate_jija_expression(value, context)
                )
            )
        return list_items

    def _with_dict(self, text, value, items, start_index):
        return self._with_items(text, value, items, start_index)


