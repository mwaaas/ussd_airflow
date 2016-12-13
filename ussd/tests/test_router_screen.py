from ussd.tests import UssdTestCase


class TestRouterHandler(UssdTestCase.BaseUssdTestCase):
    validation_error_message = dict(
        invalid_router_1=dict(
            router_options=['This field is required.']
        ),
        invalid_router_2=dict(
            router_options=dict(
                next_screen=['This field is required.']
            )
        )
    )

    def test(self):
        ussd_client = self.ussd_client(phone_number=200)

        self.assertEqual("This number is 200", ussd_client.send(''))

        ussd_client = self.ussd_client(phone_number=202)

        self.assertEqual("This number is 202", ussd_client.send(''))

        ussd_client = self.ussd_client(phone_number=300)

        self.assertEqual("This is the default screen",
                         ussd_client.send(''))
