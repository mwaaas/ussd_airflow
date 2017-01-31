from django.core.management import BaseCommand
from django.core.management import CommandError
from django.core.management import call_command
from ussd_airflow.settings import BASE_DIR

path = BASE_DIR + '/ussd_airflow_app_tpl'


class Command(BaseCommand):
    help = 'create ussd app'

    def add_arguments(self, parser):
        parser.add_argument('ussd_app_name', nargs='+', type=str)

    def handle(self, *args, **options):
        try:
            if len(options.get('ussd_app_name')[0].split()) > 1:
                raise CommandError
            app_name = options.get('ussd_app_name')[0]
            call_command('startapp', app_name, template=path)
        except CommandError:
            print('Provide a valid django App Name as documented here: '
                  ' https://docs.djangoproject.com/en/1.10/ref/django-admin/')
