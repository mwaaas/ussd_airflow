from ussd.tests import UssdTestCase
from ussd.core import ussd_session


class TestScreensUsingVariable(UssdTestCase.BaseUssdTestCase):
    validate_ussd = False

    def get_ussd_client(self):
        return self.ussd_client(
            generate_customer_journey=False,
            extra_payload={
                "customer_journey_conf": "sample_using_variables.yml"
            }
        )

    def test_initial_variables_are_created(self):
        ussd_client = self.get_ussd_client()

        # dial in
        ussd_client.send('')

        session = ussd_session(ussd_client.session_id)

        # check ussd variables were created
        expected_variables = {"name": "mwas", "hobbies": [],
                              "environment": "sample_variable_two"}

        for key, value in expected_variables.items():
            self.assertTrue(key in session)
            self.assertEqual(session[key], value)

    def test_using_variable(self):
        client = self.get_ussd_client()

        # dial in
        response = client.send('1')

        self.assertEqual(
            "Displaying variable in the first config bar_variable_one. "
            "press one to show variable in config two\n1. Continue\n",
            response
        )

        # select one to continue
        response = client.send('1')

        self.assertEqual(
            "Displaying variable in the second config that has overridden "
            "the second config foo_variable_two.\n1. continue\n",
            response
        )

    def excute_following_inputs(self, inputs, expected_response):
        client = self.get_ussd_client()
        response = ''
        for i in inputs:
            response = client.send(i)
        self.assertEqual(expected_response, response)
        return client

    def test_using_variable_in_router_screen(self):

        # sequence of input to reach router screen
        inputs = ['', '1', '1']

        # screen that directs to router screen
        screen_three_expected_text = "Enter your any number we compare it " \
                                     "aganist a variable " \
                                     "set in the variables.\n"

        client = self.excute_following_inputs(inputs,
                                              screen_three_expected_text)

        # enter number equal to variable number
        response = client.send(50)

        self.assertEqual(
            "The number you have entered is equal to the variable 50",
            response
        )

        client = self.excute_following_inputs(inputs,
                                              screen_three_expected_text)

        # enter number greater than input
        self.assertEqual(
            "The number you have entered is greater than the variable 50",
            client.send('55')
        )

        client = self.excute_following_inputs(inputs,
                                              screen_three_expected_text)

        # enter number less than input
        self.assertEqual(
            "The number you have entered is less than "
            "the variable 50. "
            "Displaing a variable that has not been defined \n",
            client.send('40')
        )
