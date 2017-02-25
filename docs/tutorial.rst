=====================
Creating ussd screens
=====================

This document is a whirlwind tour of how to create ussd screen.

Strong feature of ussd airflow is to create ussd screen via yaml and not code.
This make it easier to give the product owners to design ussd without
knowing how to code

In ussd airflow customer journey is created via yaml.
Each section in a yaml defines a ussd screen.
There different types of ussd and each type has its own rule on how
to write ussd application

Common rule in creating any kind of screen
**Each screen has field called "type"** apart from initial_screen

The following are types of ussd and the rules to write them.

1. Initial screen (type -> initial_screen)
------------------------------------------
This screen is mandatory in any customer journey.
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


2. Input screen (type -> input_screen)
--------------------------------------

.. automodule:: ussd.screens.input_screen
   :members: InputScreen

3. Menu screen (type -> menu_screen)
------------------------------------

.. autoclass:: ussd.screens.menu_screen.MenuScreen


4. Quit screen (type -> quit_screen)
------------------------------------

.. autoclass:: ussd.screens.quit_screen.QuitScreen


5. Http screen (type -> http_screen)
------------------------------------

.. autoclass:: ussd.screens.http_screen.HttpScreen

6. Router screen (type -> router_screen)
----------------------------------------

.. autoclass:: ussd.screens.router_screen.RouterScreen

7. Update session screen (type -> update_session_screen)
--------------------------------------------------------

.. autoclass:: ussd.screens.update_session_screen.UpdateSessionScreen

8. Custom screen (type -> custom_screen)
----------------------------------------

.. autoclass:: ussd.screens.custom_screen.CustomScreen


***Once you have created your ussd screens run the following code to validate
them:***

   .. code-block:: text

         python manage.py validate_ussd_journey /path/to/your/ussd/file.yaml

