"""
To have the ability to change ussd text and ussd workflow ( ussd customer journey)
without code change the best strategy would be your ussd content to be derived from a data rather than the code

Since we need to change ussd content without changing the code, we will be storing the ussd content in database
and then write logic to interpret the ussd content in the database

To make it easier to interpret ussd content from db will subdivide ussd content into the following ussd screens:

**1. Input Screen**

Its a screen requesting for input from the user,
it contains a text and input field.

Below is an example of input screen

.. image:: ../img/input_screen.png

**2. Menu Screen**

Its a screen displaying menu options for users to select

Below is an example of menu screen

.. image:: ../img/menu_screen.png

**3. List Screen**

Its a screen displaying dynamic options to display to the users to select.

The difference between List screen and menu screen is in List screen
options are not static they are dynamic, the List screen can also contain static options

.. image:: ../img/list_screen.png

The diagram above is an example of list_screen, option 1 - 4 are dynamic, are displayed to you depending on the
the input you had choose in the previous screen.
The last option is static

**4. Quit Screen**

Its a screen displaying ussd text only and no field to enter input

Its used to terminate the ussd session

Below is an example of quit screen

.. image:: ../img/quit_screen.png

**5. Router Screen**

Sometimes you want to show a certain screen to the user depending the input, phone number e.t.c
To do this we use the route screen, its responsible to route to different screens depending on
the condition given.

*This screen is not visible to the user.*

**6. HttpRequest Screen**

In some cases you may want to do a http request in between you ussd session.
This is the screen responsible for that functionality.

*This screen is not visible to the user.*

**7. Initial Screen**

This can be any of the screens above. The first ussd request goes to this screen

"""

from django.db import models


class UssdScreens(object):
    """
    All the types of ussd screen we have mentioned in the previous section
    are stored in this model.

    The model contains all the possible fields that any of the screen may require.
    The logic of how to create a specific screen will be done in the core api views

    *Reason of saving all the type of screens in one model rather than have each screen with its own model*

    Each screen (apart from the quit screen) defines a next screen to go if a user inputs something.
    that means if we have a separate model for each screen we will have multiple foreign key, for instance
    input screen can
    point to all available screens, that means we will have all the foreign fields for each screen.

    Its cleaner and better to handler if all screens are saved in one model. and the logistic of creating the screens
    tobe handlers by the core apis


    """
    pass
# Create your models here.
