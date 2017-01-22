from ussd.tests import UssdTestCase


class TestInputHandler(UssdTestCase.BaseUssdTestCase):

    validation_error_message = dict(
            enter_height={
                "validators": {
                    'text': ['This field is required.']
                },
                "next_screen": ['This field is required.']
            },
            enter_age={
                "input_identifier": ['This field is required.'],
                "next_screen": ['thank_you_screen is missing in ussd journey'],
            },
            show_information={
                "type": ['Invalid screen type not supported']
            },
            hidden_fields={
                "initial_screen": ["This field is required."]
            }
        )

    def test_showing_screen_content(self):
        ussd_client = self.ussd_client()

        # dial in
        response = ussd_client.send('')

        self.assertEqual(
            "Enter your height\n",
            response
        )

        # enter height
        response = ussd_client.send('6')

        self.assertEqual(
            "Enter your age\n",
            response
        )

        # enter age

        response = ussd_client.send('24')

        self.assertEqual(
            "Your age is 24 and your height is 6.\n"
            "Enter anything to go back to the first screen\n",
            response
        )

    def test_multilanguage_support(self):

        ussd_client = self.ussd_client(language='sw')


        # Dial in
        response = ussd_client.send('1')

        self.assertEqual(
            "Weka ukubwa lako\n",
            response
        )

        response = ussd_client.send('7')

        self.assertEqual(
            "Weka miaka yako\n",
            response
        )

        response = ussd_client.send('23')

        self.assertEqual(
            "Miaka yako in 23 na ukubwa wako in 7.\n"
            "Weka kitu ingine yoyote unende "
            "kwenye screen ya kwanza\n",
            response
        )

    def test_input_validation(self):

        ussd_client = self.ussd_client()

        # dial in
        ussd_client.send('')

        # enter invalid height
        response = ussd_client.send('mwas')

        # should get a invalid error message
        self.assertEqual(
            "Enter number between 1 and 7\n",
            response
        )

        # enter valid height
        response = ussd_client.send('6')

        self.assertEqual(
            "Enter your age\n",
            response
        )

        # enter invalid age greater thatn 100
        response = ussd_client.send('150')

        self.assertEqual(
            "Number over 100 is not allowed\n",
            response
        )

        # enter a valid age
        response = ussd_client.send('23')

        self.assertEqual(
            "Your age is 23 and your height is 6.\n"
            "Enter anything to go back to the first screen\n",
            response
        )
