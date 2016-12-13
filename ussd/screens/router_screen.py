from ussd.core import UssdHandlerAbstract
from ussd.screens.serializers import UssdBaseSerializer, \
    NextUssdScreenSerializer
from rest_framework import serializers


class RouterOptionSerializer(NextUssdScreenSerializer):
    expression = serializers.CharField(max_length=255)


class RouterSerializer(UssdBaseSerializer):
    router_options = serializers.ListField(
        child=RouterOptionSerializer()
    )


class RouterScreen(UssdHandlerAbstract):
    screen_type = "router_screen"
    serializer = RouterSerializer

    def handle(self):
        route_options = self.screen_content.get("router_options")

        for option in route_options:
            if self.evaluate_jija_expression(option['expression']):
                return self.ussd_request.forward(option['next_screen'])
        return self.ussd_request.forward(
            self.screen_content['default_next_screen']
        )
