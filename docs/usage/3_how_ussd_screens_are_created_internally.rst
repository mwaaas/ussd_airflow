====================================
How is ussd customer journey created
====================================

How the ussd content is created in yaml
-----------------------------------------------
In ussd airflow ussd customer journey is created and defined by
yaml

Each section in yaml is a ussd screen. Each section must have an
key of value pair of screen_type: screen_type

The screen type defines the logic and how the screen is going to be
rendered.

The following are the  supported screen types:

.. automodule:: ussd.screens.input_screen
   :members:

.. automodule:: ussd.screens.menu_screen