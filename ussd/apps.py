from django.apps import AppConfig
import pkgutil
import copy
import sys


def get_all_screens_module(path_name, package_name, package_list=[]):
    for module_loader, name, ispkg in pkgutil.iter_modules((path_name, )):
        if "_screen" in name and not ispkg and\
                        package_name not in package_list:
            __import__(package_name +'.'+name)
            package_list.append(package_name +'.'+name)
        if ispkg:
            new_package_list = copy.deepcopy(package_list)
            package_list, celery_route = get_all_screens_module(
                path_name + '/' + name,
                package_name + '.' + name,
                new_package_list)
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
