import sys
from django.test.runner import DiscoverRunner
from django.core import management
from os import environ
from django.conf import settings


if sys.argv[1] == "test":
    # patch DiscoverRunner setup database to be able to create
    # dynamo db on startup
    original_setup_database = DiscoverRunner.setup_databases

    def custom_setup_database(*args, **kwargs):
        # we create dynamod db then call the normal setup database
        management.call_command('delete_dynamodb_table')
        management.call_command('create_dynamo_table', table=settings.DYNAMODB_TABLE)
        parallel = args[0].parallel
        if parallel > 1:
            for index in range(args[0].parallel):
                management.call_command('create_dynamodb_table', table_name_suffix=str(index + 1))

        return original_setup_database(*args, **kwargs)

    DiscoverRunner.setup_databases = custom_setup_database

    # path DiscoverRunner teardown to be able to tear down dynamodb
    original_teardown_databases = DiscoverRunner.teardown_databases

    def custom_teardown_database(*args, **kwargs):
        # here we delete dynamodb table
        management.call_command("delete_dynamodb_table")
        return original_teardown_databases(*args, **kwargs)

    DiscoverRunner.teardown_databases = custom_teardown_database

    # now we need to be able to truncate data from dynamo db
    # each time a test is being  executed.
    original_setup_class = DiscoverRunner.test_suite._handleClassSetUp


    def custom_handle_class_setup(*args, **kwargs):
        from ussd.store.journey_store.DynamoDb import dynamodb_table
        # here we delete all records in dynamodb
        actual_db_name = "test_" + "django-ussd-airflow"
        db_name = settings.DATABASES["default"]['NAME']
        actual_dynamo_db_name = environ["DYNAMODB_TABLE"]

        db_suffix = db_name.replace(actual_db_name, "")

        if db_suffix:
            dynamo_db_name = "test_" + actual_dynamo_db_name + db_suffix
        else:
            dynamo_db_name = "test_" + actual_dynamo_db_name

        settings.DYNAMODB_TABLE = dynamo_db_name

        table = dynamodb_table(
            settings.DYNAMODB_TABLE,
            "http://dynamodb:8000"
        )
        scan = table.scan()
        for item in scan['Items']:
            table.delete_item(Key={'id': item.get('id')})

        return original_setup_class(*args, **kwargs)


    DiscoverRunner.test_suite._handleClassSetUp = custom_handle_class_setup