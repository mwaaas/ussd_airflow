import importlib
from datetime import datetime

date_format = "%Y-%m-%d %H:%M:%S.%f"


def str_to_class(import_path):
    module_name, class_name = import_path.rsplit(".", 1)
    try:
        module_ = importlib.import_module(module_name)
        try:
            class_ = getattr(module_, class_name)
        except AttributeError:
            raise Exception('Class does not exist')
    except ImportError:
        raise Exception('Module does not exist')
    return class_


def datetime_to_string(date_obj: datetime):
    return date_obj.strftime(date_format)


def string_to_datetime(date_str_obj: str):
    return datetime.strptime(date_str_obj, date_format)
