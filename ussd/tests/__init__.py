from django.urls import reverse
import requests
import uuid
from django.test import LiveServerTestCase
import staticconf
from ussd.tests.sample_screen_definition import path
from ussd.core import UssdView
from unittest import  skip


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
            file_yml = self.__module__.split('.')[-1].\
                           replace('test_', '') + '_conf.yml'
            self.valid_yml = 'valid_' + file_yml
            self.invalid_yml = 'invalid_' + file_yml
            self.namespace = self.__module__.split('.')[-1]
            self.maxDiff = None

        def testing_valid_customer_journey(self):
            # load yaml file
            namespace = 'valid' + self.namespace
            staticconf.YamlConfiguration(
                path + '/' + self.valid_yml,
                namespace=namespace,
                flatten=False)

            ussd_screens = staticconf.config.\
                get_namespace(namespace).\
                get_config_values()

            is_valid, error_message = UssdView.validate_ussd_journey(
                ussd_screens)
            self.assertTrue(is_valid, error_message)

        def testing_invalid_customer_journey(self):
            namespace = 'invalid' + self.namespace
            staticconf.YamlConfiguration(
                path + '/' + self.invalid_yml,
                namespace=namespace,
                flatten=False)

            ussd_screens = staticconf.config.\
                get_namespace(namespace).\
                get_config_values()

            is_valid, error_message = UssdView.validate_ussd_journey(
                ussd_screens)

            self.assertFalse(
                is_valid
            )

            self.assertDictEqual(error_message,
                                 self.validation_error_message)

        def ussd_client(self, **kwargs):
            class UssdTestClient(object):
                def __init__(self, host, session_id=None, phone_number=200,
                             language='en', extra_payload={}):
                    self.phone_number = phone_number
                    self.language = language
                    self.session_id = session_id \
                        if session_id is not None \
                        else str(uuid.uuid4())
                    self.url = host + reverse('africastalking_url')
                    self.extra_payload = extra_payload

                def send_(self, ussd_input):
                    payload = {
                            "sessionId": self.session_id,
                            "text": ussd_input,
                            "phoneNumber": self.phone_number,
                            "serviceCode": "test",
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