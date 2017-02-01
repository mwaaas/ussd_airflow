import uuid
import requests
import staticconf
from django.test import LiveServerTestCase
from django.urls import reverse
from ussd.core import UssdView, load_yaml
from ussd.tests.sample_screen_definition import path


class UssdTestCase(object):
    """
    this contains two test that are required in each screen test case
    """

    class BaseUssdTestCase(LiveServerTestCase):
        validate_ussd = True

        def setUp(self):
            file_yml = self.__module__.split('.')[-1]. \
                           replace('test_', '') + '_conf.yml'
            self.valid_yml = 'valid_' + file_yml
            self.invalid_yml = 'invalid_' + file_yml
            self.namespace = self.__module__.split('.')[-1]
            self.maxDiff = None

        def _test_ussd_validation(self, yaml_to_validate, expected_validation,
                                  expected_errors):

            if self.validate_ussd:
                namespace = self.namespace + str(expected_validation)
                file_path = path + '/' + yaml_to_validate
                load_yaml(file_path, namespace)
                ussd_screens = staticconf.config. \
                    get_namespace(namespace). \
                    get_config_values()

                is_valid, error_message = UssdView.validate_ussd_journey(
                    ussd_screens)

                self.assertEqual(is_valid, expected_validation, error_message)

                self.assertDictEqual(error_message,
                                     expected_errors)

        def testing_valid_customer_journey(self):
            self._test_ussd_validation(self.valid_yml, True, {})

        def testing_invalid_customer_journey(self):

            self._test_ussd_validation(self.invalid_yml, False,
                                       getattr(self,
                                               "validation_error_message",
                                               {}))

        def ussd_client(self, generate_customer_journey=True, **kwargs):
            class UssdTestClient(object):
                def __init__(self, host, session_id=None, phone_number=200,
                             language='en', extra_payload={},
                             service_code="test"):
                    self.phone_number = phone_number
                    self.language = language
                    self.session_id = session_id \
                        if session_id is not None \
                        else str(uuid.uuid4())
                    self.url = host + reverse('africastalking_url')
                    self.extra_payload = extra_payload
                    self.service_code = service_code

                def send_(self, ussd_input):
                    payload = {
                        "sessionId": self.session_id,
                        "text": ussd_input,
                        "phoneNumber": self.phone_number,
                        "serviceCode": self.service_code,
                        "language": self.language
                    }
                    payload.update(self.extra_payload)
                    response = requests.post(
                        url=self.url,
                        data=payload
                    )
                    return response

                def send(self, ussd_input):
                    return self.send_(ussd_input).content.decode()

            if generate_customer_journey:
                customer_journey_conf = {
                    'customer_journey_conf': self.valid_yml
                }
                kwargs['extra_payload'] = customer_journey_conf

            return UssdTestClient(self.live_server_url, **kwargs)
