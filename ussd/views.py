from ussd.core import UssdView, UssdRequest, SessionStore, APIView
from rest_framework.response import Response


class AfricasTalkingUssdGateway(APIView):

    def post(self, req):
        session = SessionStore(session_key=req.data['sessionId'])

        ussd_request = UssdRequest(
            phone_number=req.data['phoneNumber'].strip('+'),
            session_id=req.data['sessionId'],
            ussd_input=req.data['text'],
            session=session,
            service_code=req.data['serviceCode'],
            ussd_yml_namespace="test_customer_journey"
        )

        return Response("hello world")