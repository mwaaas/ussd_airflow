from ussd.core import UssdView, UssdRequest,_customer_journey_files, \
    render_journey_as_mermaid_text, convert_error_response_to_mermaid_error
from ussd.tests.sample_screen_definition import path
from django.http import HttpResponse, JsonResponse
from django.conf import settings

from django.shortcuts import render
import json
from ussd.utilities import YamlToGo
from rest_framework.views import APIView


class AfricasTalkingUssdGateway(UssdView):

    def post(self, req):
        list_of_inputs = req.data['text'].split("*")
        text = "*" if len(list_of_inputs) >= 2 and list_of_inputs[-1] == "" and list_of_inputs[-2] == "" else list_of_inputs[
            -1]

        session_id = req.data['sessionId']
        if req.data.get('use_built_in_session_management', False):
            session_id = None
        ussd_request = UssdRequest(
            phone_number=req.data['phoneNumber'].strip('+'),
            session_id=session_id,
            ussd_input=text,
            service_code=req.data['serviceCode'],
            language=req.data.get('language', 'en'),
            use_built_in_session_management=req.data.get(
                'use_built_in_session_management', False)
        )

        return ussd_request

    def get_customer_journey_conf(self, request):
        if request.data.get('customer_journey_conf'):
            return path + '/' + request.data.get('customer_journey_conf')
        return getattr(settings, 'DEFAULT_USSD_SCREEN_JOURNEY',
                       path + "/sample_customer_journey.yml")

    def get_customer_journey_namespace(self, request):
        if request.data.get('customer_journey_conf'):
            return request.data['customer_journey_conf'].replace(
                '.yml', ''
            )
        return "AfricasTalkingUssdGateway"

    def ussd_response_handler(self, ussd_response):
        if self.request.data.get('serviceCode') == 'test':
            return super(AfricasTalkingUssdGateway, self).\
                ussd_response_handler(ussd_response)
        if ussd_response.status:
            res = 'CON' + ' ' + str(ussd_response)
            response = HttpResponse(res)
        else:
            res = 'END' + ' ' + str(ussd_response)
            response = HttpResponse(res)
        return response

class MermaidText(APIView):

    def post(self, req):
        ussd_journey = req.data['journey']
        if isinstance(ussd_journey, str):
            ussd_journey = json.loads(ussd_journey)

        mermaid_options = req.data.get('mermaidOptions', {})

        mermaid_text = render_journey_as_mermaid_text(ussd_journey)

        return JsonResponse({'mermaidText': mermaid_text,
                             'mermaidOptions': mermaid_options})

class ValidateJourney(APIView):

    def post(self, req):
        journey = req.data['journey']

        if isinstance(journey, str):
            journey = json.loads(journey)

        error_type = req.data.get('error_type', 'default')

        is_valid, errors = UssdView.validate_ussd_journey(journey)


        if error_type == 'mermaid_txt':
            errors = convert_error_response_to_mermaid_error(errors)
        return JsonResponse(errors, safe=False)


def journey_visual(request):
    return render(request,'journey_visual.html',{'yaml_files':_customer_journey_files})



def journey_visual_data(request):
    yaml = request.GET.get('file',_customer_journey_files[0])
    if yaml == None:
        return HttpResponse()
    res = YamlToGo(yaml).get_model_data()
    return HttpResponse(json.dumps(res),content_type='application/json')