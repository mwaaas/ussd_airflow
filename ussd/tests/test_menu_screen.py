"""
This module is involved in testing Menu screen only
"""
from ussd.tests import UssdTestClient, UssdTestCase


class TestMenuHandler(UssdTestCase.BaseUssdTestCase):
    choose_meal = "Choose your favourite meal\n" \
                  "1. food\n" \
                  "2. fruits\n" \
                  "3. drinks\n"

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

    validation_error_message = dict(
        choose_meal=dict(
            options=['This field is required.']
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
        )
    )

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
