from django.core.management import call_command
from django.test import LiveServerTestCase
import json
import os
from django.conf.urls import url, include
from django.test import TestCase

from ussd_airflow import urls
from rest_framework.test import APIClient


class TestUssdAppIsNotCreated(TestCase):

    def test_app_not_created(self):
        app_name = 'TestUssdApp TestUssdApp'
        call_command('create_ussd_app', app_name)
        with self.assertRaises(ImportError):
            include(app_name)


class TestUssdAppCreation(LiveServerTestCase):
    def setUp(self):
        self.client = APIClient()

    def test_app_creation(self):
        app_name = 'TestUssdApp'
        call_command('create_ussd_app', app_name)

        ussd_url = [
            url(r'^ussd/', include('TestUssdApp.urls'))
        ]

        urls.urlpatterns += ussd_url

        end_point_url = "http://localhost:8081/ussd/TestUssdApp_ussd_gateway"
        payload = {
            "phoneNumber": "0717199135", "sessionId": "12", "text": "1", "language": "en", "serviceCode": "200"}

        response = self.client.post(end_point_url,
                                    data=json.dumps(payload),
                                    content_type="application/json",)
        self.assertEqual(response.content,
                         b'END Example Quit Screen. Delete this and define your own customer journey screens.')
        self.assertEqual(response.status_code, 200)
        print(response.status_code)
        os.system('rm -r TestUssdApp')  # Remove created app. Clean up

