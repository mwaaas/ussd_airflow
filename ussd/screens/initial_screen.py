from ussd.core import UssdHandlerAbstract, load_yaml
from rest_framework import serializers
from ussd.screens.serializers import NextUssdScreenSerializer
import staticconf


class VariableDefinition(serializers.Serializer):
    file = serializers.CharField()
    namespace = serializers.CharField(max_length=100)


class ValidateResposeSerialzier(serializers.Serializer):
    expression = serializers.CharField(max_length=255)


class UssdReportSessionSerializer(serializers.Serializer):
    session_key = serializers.CharField(max_length=100)
    validate_response = serializers.ListField(
        child=ValidateResposeSerialzier()
    )
    request_conf = serializers.DictField()



class InitialScreenSerializer(NextUssdScreenSerializer):
    variables = VariableDefinition(required=False)
    create_ussd_variables = serializers.DictField(default={})
    default_language = serializers.CharField(required=False,
                                             default="en")
    ussd_report_session = UssdReportSessionSerializer(required=False)


class InitialScreen(UssdHandlerAbstract):
    """This screen is mandatory in any customer journey.
    It is the screen all new ussd session go to.

    example of one

        .. code-block:: yaml

            initial_screen: enter_height

            first_screen:
            type: quit
            text: This is the first screen

    Its is also used to define variable file if you have one.
    Example when defining variable file

        .. code-block:: yaml

            initial_screen:
                screen: screen_one
                variables:
                    file: /path/of/your/variable/file.yml
                    namespace: used_to_save_the_variable
    Sometimes you want to send ussd session to some 3rd party application when
    the session has been terminated.
    
    We can easily do that at end of session i.e quit screen, But for those
    scenarios where session is terminated by user or mno we don't know that 
    unless the mno send us a request. 
    
    Most mnos don't send notifier 3rd party application about the session being
    dropped. The work around we use is schedule celery task to run after 
    15 minutes ( by that time we know there is no active session)
    
    Below is an example of how to schedule a ussd report session after 15min
        
    
    example:
        
        .. code-block:: yaml
        
            initial_screen:
                type: initial_screen
                next_screen: screen_one
                ussd_report_session:
                    session_key: reported
                    retry_mechanism:
                        max_retries: 3
                    validate_response:
                        - expression: "{{reported.status_code}} == 200"
                    request_conf:
                        url: localhost:8006/api
                        method: post
                        data:
                            ussd_interaction: "{{ussd_interaction}}"
                            session_id: "{{session_id}}"
                    async_parameters:
                        queue: report_session
                        countdown: 900
                    
        
        Lets explain the variables in ussd_report_session
            - session_key ( Mandatory )
                response of ussd report session would be saved under that key
                in session store
                
            - request_conf ( Mandatory )
                Those are the parameters to be used to make request to 
                report ussd session
            
            - validate_response ( Mandatory )
                After making ussd report request the framework will evaluate 
                your options and if one of them is valid it would 
                mark session as posted (This is used to avoid double ussd 
                submission)
                
            - retry_mechanism ( Optional )
                After validating your response and all of them fail 
                we will go ahead and retry if this field is active. 
                
            - async_parameters ( Optional )
                This is are the parameters used to make ussd request
            
            
                
    """
    screen_type = "initial_screen"

    serializer = InitialScreenSerializer

    def handle(self):

        if isinstance(self.screen_content, dict):
            if self.screen_content.get('variables'):
                self.load_variable_files()

            # create ussd variables defined int the yaml
            self.create_variables()

            # set default language
            self.set_language()

            next_screen = self.screen_content['next_screen']

            # call report session
            if self.screen_content.get('ussd_report_session'):
                self.fire_ussd_report_session_task(self.initial_screen,
                                                   self.ussd_request.session_id
                                                   )
        else:
            next_screen = self.screen_content
        return self.route_options(route_options=next_screen)

    def create_variables(self):
        for key, value in \
                self.screen_content.get('create_ussd_variables', {}). \
                        items():
            self.ussd_request.session[key] = \
                self.evaluate_jija_expression(value,
                                              lazy_evaluating=True,
                                              session=self.ussd_request.session
                                              )

    def load_variable_files(self):
        variable_conf = self.screen_content['variables']
        file_path = variable_conf['file']
        namespace = variable_conf['namespace']

        # check if it has been loaded
        if not namespace in \
                staticconf.config.configuration_namespaces:
            load_yaml(file_path, namespace)

        self.ussd_request.session.update(
            staticconf.config.configuration_namespaces[namespace].
            configuration_values
        )

    def set_language(self):
        self.ussd_request.session['default_language'] = \
            self.screen_content.get('default_language', 'en')
