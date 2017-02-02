from django.apps import AppConfig
import pkgutil



def get_all_screens_module(path_name, package_name, package_list=None):
    package_list = [] if package_list is None else package_list
    for module_loader, name, ispkg in pkgutil.iter_modules((path_name, )):
        if "_screen" in name and not ispkg and\
                        package_name not in package_list:
            __import__(package_name + '.' + name)
            package_list.append(package_name + '.' + name)
    return package_list


class UssdConfig(AppConfig):
    name = 'ussd'

    def ready(self):
        from ussd import screens
        path_name = screens.__path__[0]
        package_name = screens.__name__

        loaded_screens = get_all_screens_module(path_name, package_name)

        for i in loaded_screens:
            print("loaded screens:", i)
        print("loading filters")
        from ussd.filters import date_filters
        from ussd.filters import dict_filters
        from ussd.filters import list_filters
