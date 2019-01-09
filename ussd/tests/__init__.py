import uuid
import requests
import staticconf
from django.test import LiveServerTestCase, TestCase
from django.urls import reverse
from ussd.core import UssdView, load_yaml, render_journey_as_graph, render_journey_as_mermaid_text
from ussd.tests.sample_screen_definition import path
import os
import json


class UssdTestCase(object):
    """
    this contains two test that are required in each screen test case
    """

    class BaseUssdTestCase(LiveServerTestCase):
        validate_ussd = True

        def setUp(self):
            file_prefix = self.__module__.split('.')[-1].replace('test_', '')
            file_yml = file_prefix + '_conf.yml'
            self.valid_yml = 'valid_' + file_yml
            self.invalid_yml = 'invalid_' + file_yml
            self.mermaid_file = path + '/' + 'valid_' + file_prefix + '_mermaid.txt'
            self.graph_file = path + '/' + 'valid_' + file_prefix + '_graph.json'
            self.namespace = self.__module__.split('.')[-1]
            self.maxDiff = None

            super(UssdTestCase.BaseUssdTestCase, self).setUp()

            #

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

        def test_rendering_graph_js(self):
            if os.path.exists(self.graph_file):
                namespace = self.namespace + 'mermaid_js'
                file_path = path + '/' + self.valid_yml
                load_yaml(file_path, namespace)
                ussd_screens = staticconf.config.get_namespace(namespace). \
                    get_config_values()

                actual_graph_js = render_journey_as_graph(ussd_screens)

                expected_graph_js = json.loads(self.read_file_content(self.graph_file))

                for key, value in expected_graph_js["vertices"].items():
                    if value.get('id') == 'test_explicit_dict_loop':
                        for i in (
                                "a for apple\n",
                                "b for boy\n",
                                "c for cat\n"
                        ):
                            self.assertRegex(value.get('text'), i)
                    else:
                        self.assertDictEqual(value, actual_graph_js.vertices[key])
                # self.assertDictEqual(expected_graph_js["vertices"], actual_graph_js.vertices)

                for index, value in enumerate(expected_graph_js['edges']):
                    self.assertDictEqual(value, actual_graph_js.get_edges()[index])
                self.assertEqual(expected_graph_js["edges"], actual_graph_js.get_edges())

        def test_rendering_mermaid_js(self):
            if os.path.exists(self.mermaid_file):
                namespace = self.namespace + 'mermaid_js'
                file_path = path + '/' + self.valid_yml
                load_yaml(file_path, namespace)
                ussd_screens = staticconf.config.get_namespace(namespace).\
                    get_config_values()

                mermaid_text_format = render_journey_as_mermaid_text(ussd_screens)

                file_content = self.read_file_content(self.mermaid_file)

                expected_text_lines = file_content.split('\n')
                actual_text_lines = mermaid_text_format.split('\n')

                for index, line in enumerate(expected_text_lines):
                    self.assertEqual(line, actual_text_lines[index])

                self.assertEqual(mermaid_text_format, file_content)

        def read_file_content(self, file_path):
            with open(file_path) as f:
                mermaid_text = f.read()
            return mermaid_text


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
