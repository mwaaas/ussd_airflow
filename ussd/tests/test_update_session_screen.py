from ussd.tests import UssdTestCase
from ussd.core import ussd_session


class TestUpdateSessionScreen(UssdTestCase.BaseUssdTestCase):
    validation_error_message = dict(
        screen_one=dict(
            next_screen=['This field is required.'],
            values_to_update=['This field is required.']
        ),
        screen_two=dict(
            values_to_update=dict(
                key=['This field is required.'],
                value=['This field is required.']
            )
        ),
        screen_three=dict(
            values_to_update=dict(
                key=['This field is required.'],
                value=['This field is required.']
            )
        )
    )

    def test(self):
        ussd_client = self.ussd_client()
        ussd_client.send('')
        session = ussd_session(ussd_client.session_id)

        self.assertEqual(
            session['customer_status'],
            "registered"
        )

        self.assertEqual(
            session['aged_24'],
            [
                {
                    'name': "Francis Mwangi",
                    'age': 24,
                    'height': 5.4
                },
                {
                    "name": "Wambui",
                    "age": 24,
                    "height": 5.4
                }
            ]
        )

        self.assertEqual(
            session["height_54"],
            [
                {
                    'name': "Francis Mwangi",
                    'age': 24,
                    'height': 5.4
                },
                {
                    'name': 'Isaac Karanja',
                    'age': 22,
                    'height': 5.4
                },
                {
                    "name": "Wambui",
                    "age": 24,
                    "height": 5.4
                }
            ]
        )
        # test for unregistered user
        ussd_client = self.ussd_client(phone_number=404)
        ussd_client.send('')
        session = ussd_session(ussd_client.session_id)

        self.assertEqual(
            session['customer_status'],
            "not_registered"
        )
