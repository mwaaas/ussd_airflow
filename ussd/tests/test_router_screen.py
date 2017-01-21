from ussd.tests import UssdTestCase
from ussd.core import ussd_session


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

    @staticmethod
    def add_phone_number_status_in_session(ussd_client):
        session = ussd_session(ussd_client.session_id)

        session["phone_numbers"] = {
            "203": ["registered"],
            "204": ["not_registered"],
            "205": ["not_there"]
        }
        session.save()

    def test(self):
        ussd_client = self.ussd_client(phone_number=200)

        self.assertEqual("This number is 200", ussd_client.send(''))

        ussd_client = self.ussd_client(phone_number=202)

        self.assertEqual("This number is 202", ussd_client.send(''))

        ussd_client = self.ussd_client(phone_number=300)

        self.assertEqual("This is the default screen",
                         ussd_client.send(''))

    def test_route_options_with_list_loop(self):
        ussd_client = self.ussd_client(phone_number=204)
        # add phone_number in session
        self.add_phone_number_status_in_session(ussd_client)

        # dial in
        response = ussd_client.send('')

        self.assertEqual(
            "You are not registered user",
            response
        )

        ussd_client = self.ussd_client(phone_number=203)
        # add phone_number in session
        self.add_phone_number_status_in_session(ussd_client)

        # dial in
        response = ussd_client.send('')

        self.assertEqual(
            "You are registered user",
            response
        )

        ussd_client = self.ussd_client(phone_number=205)
        # add phone_number in session
        self.add_phone_number_status_in_session(ussd_client)

        # dial in
        response = ussd_client.send('')

        self.assertEqual(
            "This is the default screen",
            response
        )

    def test_router_option_with_dict_loop(self):

        ussd_client = self.ussd_client(phone_number=206)

        self.assertEqual(
            "This is the default screen",
            ussd_client.send('')
        )

        ussd_client = self.ussd_client(phone_number=207)

        self.assertEqual(
            "This screen has been routed here because the "
            "phone number is 207",
            ussd_client.send('')
        )
