from ussd.core import UssdHandlerAbstract
from ussd.screens.serializers import NextUssdScreenSerializer
from rest_framework import serializers
import requests
from ussd.tasks import http_task
import json


class HttpScreenConfSerializer(serializers.Serializer):
    method = serializers.ChoiceField(
        ("post", "get", "put", "delete")
    )
    url = serializers.URLField()


class HttpScreenSerializer(NextUssdScreenSerializer):
    session_key = serializers.CharField()
    synchronous = serializers.BooleanField(required=False)
    http_request = HttpScreenConfSerializer()


class HttpScreen(UssdHandlerAbstract):
    screen_type = "http_screen"
    serializer = HttpScreenSerializer

    def render_request_conf(self, data):
        if isinstance(data, str):
            return self._render_text(data)

        elif isinstance(data, list):
            list_data = []
            for i in data:
                list_data.append(self.render_request_conf(i))

            return list_data

        elif isinstance(data, dict):
            dict_data = {}
            for key, value in data.items():
                dict_data.update(
                    {key: self.render_request_conf(value)}
                )
            return dict_data
        else:
            return data

    def handle(self):
        http_request_conf = self.render_request_conf(
            self.screen_content['http_request']
        )
        response_to_save = {}
        if self.screen_content.get('synchronous', False):
            http_task.delay(request_conf=http_request_conf)
        else:
            self.logger.info("sending_request", **http_request_conf)
            response = requests.request(**http_request_conf)
            self.logger.info("response", status_code=response.status_code, content=response.content)
            response_to_save = json.loads(response.content.decode())
        # save response in session
        self.ussd_request.session[self.screen_content['session_key']] = response_to_save

        return self.ussd_request.forward(self.screen_content['next_screen'])
