from ..journey_store import JourneyStore
import boto3
from structlog import get_logger
from django.conf import settings
from botocore.config import Config
from copy import deepcopy
from boto3.dynamodb.conditions import Key

BOTO_CORE_CONFIG = getattr(
    settings, 'BOTO_CORE_CONFIG', None)
USE_LOCAL_DYNAMODB_SERVER = getattr(
    settings, 'USE_LOCAL_DYNAMODB_SERVER', False)

logger = get_logger(__name__)


# We'll find some better way to do this.
_DYNAMODB_CONN = None
_DYNAMODB_TABLE = {}


# defensive programming if config has been defined
# make sure it's the correct format.
if BOTO_CORE_CONFIG:
    assert isinstance(BOTO_CORE_CONFIG, Config)

dynamo_kwargs = dict(
    service_name='dynamodb',
    config=BOTO_CORE_CONFIG
)


def dynamodb_connection_factory(low_level=False, endpoint=None):
    """
    Since SessionStore is called for every single page view, we'd be
    establishing new connections so frequently that performance would be
    hugely impacted. We'll lazy-load this here on a per-worker basis. Since
    boto3.resource.('dynamodb')objects are state-less (aside from security
    tokens), we're not too concerned about thread safety issues.
    """
    boto_config = deepcopy(dynamo_kwargs)
    if endpoint is not None:
        boto_config["endpoint_url"] = endpoint

    if low_level:
        return boto3.client(**boto_config)

    global _DYNAMODB_CONN

    if not _DYNAMODB_CONN:
        logger.debug("Creating a DynamoDB connection.")
        _DYNAMODB_CONN = boto3.resource(**boto_config)
    return _DYNAMODB_CONN


def dynamodb_table(table: str, endpoint=None):
    global _DYNAMODB_TABLE

    if not _DYNAMODB_TABLE.get(table):
        _DYNAMODB_TABLE[table] = dynamodb_connection_factory(endpoint=endpoint).Table(table)
    return _DYNAMODB_TABLE[table]


class DynamoDb(JourneyStore):
    edit_mode_version = "-1"
    journeyName = "journeyName"
    version = "version"

    def __init__(self, table_name, endpoint=None):
        self.table_name = table_name
        self.table = dynamodb_table(table_name, endpoint=endpoint)

    def _get(self, name, version, screen_name, **kwargs):
        screen_kwarg = {}
        if screen_name is not None:
            screen_kwarg["ProjectionExpression"] = screen_name

        if version is None:
            response = self.table.query(
                KeyConditionExpression=Key(self.journeyName).eq(name) & Key(self.version).gt(self.edit_mode_version),
                **kwargs
            )
            item = response.get("Items")[-1]
        else:
            key = {
                self.journeyName: name,
                self.version: version
            }

            response = self.table.get_item(Key=key, **screen_kwarg)
            item = response.get('Item')

        if item:
            if item.get(self.journeyName):
                del item[self.journeyName]
            if item.get(self.version):
                del item[self.version]

            if screen_name:
                item = item.get(screen_name)
        return item or None

    def _all(self, name):
        results = {}
        for i in self._query(name):
            version = i[self.version]
            del i[self.journeyName]
            del i[self.version]
            results[version] = i
        return results

    def _query(self, name, **kwargs):
        response = self.table.query(
            KeyConditionExpression=Key(self.journeyName).eq(name),
            **kwargs
        )
        return response.get('Items')

    def _save(self, name, journey, version):
        item = {
                self.journeyName: name,
                self.version: version
            }
        item.update(journey)

        response = self.table.put_item(
            Item=item
        )

    def _delete(self, name, version=None):
        items = [
            {
                self.journeyName: name,
                self.version: version
            }
        ]
        if version is None:
            items = self._query(name,
                                **{"ProjectionExpression": "{0}, {1}".format(self.journeyName, self.version)})

        with self.table.batch_writer() as batch:
            for i in items:
                batch.delete_item(
                    Key={
                        self.journeyName: i[self.journeyName],
                        self.version: i[self.version]
                    }
                )

    def flush(self):
        all_records = self.table.scan()
        for i in all_records['Items']:
            self._delete(i[self.journeyName], i[self.version])
