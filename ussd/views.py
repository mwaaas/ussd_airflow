from ussd.core import UssdView, UssdRequest, APIView
from rest_framework.response import Response
from ussd.tests.sample_screen_definition import path


class AfricasTalkingUssdGateway(UssdView):

    def post(self, req):
        ussd_request = UssdRequest(
            phone_number=req.data['phoneNumber'].strip('+'),
            session_id=req.data['sessionId'],
            ussd_input=req.data['text'],
            service_code=req.data['serviceCode'],
            language=req.data.get('language', 'en')
        )

        return ussd_request

    def get_customer_journey_conf(self, request):
        if request.data.get('customer_journey_conf'):
            return path + '/' + request.data.get('customer_journey_conf')
        return path + "/valid_input_screen_conf.yml"

    def get_customer_journey_namespace(self, request):
        if request.data.get('customer_journey_conf'):
            return request.data['customer_journey_conf'].replace(
                '.yml', ''
            )
        return "AfricasTalkingUssdGateway"
