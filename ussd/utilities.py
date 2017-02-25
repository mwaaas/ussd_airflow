import importlib


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
