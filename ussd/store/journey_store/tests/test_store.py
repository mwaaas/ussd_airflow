from django.test import TestCase
from django.core.exceptions import ValidationError
from copy import deepcopy
from ussd.core import UssdView
from ..DummyStore import DummyStore
from ..DynamoDb import DynamoDb
from django.core import management
from django.conf import settings


class TestDriverStore:
    class BaseDriverStoreTestCase(TestCase):

        maxDiff = None

        def setUp(self):
            # setup driver instance
            self.driver = self.setup_driver()

        def tearDown(self):
            self.driver.flush()

        def test_creating_invalid_journey(self):
            sample_journey = {
                "initial_screen": {
                    "type": "initial_screen",
                    "next_screen": "end_screen",
                    "default_language": "en"
                },
            }

            self.assertRaises(ValidationError,
                              self.driver.save,
                              name="journey_a",
                              journey=sample_journey,
                              version="0.0.2")

        def test_creating_journey(self):
            sample_journey = {
                "initial_screen": {
                    "type": "initial_screen",
                    "next_screen": "end_screen",
                    "default_language": "en"
                },
                "end_screen": {
                    "type": "quit_screen",
                    "text": "end screen"
                }
            }

            # Creating journey_a
            sample_journey_one = deepcopy(sample_journey)

            sample_journey_two = deepcopy(sample_journey_one)
            sample_journey_two['end_screen']['text'] = "end screen of sample journey two"

            sample_journey_three = deepcopy(sample_journey)
            sample_journey_three['end_screen']['text'] = "end screen of sample journey three"

            self.driver.save(name="journey_a", journey=sample_journey_one, version="0.0.1")
            self.driver.save(name="journey_a", journey=sample_journey_two, version="0.0.2")
            self.driver.save(name="journey_a", journey=sample_journey_three, version="0.0.3")


            # Creating journey_b
            sample_journey_b_one = deepcopy(sample_journey)
            sample_journey_b_one['end_screen']['text'] = "end screen of sample journey_b one"

            sample_journey_b_two = deepcopy(sample_journey_b_one)
            sample_journey_b_two['end_screen']['text'] = "end screen of sample journey_b two"

            sample_journey_b_three = deepcopy(sample_journey_b_one)
            sample_journey_b_three['end_screen']['text'] = "end screen of sample journey_b three"

            self.driver.save(name="journey_b", journey=sample_journey_b_one, version="0.0.1")
            self.driver.save(name="journey_b", journey=sample_journey_b_two, version="0.0.2")
            self.driver.save(name="journey_b", journey=sample_journey_b_three, version="0.0.3")

            # test getting the journey a
            a = sample_journey_two
            b = self.driver.get('journey_a', '0.0.2')
            self.assertDictEqual(sample_journey_two, self.driver.get('journey_a', '0.0.2'))
            self.assertEqual(sample_journey_three, self.driver.get('journey_a', '0.0.3'))
            self.assertEqual(sample_journey_one, self.driver.get('journey_a', '0.0.1'))

            # test getting the journey b
            self.assertEqual(sample_journey_b_two, self.driver.get('journey_b', '0.0.2'))
            self.assertEqual(sample_journey_b_three, self.driver.get('journey_b', '0.0.3'))
            self.assertEqual(sample_journey_b_one, self.driver.get('journey_b', '0.0.1'))

            # test that you cannot save/update with the same version
            self.assertRaises(ValidationError, self.driver.save, name="journey_a",
                              journey=sample_journey_two, version="0.0.3")

            # test getting all the journeys
            self.assertDictEqual(
                {"0.0.1": sample_journey_one, "0.0.2": sample_journey_two, "0.0.3": sample_journey_three},
                self.driver.all('journey_a'))

            # test getting the latest journey
            self.assertEqual(sample_journey_three, self.driver.get('journey_a'))

            # test getting part of screen alone
            self.assertEqual(sample_journey_three['end_screen'],
                             self.driver.get('journey_a', screen_name='end_screen'))
            self.assertEqual(sample_journey_two['end_screen'],
                             self.driver.get('journey_a', version="0.0.2", screen_name='end_screen'))

            # sanity check
            assert sample_journey_two['end_screen'] != sample_journey['end_screen']

            # testing deleting
            self.driver.delete('journey_a', version="0.0.1")
            self.assertIsNone(self.driver.get('journey_a', version="0.0.1"))

            # check that it hasn't deleted anything
            self.assertEqual(len(self.driver.all('journey_a')), 2)

            # deleting all journeys including the versions
            self.driver.delete('journey_a')
            self.assertEqual(len(self.driver.all('journey_a')), 0)

        def test_saving_journeys_thats_still_in_edit_mode(self):
            sample_journey = {
                "initial_screen": {
                    "type": "initial_screen",
                    "next_screen": "end_screen",
                    "default_language": "en"
                },
                "end_screen": {
                    "type": "quit_screen",
                    "text": "end screen"
                }
            }

            self.driver.save(name="journey_a", journey=sample_journey, version="0.0.1")

            self.assertEqual(sample_journey, self.driver.get('journey_a', '0.0.1'))

            sample_journey_edit_mode = {
                "initial_screen": {
                    "type": "initial_screen",
                    "next_screen": "end_screen",
                    "default_language": "en"
                },
            }

            # confirm its invalid
            is_valid, errors = UssdView.validate_ussd_journey(sample_journey_edit_mode)
            self.assertFalse(is_valid)

            # but we can still save it under edit mode
            self.driver.save(name='journey_a', journey=sample_journey_edit_mode, edit_mode=True)

            # stills get the valid one that was saved.
            self.assertEqual(sample_journey, self.driver.get('journey_a'))

            # getting the one use edit mode
            self.assertEqual(sample_journey_edit_mode, self.driver.get('journey_a', edit_mode=True))

            sample_journey_edit_mode['invalid_screen'] = "invalid_screen"

            # and we can still save it again
            self.driver.save(name='journey_a', journey=sample_journey_edit_mode, edit_mode=True)
            self.assertEqual(sample_journey_edit_mode, self.driver.get('journey_a', edit_mode=True))


class TestDummyStore(TestDriverStore.BaseDriverStoreTestCase):

    @staticmethod
    def setup_driver() -> DummyStore:
        return DummyStore()


class TestDynamodb(TestDriverStore.BaseDriverStoreTestCase):

    @staticmethod
    def setup_driver() -> DynamoDb:
        return DynamoDb(settings.DYNAMODB_TABLE, "http://dynamodb:8000")
