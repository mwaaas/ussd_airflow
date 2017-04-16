from ussd.core import UssdHandlerAbstract
from ussd.screens.serializers import NextUssdScreenSerializer
from rest_framework import serializers
from ussd.tasks import http_task


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

    def handle(self):
        http_request_conf = self.render_request_conf(
            self.ussd_request.session,
            self.screen_content['http_request']
        )

        if self.screen_content.get('synchronous', False):
            http_task.delay(request_conf=http_request_conf)
        else:
            self.make_request(
                http_request_conf=http_request_conf,
                response_session_key_save=self.screen_content['session_key'],
                session=self.ussd_request.session,
                logger=self.logger
            )
        return self.route_options()
