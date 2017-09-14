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

- Change session serializer to pickle serializer

    .. code-block:: python

        SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

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

      To use the existing Africastalking ussd gateway and your own ussd
      screen. Create a yaml file. On the yaml create your ussd screen.
      Learn more on how to create ussd screen here :doc:`tutorial`.
      For quick start copy the below yaml

        .. literalinclude:: .././ussd/tests/sample_screen_definition/sample_customer_journey.yml

      Next step add this to your settings. For ussd airflow to know where your
      ussd screens files are located.

        .. code-block:: python

            DEFAULT_USSD_SCREEN_JOURNEY = "/file/path/of/the/screen"

      To validate your ussd screen file. Run this command

        .. code-block:: text

            python manage.py validate_ussd_journey /file/path

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

