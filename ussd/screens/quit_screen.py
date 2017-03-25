from ussd.core import UssdHandlerAbstract, UssdResponse
from ussd.screens.serializers import UssdContentBaseSerializer
from ussd import defaults as ussd_airflow_variables

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
        # set session has expired
        self.ussd_request.session[ussd_airflow_variables.expiry] = True

        if self.initial_screen.get('ussd_report_session'):
            # schedule a task to report session
            self.fire_ussd_report_session_task(self.initial_screen,
                                               self.ussd_request.session_id,
                                               support_countdown=False)

        return UssdResponse(self.get_text(), status=False)
