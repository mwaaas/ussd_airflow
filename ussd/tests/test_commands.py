from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO
from .sample_screen_definition import path
from django.core.management.base import CommandError
import json


class ValidateCustomerJourneyConfig(TestCase):
    maxDiff = None

    def test_command_output(self):
        out = StringIO()
        file_name = "{0}/valid_quit_screen_conf.yml".format(path)
        call_command('validate_ussd_journey', file_name, stdout=out)
        expected_output = {
            file_name: dict(
                valid=True,
                error_message=dict()
            )
        }
        self.assertDictEqual(expected_output, json.loads(out.getvalue()))

    def testing_invalid_ussd_journey(self):
        out = StringIO()
        file_name = "{0}/invalid_quit_screen_conf.yml".format(path)
        self.assertRaises(CommandError, call_command, 'validate_ussd_journey',
                          file_name, stdout=out)

    def test_called_with_multiple_files(self):
        out = StringIO()
        file_1 = "{0}/valid_quit_screen_conf.yml".format(path)
        file_2 = "{0}/valid_http_screen_conf.yml".format(path)
        file_3 = "{0}/valid_input_screen_conf.yml".format(path)
        call_command(
            "validate_ussd_journey",
            file_1,
            file_2,
            file_3,
            stdout=out)

        expected_output = {
            file_1: dict(
                valid=True,
                error_message={},
            ),
            file_2: dict(
                valid=True,
                error_message={}
            ),
            file_3: dict(
                valid=True,
                error_message={}
            )
        }

        self.assertDictEqual(expected_output, json.loads(out.getvalue()))

    def test_called_with_invalid_file_path(self):
        out = StringIO()

        self.assertRaises(CommandError, call_command, 'validate_ussd_journey', 'invalid_path', stdout=out)