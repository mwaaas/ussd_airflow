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
                  "4. vegetables\n"

    types_of_food = "Choose your favourite food\n" \
                    "1. rice\n" \
                    "2. back\n"

    types_of_fruit = "No fruits available choose * to go back\n" \
                     "*back\n"

    rice_chosen = "Your rice will be delivered shortly. " \
                  "Choose 1 to go back\n1. back\n"

    type_of_drinks = "No drinks available choose 0 to go back\n" \
                     "0 back\n"

    error_message = "Please enter a valid choice.\n"

    types_of_vegetables = "Choose one of the following vegetables\n" \
                          "1. Vege Sukuma\n" \
                          "2. Vege Carrot\n" \
                          "3. Vege Cabbage\n"

    choose_quantity = "Choose vegetable quantity\n" \
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

    def test_invalid_input(self):
        ussd_client = self.ussd_client()

        # dial in
        ussd_client.send('')

        # select invalid option
        self.assertEqual(ussd_client.send('9'),
                         "You have selected invalid option try again\n"
                         )

        # select the correct option 2 for drinks
        self.assertEqual(ussd_client.send('3'), self.type_of_drinks)

        # select invalid back option
        self.assertEqual(ussd_client.send('*'), self.error_message)

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
            self.error_message,
            ussd_client.send('9')
        )

        # choose the cabbage
        ussd_client.send('3')
