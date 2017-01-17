from ussd.core import UssdHandlerAbstract, UssdResponse
from ussd.screens.serializers import UssdContentBaseSerializer


class QuitScreen(UssdHandlerAbstract):
    """
    This is the last screen to be shown in a ussd session.

    Its the easiest screen to create. It requires only text

    Example of quit screen:

        .. literalinclude:: .././ussd/tests/sample_screen_definition/valid_quit_screen_conf.yml
    """
    screen_type = "quit_screen"
    serializer = UssdContentBaseSerializer

    def handle(self):
        return UssdResponse(self.get_text(), status=False)
