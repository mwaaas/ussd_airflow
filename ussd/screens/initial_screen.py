from ussd.core import UssdHandlerAbstract, load_yaml
from rest_framework import serializers
from ussd.screens.serializers import NextUssdScreenSerializer
import staticconf


class VariableDefinition(serializers.Serializer):
    file = serializers.CharField()
    namespace = serializers.CharField(max_length=100)


class InitialScreenSerializer(NextUssdScreenSerializer):
    variables = VariableDefinition(required=False)
    create_ussd_variables = serializers.DictField(default={})
    default_language = serializers.CharField(required=False,
                                             default="en")


class InitialScreen(UssdHandlerAbstract):

    screen_type = "initial_screen"

    serializer = InitialScreenSerializer

    def handle(self):

        if isinstance(self.screen_content, dict):
            if self.screen_content.get('variables'):
                variable_conf = self.screen_content['variables']
                file_path = variable_conf['file']
                namespace = variable_conf['namespace']

                # check if it has been loaded
                if not namespace in \
                        staticconf.config.configuration_namespaces:
                    load_yaml(file_path, namespace)

                self.ussd_request.session['template_namespace'] = namespace

            # create ussd variables defined int the yaml
            for key, value in \
                    self.screen_content.get('create_ussd_variables', {}).\
                            items():
                self.ussd_request.session[key] = \
                    self.evaluate_jija_expression(value, lazy_evaluating=True)

            # set default language
            self.ussd_request.session['default_language'] = \
                self.screen_content.get('default_language', 'en')
            return self.ussd_request.forward(
                self.screen_content['next_screen']
            )
        else:
            return self.ussd_request.forward(self.screen_content)