import importlib
import yaml
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


class YamlToGo:
    def __init__(self,file):
        file = open(file)
        self.yaml = yaml.load(file)
        file.close()

        self.count = 0

    def get_model_data(self):
        data = {}
        links = []
        for index,value in enumerate(self.yaml):
            data[value] = self.convert_screen(value,index)

        for index,value in enumerate(self.yaml):
            links.extend(self.get_links(value,data))

        dataArray = []
        dataArray.append(data.pop('initial_screen'))
        dataArray.extend(list(data.values()))

        return {'data':dataArray,'links':links}

    def get_text(self,text):
        if type(text) is str:
            return text
        else:
            return text['en']

    def convert_screen(self,screen,key):
        _data = {}
        name = screen
        screen = self.yaml[screen]
        type = screen['type']
        _data['key'] = key
        _data['title'] = name

        if type == 'initial_screen':
            _data['items'] = [
                {'index':1,'portName':'out1','text':'Initial Screen'}
            ]
        elif type == 'input_screen':
            _data['items'] = [
                {'index':'1','portName':'out1','text':self.get_text(screen['text'])}
            ]
        elif type.endswith('http_screen'):
            _data['items'] = [
                {'index':'1','portName':'out1','text':'Http Request Screen'}
            ]

        elif type == 'menu_screen':
            _data['items'] = []
            for index,value in enumerate(screen['options']):
                _data['items'].append({
                    'index' : index+1,
                    'text' : self.get_text(value['text']),
                    'portName': 'out' + str(index)
                })

        elif type == 'router_screen':
            _data['items'] = []

            for index,value in enumerate(screen['router_options']):
                _data['items'].append({
                    'index' : index+1,
                    'text' : value['expression'],
                    'portName': 'out' + str(index)
                })

            if 'default_next_screen' in screen:
                _data['items'].append({
                    'index' : len(screen['router_options'])+1,
                    'text' : 'Default Route',
                    'portName':'outDefault'
                })


        elif type == 'quit_screen':
            _data['items'] = [
                {'index':1,'portName':'out1','text':self.get_text(screen['text'])}
            ]

        return _data

    def get_links(self,screen,data):
        _data = []
        name = screen
        screen = self.yaml[screen]
        type = screen['type']

        if type == 'initial_screen':
            _data = [
                {
                    'from' : data[name]['key'],
                    'to' : data[screen['next_screen']]['key'],
                    'fromPort':'out1'
                }
            ]
        elif type == 'input_screen':
            _data = [
                {
                    'from': data[name]['key'],
                    'to': data[screen['next_screen']]['key'],
                    'fromPort': 'out1'
                }
            ]
        elif type.endswith('http_screen'):
            _data = [
                {
                    'from': data[name]['key'],
                    'to': data[screen['next_screen']]['key'],
                    'fromPort': 'out1'
                }
            ]

        elif type == 'menu_screen':
            for index, value in enumerate(screen['options']):
                _data.append({
                    'from': data[name]['key'],
                    'to': data[value['next_screen']]['key'],
                    'fromPort': 'out' + str(index)
                })

        elif type == 'router_screen':
            if 'default_next_screen' in screen:
                _data.append({
                    'from' : data[name]['key'],
                    'to' : data[screen['default_next_screen']]['key'],
                    'fromPort' : 'outDefault'
                })
            for index, value in enumerate(screen['router_options']):
                _data.append({
                    'from': data[name]['key'],
                    'to': data[value['next_screen']]['key'],
                    'fromPort': 'out' + str(index)
                })


        elif type == 'quit_screen':
            pass

        return _data
