import uuid
import requests
import staticconf
from django.test import LiveServerTestCase
from django.urls import reverse
from ussd.core import UssdView
from ussd.tests.sample_screen_definition import path


class UssdTestClient(object):
    def __init__(self, host, session_id=None, phone_number=200,
                 language='en'):
        self.phone_number = phone_number
        self.language = language
        self.session_id = session_id \
            if session_id is not None \
            else str(uuid.uuid4())
        host = host if host is not None else self.live_server_url
        self.url = host + reverse('africastalking_url')

    def send_(self, ussd_input):
        response = requests.post(
            url=self.url,
            data={
                "sessionId": self.session_id,
                "text": ussd_input,
                "phoneNumber": self.phone_number,
                "serviceCode": "test",
                "language": self.language
            }
        )
        return response

    def send(self, ussd_input):
        return self.send_(ussd_input).content.decode()


class UssdTestCase(object):
    """
    this contains two test that are required in each screen test case
    """

    class BaseUssdTestCase(LiveServerTestCase):

        def setUp(self):
            file_yml = self.__module__.split('.')[-1]. \
                           replace('test_', '') + '_conf.yml'
            self.valid_yml = 'valid_' + file_yml
            self.invalid_yml = 'invalid_' + file_yml
            self.namespace = self.__module__.split('.')[-1]
            self.maxDiff = None

        def _test_ussd_validation(self, yaml_to_validate, expected_validation,
                                  expected_errors):

            staticconf.YamlConfiguration(
                path + '/' + yaml_to_validate,
                namespace=self.namespace,
                flatten=False)

            ussd_screens = staticconf.config. \
                get_namespace(self.namespace). \
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
                                       self.validation_error_message)

        def ussd_client(self, **kwargs):
            class UssdTestClient(object):
                def __init__(self, host, session_id=None, phone_number=200,
                             language='en', extra_payload=None,
                             service_code="test"):
                    if extra_payload is None:
                        extra_payload = {}
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

            customer_journey_conf = {
                'customer_journey_conf': self.valid_yml
            }
            if 'extra_payload' in kwargs:
                kwargs['extra_payload'].update(
                    customer_journey_conf
                )
            else:
                kwargs['extra_payload'] = customer_journey_conf

            return UssdTestClient(self.live_server_url, **kwargs)
