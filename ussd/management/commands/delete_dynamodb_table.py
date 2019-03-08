from django.core.management import BaseCommand
from botocore.exceptions import ClientError
from ussd.store.journey_store.DynamoDb import dynamodb_connection_factory


class Command(BaseCommand):
    help = "delete dynamodb tables"

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete_all', '--delete_all',
            default=False,
            help='Boolean ',
            action='store_true',
            dest='delete_all'
        )

    def handle(self, *args, **options):
        connection = dynamodb_connection_factory(low_level=True, endpoint="http://dynamodb:8000")
        tables = connection.list_tables().get('TableNames')

        for table_name in tables:
            if table_name.startswith("test") or options.get('delete_all'):
                try:
                    connection.delete_table(
                        TableName=table_name
                    )
                except ClientError as e:
                    if e.response['Error']['Code'] != \
                            'ResourceNotFoundException':
                        raise e

                if not options.get('ignore_logs'):
                    self.stdout.write(
                        "{0} dynamble table  deleted".format(table_name))
