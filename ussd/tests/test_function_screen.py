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
        client = self.ussd_client(phone_number='200')
        client.send('')  # dial in
        client.send('10')  # enter 10
        resp = client.send('1')

        expected_text = "The results was an {0} number " \
                        "which is {1}"

        self.assertEqual(
            expected_text.format('odd', 11),
            resp
        )

        client = self.ussd_client(phone_number='200')
        client.send('')  # dial in
        client.send('10')  # enter 10
        resp = client.send('2')

        expected_text = "The results was an {0} number " \
                        "which is {1}"

        self.assertEqual(
            expected_text.format('even', 12),
            resp
        )
