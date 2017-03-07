"""
This module is involved in testing Menu screen only
"""
from ussd.tests import UssdTestCase
from ussd.core import ussd_session
from collections import OrderedDict


class TestMenuHandler(UssdTestCase.BaseUssdTestCase):
    choose_meal = "Choose your favourite meal\n" \
                  "1. food\n" \
                  "2. fruits\n" \
                  "3. drinks\n" \
                  "4. vegetables\n" \
                  "5. test pagination\n"

    types_of_food = "Choose your favourite food\n" \
                    "1. rice\n" \
                    "2. back\n"

    types_of_fruit = "No fruits available choose * to go back\n" \
                     "*. back\n"

    rice_chosen = "Your rice will be delivered shortly. " \
                  "Choose 1 to go back\n1. back\n"

    type_of_drinks = "No drinks available choose 0 to go back\n" \
                     "0 back\n"

    error_message = "Please enter a valid choice.\n"

    types_of_vegetables = "Choose one of the following vegetables\n" \
                          "1. Vege Sukuma\n" \
                          "2. Vege Carrot\n" \
                          "3. Vege Cabbage\n"

    choose_quantity = "Choose vegetable size\n" \
                      "1. small at Ksh 50\n" \
                      "2. medium at Ksh 100\n" \
                      "3. large at Ksh 150\n" \
                      "4. back\n"

    selected_vegetables = "You have selected this {vegetable} and " \
                          "this quantity {quantity} at {price}\n" \
                          "1. test_list\n"

    validation_error_message = dict(
        choose_meal=dict(
            non_field_errors=[
                'options field is required or items is required'
            ]
        ),
        types_of_food=dict(
            text=['This field is required.']
        ),
        types_of_fruit=dict(
            options=dict(
                next_screen=["invalid_screen is missing in ussd journey"]
            )
        ),
        types_of_drinks=dict(
            options=dict(
                next_screen=['This field is required.']
            )
        ),
        rice_chosen=dict(
            options=dict(
                next_screen=['This field is required.']
            )
        ),
        types_of_vegetables=dict(
            items=dict(
                value=['This field is required.'],
                session_key=['This field is required.'],
                next_screen=['This field is required.'],
                with_items=['with_items or with_dict field is required'],
                with_dict=['with_items or with_dict field is required']
            )
        )
    )

    @staticmethod
    def add_vegetable_list_in_session(ussd_client):
        session = ussd_session(ussd_client.session_id)
        session["vegetables_list"] = [
            "Sukuma",
            "Carrot",
            "Cabbage"
        ]
        session['vegetable_quantity'] = OrderedDict()
        session['vegetable_quantity']['small'] = 50
        session['vegetable_quantity']['medium'] = 100
        session['vegetable_quantity']['large'] = 150

        session.save()

    def test_happy_case(self):
        ussd_client = self.ussd_client()

        # dial in
        response = ussd_client.send('')

        self.assertEqual(self.choose_meal, response)

        # choose food
        response = ussd_client.send('1')
        self.assertEqual(self.types_of_food, response)

        # choose rice
        response = ussd_client.send('1')
        self.assertEqual(self.rice_chosen, response)

        # choose one to go back
        self.assertEqual(self.choose_meal, ussd_client.send('1'))

        # choose fruits
        self.assertEqual(self.types_of_fruit, ussd_client.send('2'))

        # choose * to go back
        self.assertEqual(self.choose_meal, ussd_client.send('*'))

        # choose 3 for drinks
        self.assertEqual(self.type_of_drinks, ussd_client.send('3'))

        # choose 0 to go back
        self.assertEqual(self.choose_meal, ussd_client.send('0'))

    # todo test invalid option with screen that have multiple pages
    def test_invalid_input(self):
        ussd_client = self.ussd_client()

        # dial in
        ussd_client.send('')

        # select invalid option
        self.assertEqual(ussd_client.send('9'),
                         "You have selected invalid option try again\n" +
                         self.choose_meal
                         )

        # select the correct option 2 for drinks
        self.assertEqual(ussd_client.send('3'), self.type_of_drinks)

        # select invalid back option
        self.assertEqual(ussd_client.send('*'),
                         self.error_message + self.type_of_drinks)

        # select the correct back option
        self.assertEqual(ussd_client.send('0'), self.choose_meal)

    def test_list_screen(self):
        ussd_client = self.ussd_client()
        self.add_vegetable_list_in_session(ussd_client)

        # dial in
        ussd_client.send('')

        # choose vegetables
        self.assertEqual(
            self.types_of_vegetables,
            ussd_client.send('4')
        )

        # choose sukuma
        self.assertEqual(
            self.choose_quantity,
            ussd_client.send('1')
        )

        # choose medium
        self.assertEqual(
            self.selected_vegetables.format(
                vegetable="Sukuma",
                quantity="medium",
                price=100
            ),
            ussd_client.send('2')
        )

        # choose 1 to test native list
        self.assertEqual(
            "1. a\n"
            "2. b\n"
            "3. c\n"
            "4. d\n",
            ussd_client.send('1')
        )

        # choose one ot test native dict items
        response = ussd_client.send('1')
        for i in (
            "a for apple\n",
            "b for boy\n",
            "c for cat\n"
        ):
            self.assertRegex(response, i)

        self.assertEqual(
            "Choose one of the following vegetables\n",
            ussd_client.send('1')
        )

    def test_invalid_input_in_list_screen(self):
        ussd_client = self.ussd_client()

        # dial in
        ussd_client.send('')
        self.add_vegetable_list_in_session(ussd_client)
        # choose vegetables
        ussd_client.send('4')

        # choose invalid option for vegetables
        self.assertEqual(
            self.error_message + self.types_of_vegetables,
            ussd_client.send('9')
        )

        # choose the cabbage
        ussd_client.send('3')

    def test_text_pagination(self):
        ussd_client = self.ussd_client()

        # dial in
        ussd_client.send('')

        # select testing pagination
        response = ussd_client.send('5')

        page_one = "Ussd airflow should be able to wrap anytext " \
                   "that is larger than the one\n98. More\n"

        self.assertEqual(
            response,
            page_one
        )

        # select more
        response = ussd_client.send('98')

        self.assertEqual(
            "specified into two screens.\n1. next\n00. Back\n",
            response
        )

        # test back option
        self.assertEqual(
            page_one,
            ussd_client.send('00')
        )

        self.assertEqual(
            "An example of screen with "
            "multiple options that need to be paginated\n98. More\n",
            ussd_client.send('1')  # select next screen without viewing that option
        )

        # select more to see the next option
        self.assertEqual(
            "1. screen_with_both_text_and_menu_options_pagination\n"
            "00. Back\n"
            "98. More\n",
            ussd_client.send('98')
        )

        # select more to view the next screen
        self.assertEqual(
            "2. screen_with_both_text_item_options_pagination\n00. Back\n",
            ussd_client.send('98')
        )

        # select option 1 to test pagination in both text and options
        self.assertEqual(
            "This screen has both large text and options that exceed the "
            "limit required so\n"
            "98. More\n",
            ussd_client.send('1')
        )

        # select 98 to view more
        self.assertEqual(
            "both the prompt and options will be paginated.\n"
            "1. go back to the previous screen\n"
            "00. Back\n"
            "98. More\n",
            ussd_client.send('98')
        )

        # select 98 to view more
        self.assertEqual(
            "2. quit this session\n"
            "3. this options will be showed in the next_screen\n"
            "00. Back\n",
            ussd_client.send('98')
        )

        # select 3 to test pagination with options and items
        self.assertEqual(
            "This screen has both large text, options, "
            "items that exceed ussd text limit part\n"
            "98. More\n",
            ussd_client.send('3')
        )

        # Todo fix this tests
        # # select 98 to view more
        # self.assertEqual(
        #     "of this text would be displayed in the next screen\n"
        #     "1. apple\n"
        #     "2. boy\n"
        #     "00. Back\n"
        #     "98. More\n",
        #     ussd_client.send('98')
        # )
        #
        # # select 98 to view more
        # self.assertEqual(
        #     "3. cat\n"
        #     "4. dog\n"
        #     "5. egg\n"
        #     "6. frog\n"
        #     "7. girl\n"
        #     "8. house\n"
        #     "9. ice\n"
        #     "10. joyce\n"
        #     "00. Back\n"
        #     "98. More\n",
        #     ussd_client.send('98')
        # )
        #
        # # select 98 to view more
        # self.assertEqual(
        #     "11. kettle\n"
        #     "12. lamp\n"
        #     "13. mum\n"
        #     "14. nurse\n"
        #     "15. ostrich\n"
        #     "16. pigeon\n"
        #     "17. queen\n"
        #     "00. Back\n"
        #     "98. More\n",
        #     ussd_client.send('98')
        # )
        #
        # # select 98 to view more
        # self.assertEqual(
        #     "18. river\n"
        #     "19. sweet\n"
        #     "20. tiger\n"
        #     "21. umbrella\n"
        #     "22. van\n"
        #     "23. water\n"
        #     "24. quit_session\n"
        #     "00. Back\n",
        #     ussd_client.send('98')
        # )
        #
        # # choose apple
        # self.assertEqual(
        #     "end of session apple",
        #     ussd_client.send('1')
        # )