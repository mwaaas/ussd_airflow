from ussd.tests import UssdTestCase


class TestFunctionScreen(UssdTestCase.BaseUssdTestCase):
    validation_error_message = dict(
        get_name=dict(
            function=["Function ussd.tests.utils.show_name does not exist"]
        ),
        get_height=dict(
            function=["Module ussd.tests.util does not exist"]
        ),
        get_weight=dict(
            function=["Module name where function is located not given"]
        ),
        get_age=dict(
            next_screen=['This field is required.'],
            session_key=['This field is required.'],
            function=['This field is required.'],
        )
    )

    def test(self):
        phone_number = '0711111111'
        expected_text = "Your name is mwas " \
                        "and phone number is {0}"
        self.assertEqual(expected_text.format(phone_number),
                         self.ussd_client(
                             phone_number=phone_number).send('')
                         )

        # test with a different number
        phone_number = '072222222'
        self.assertEqual(
            expected_text.format(phone_number),
            self.ussd_client(
                phone_number=phone_number).send('')
        )
