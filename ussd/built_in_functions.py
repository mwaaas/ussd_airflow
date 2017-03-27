from ussd import VERSION
from ussd.core import register_function


@register_function
def ussd_airflow_version():
    return "v{}".format(VERSION)