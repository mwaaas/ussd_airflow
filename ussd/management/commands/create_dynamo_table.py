from django.core.management import BaseCommand
from django.conf import settings
import subprocess
import sys


class Command(BaseCommand):
    help = "creates a session table if does not exist"

    def add_arguments(self, parser):
        parser.add_argument(
            '--table_name', '--table_name',
            default='journeyTable',
            help='String',
            dest='table_name'
        )

        parser.add_argument(
            '--table_name_suffix', '--table_name_suffix',
            default='',
            help='String',
            dest='table_name_suffix'
        )

    def handle(self, *args, **options):
        api_request_table = options.get('table_name')

        if sys.argv[1] == 'test':
            api_request_table = "test_" + api_request_table

        if options.get('table_name_suffix'):
            api_request_table += "_" + options.get('table_name_suffix')

        cloud_formation_parameters = "" \
                                     "WriteCapacityUnits=1 " \
                                     "DyanamoTableName={table} " \
                                     "PreRequisiteStack=None " \
                                     "RequestIndexReadCapacityUnits=1 " \
                                     "StateIndexReadCapacityUnits=1 " \
                                     "ReadCapacityUnits=1".format(table=api_request_table)

        command = 'dynamodb_cloud_formation_cli ' \
                  '--endpoint-url=http://dynamodb:8000 ' \
                  '--region=eu-west-1 --parameters="{parameters}" ' \
                  '/usr/src/app/devops/templates/cloud-formation/' \
                  'dynamodb.templates.yml ' \
                  '| sh'.format(parameters=cloud_formation_parameters)

        subprocess.check_call(['bash', '-c', command])
