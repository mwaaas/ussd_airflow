from ussd.core import UssdView, UssdRequest, APIView
from rest_framework.response import Response
from ussd.tests.sample_screen_definition import path


class AfricasTalkingUssdGateway(UssdView):
    ussd_customer_journey_file = path + "/valid_input_screen_conf.yml"
    ussd_customer_journey_namespace = "AfricasTalkingUssdGateway"

    def post(self, req):
        ussd_request = UssdRequest(
            phone_number=req.data['phoneNumber'].strip('+'),
            session_id=req.data['sessionId'],
            ussd_input=req.data['text'],
            service_code=req.data['serviceCode'],
            language='en'
        )

        return ussd_request