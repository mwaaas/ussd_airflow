from django.test import TestCase
from ussd.core import _registered_ussd_handlers, \
    UssdHandlerAbstract, MissingAttribute, InvalidAttribute


class TestHandlerRegistration(TestCase):

    def test_happy_case(self):

        class TestOne(UssdHandlerAbstract):
            screen_type = "test_one"

            @staticmethod
            def validate_schema(file_name):
                pass

            def handle(self, req):
                pass

        self.assertTrue(_registered_ussd_handlers.get("test_one"))

        self.assertTrue(
            _registered_ussd_handlers['test_one'] == TestOne
        )

    def test_missing_screen_type_attribute(self):

        try:
            # missing screen_type
            class TestTwo(UssdHandlerAbstract):

                @staticmethod
                def validate_schema(file_name):
                    pass

                def handle(self, req):
                    pass

            assert False, "should raise missing attriute name"
        except MissingAttribute:
            pass

    def test_missing_handle_attribute(self):

        try:
            # missing handle
            class Testthree(UssdHandlerAbstract):

                screen_type = "test_three"

                @staticmethod
                def validate_schema(file_name):
                    pass

            assert False, "should raise missing attriute name"
        except MissingAttribute:
            pass

    def test_missing_validate_attribute(self):

        try:
            # missing validate schema
            class TestFour(UssdHandlerAbstract):
                screen_type = 'test_four'
                @staticmethod
                def handle(file_name):
                    pass

            assert False, "should raise missing attriute name"
        except MissingAttribute:
            pass