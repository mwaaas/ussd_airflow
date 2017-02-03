from json import JSONDecodeError

from ussd.tests import UssdTestCase
from unittest import mock
from django.http.response import JsonResponse, HttpResponse
from django.test.utils import override_settings


@override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND='memory'
    )
class TestHttpScreen(UssdTestCase.BaseUssdTestCase):
    validation_error_message = dict(
        screen_name="Screen not available",
        http_invalid_screen=dict(
            next_screen=['This field is required.'],
            session_key=['This field is required.'],
            http_request=['This field is required.']
        ),
        http_screen_invalid_method=dict(
            http_request=dict(
                method=['"done" is not a valid choice.'],
            )
        ),
        http_screen_invalid_synchronous=dict(
            synchronous=['"not boolean" is not a valid boolean.']
        )
    )

    @mock.patch("ussd.screens.http_screen.requests.request")
    def test(self, mock_request):
        mock_response = JsonResponse({"balance": 250})
        mock_request.return_value = mock_response
        ussd_client = self.ussd_client()

        self.assertEqual(
            "Testing response is being saved in "
            "session status code is 200 and "
            "balance is 250 and full content {'balance': 250}.\n",
            ussd_client.send('')
        )
        expected_calls = [
            mock.call(
                method='get',
                url="http://localhost:8000/mock/balance",
                params=dict(
                    phone_number="200",
                    session_id=ussd_client.session_id
                ),
                verify=False,
                headers={"content-type": "application/json",
                         "user-agent": "my-app/0.0.1"}
            ),
            mock.call(
                method="get",
                url="http://localhost:8000/mock/balance/200/"
            ),
            mock.call(
                method='post',
                url='http://localhost:8000/mock/balance',
                params=dict(
                    phone_numbers=[200, 201, 202],
                    session_id=ussd_client.session_id
                ),
                verify=True,
                timeout=30,
                headers={"content-type": "application/json"}
            ),
            mock.call(
                method='get',
                url="https://localhost:8000/mock/submission",
                params={'phone_number': '200',
                        'session_id': ussd_client.session_id}
            )
        ]
        # test requests that were made
        mock_request.assert_has_calls(expected_calls)

    @mock.patch("ussd.screens.http_screen.http_task")
    @mock.patch("ussd.tasks.requests.request")
    def test_async_workflow(self, mock_request, mock_http_task):
        mock_response = JsonResponse({"balance": 257})
        mock_request.return_value = mock_response

        ussd_client = self.ussd_client()
        ussd_client.send('')

        # check http_task is called
        mock_http_task.delay.assert_called_once_with(
            request_conf=dict(
                method='get',
                url="https://localhost:8000/mock/submission",
                params={'phone_number': '200',
                        'session_id': ussd_client.session_id}
            )
        )

    @mock.patch("ussd.screens.http_screen.requests.request")
    def test_json_decoding(self, mock_request):
        mock_response = HttpResponse("Balance is 257")
        mock_request.return_value = mock_response

        ussd_client = self.ussd_client()
        ussd_client.send('')

        self.assertEqual(
            "Testing response is being saved in "
            "session status code is 200 and "
            "balance is  and full content Balance is 257.\n",
            ussd_client.send('')
        )


