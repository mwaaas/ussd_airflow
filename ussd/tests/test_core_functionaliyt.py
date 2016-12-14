from django.test import TestCase
from ussd.core import _registered_ussd_handlers, \
    UssdHandlerAbstract, MissingAttribute, InvalidAttribute, UssdRequest
from rest_framework import serializers


class SampleSerializer(serializers.Serializer):
    text = serializers.CharField()


class TestHandlerRegistration(TestCase):

    def test_happy_case(self):

        class TestOne(UssdHandlerAbstract):
            screen_type = "test_one"
            serializer = SampleSerializer

            def handle(self, req):
                pass

        self.assertTrue(_registered_ussd_handlers.get("test_one"))

        self.assertTrue(
            _registered_ussd_handlers['test_one'] == TestOne
        )

    @staticmethod
    def test_missing_screen_type_attribute():

        try:
            # missing screen_type
            class TestTwo(UssdHandlerAbstract):
                serializer = SampleSerializer
                def handle(self, req):
                    pass

            assert False, "should raise missing attriute name"
        except MissingAttribute:
            pass

    @staticmethod
    def test_missing_handle_attribute():

        try:
            # missing handle
            class Testthree(UssdHandlerAbstract):

                screen_type = "test_three"
                serializer = SampleSerializer

            assert False, "should raise missing attriute name"
        except MissingAttribute:
            pass

    @staticmethod
    def test_missing_serializer_attribute():

        try:
            # missing validate schema
            class TestFour(UssdHandlerAbstract):
                screen_type = 'test_four'


            assert False, "should raise missing attriute name"
        except MissingAttribute:
            pass

    @staticmethod
    def test_invalid_serializer():

        try:
            # invalid serializer
            class TestFive(UssdHandlerAbstract):
                screen_type = 'test_five'
                serializer = "Sample serializer"

                def handle(self, req):
                    pass


            assert False, "should raise invalid serializer"
        except InvalidAttribute:
            pass


class TestUssdRequestCreation(TestCase):

    def test(self):
        session_id = '1234'
        ussd_request = UssdRequest('1234', '200', '', 'en')

        self.assertTrue(len(session_id) < 8)

        self.assertTrue(len(ussd_request.session_id) >= 8)
