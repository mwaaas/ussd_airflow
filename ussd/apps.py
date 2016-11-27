from django.apps import AppConfig


class UssdConfig(AppConfig):
    name = 'ussd'

    def ready(self):
        # register all types of screens
        from ussd.ussd_screens import InputScreen
