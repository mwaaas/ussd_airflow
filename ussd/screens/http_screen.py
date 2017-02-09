from json import JSONDecodeError

from ussd.core import UssdHandlerAbstract
from ussd.screens.serializers import NextUssdScreenSerializer
from rest_framework import serializers
import requests
from ussd.tasks import http_task
import json
import inspect


class HttpScreenConfSerializer(serializers.Serializer):
    method = serializers.ChoiceField(
        ("post", "get", "put", "delete")
    )
    url = serializers.CharField(max_length=255)


class HttpScreenSerializer(NextUssdScreenSerializer):
    session_key = serializers.CharField()
    synchronous = serializers.BooleanField(required=False)
    http_request = HttpScreenConfSerializer()


class HttpScreen(UssdHandlerAbstract):
    """
    This screen is invisible to the user. Its used if you want to make an
    api call. Its very if you want to make a api call so that you can show
    the user the results in the next screen.

    For instance you can make call for balance check using this screen.
    And display the balance in the next screen.

    Fields used to create this screen:

        1. http_request
            This field contains all the fields used to make http request.
            It contains the following fields:
                a. method
                    This is the request method to use.
                        either: get, post, put, delete
                b. url
                    This is the url to be used to make the api call
                c. And all the parameters python request module would accept

                you will example below

        2. session_key
            In this screen the api call is expected to return json body.
            The json body is saved in session using this session_key

        3. synchronous (optional defaults to true)
           This defines the nature of the api call. If its asynchronous the
           request will be made later in celery task.

        4. next_screen
            After the api call has been made or been scheduled to celery task
            ussd request is forwarded to this next_screen

    Examples of router screens:

        .. literalinclude:: .././ussd/tests/sample_screen_definition/valid_http_screen_conf.yml
    """
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
            self.logger.info("response", status_code=response.status_code,
                             content=response.content)

            for i in inspect.getmembers(response):
                # Ignores anything starting with underscore
                # (that is, private and protected attributes)
                if not i[0].startswith('_'):
                    # Ignores methods
                    if not inspect.ismethod(i[1]) and \
                                    type(i[1]) in \
                                    (str, dict, int, dict, float, list, tuple):
                        if len(i) == 2:
                            response_to_save.update(
                                {i[0]: i[1]}
                            )
            try:
                response_content = json.loads(response.content.decode())
            except JSONDecodeError:
                response_content = response.content.decode()

            if isinstance(response_content, dict):
                response_to_save.update(
                    response_content
                )

            # update content to save the one that has been decoded
            response_to_save.update(
                {"content": response_content}
            )

        # save response in session
        self.ussd_request.session[self.screen_content['session_key']] = \
            response_to_save
        return self.ussd_request.forward(self.screen_content['next_screen'])
