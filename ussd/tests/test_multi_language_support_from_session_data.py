from ussd.tests import UssdTestCase


class TestMultiLanguage(UssdTestCase.BaseUssdTestCase):
    validate_ussd = False

    def get_ussd_client(self):
        return self.ussd_client(
            generate_customer_journey=False,
            extra_payload={
                "customer_journey_conf": "valid_multi_language_support_from_session_data_conf.yml"
            }
        )

    def test_multilanguage_support(self):

        ussd_client = self.ussd_client(language='sw')


        # Dial in
        response = ussd_client.send('')

        self.assertEqual(
            "Bienvenue\n1. Bienvenue\n",
            response
        )

        response = ussd_client.send('1')

        self.assertEqual(
            "Pour compléter, saisissez une valeur\n",
            response
        )

        response = ussd_client.send('1')

        self.assertEqual(
            "Au revoir",
            response
        )