from ussd.core import UssdHandlerAbstract, UssdResponse
from ussd.screens.serializers import UssdContentBaseSerializer


class QuitScreen(UssdHandlerAbstract):
    screen_type = "quit_screen"
    serializer = UssdContentBaseSerializer

    def handle(self):
        return UssdResponse(self.get_text(), status=False)
