from ussd.tests import UssdTestCase
from ussd import VERSION


class TestScreenUsing(UssdTestCase.BaseUssdTestCase):

    validate_ussd = False

    def get_ussd_client(self):
        return self.ussd_client(
            generate_customer_journey=False,
            extra_payload={
                "customer_journey_conf":
                    "teasting_using_built_in_functions.yml"
            }
        )

    def test(self):
        client = self.get_ussd_client()
        # dial in
        response = client.send('1')

        self.assertEqual(
            "You are using this version v{version}".format(version=VERSION),
            response
        )
