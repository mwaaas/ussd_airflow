=====
Setup
=====

- Run the following command to install

.. code-block:: text

    pip install ussd_airflow

- Add **ussd_airflow** in Installed application

    .. code-block:: python

        INSTALLED_APPS = [
        'ussd.apps.UssdConfig',
        ]

- Add ussd view to handle ussd request.
    - To use an existing ussd view that is implemented to handle
      AfricasTalking ussd gateway

        .. code-block:: python

            from ussd.views import AfricasTalkingUssdGateway

            urlpatterns = [
                url(r'^africastalking_gateway',
                    AfricasTalkingUssdGateway.as_view(),
                    name='africastalking_url')
                ]

      To test the ussd view do this curl request.

      .. code-block:: text

        curl -X POST -H "Content-Type: application/json"
        -H "Cache-Control: no-cache"
        -H "Postman-Token: 3e3f3fb9-99b9-b47d-a358-618900d486c6"
        -d '{"phoneNumber": "400","sessionId": "105","text":"1",
        "serviceCode": "312"}'
        "http://{your_host}/{you_path}/africastalking_gateway"

    - To create your own Ussd View.
            .. autoclass:: ussd.core.UssdView
