"""
This test quit screen
"""
from ussd.tests import UssdTestCase


class TestQuitHandler(UssdTestCase.BaseUssdTestCase):
    validation_error_message = dict(
        example_of_quit_screen=dict(
            text=['This field is required.']
        )
    )

    def test(self):
        ussd_client = self.ussd_client(service_code="test_")

        self.assertEqual(
            "END End of this session",
            ussd_client.send('')
        )
