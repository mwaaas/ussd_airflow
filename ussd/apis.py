"""
In the previous sections you we had seen all type of ussd screen and as you had
seen all screens are saved in one model but the logistic of creating different screens
is defined by the apis.

In this section we are going to see the apis that create the different types of
screens.

"""


class InputScreen(object):
    """
    This screen contains only text and input.

    Once the user enters input, the user is directed to the next screen.
    Two things to note. we need to know next screen to navigate to and
    we also need to store the users input.

    Its created be hitting this view with the following fields:

    * text
        *type*: string

        *description*:  representing whats going to be displayed to the user.

    * next_ussd_screen
        *type*: int -> this should be an int representing the pk of an existing ussd screen

        *description*:  represents the next screen to navigate to if user enters input

    * session_key
        *type*: string

        *description*: uses input will need to be saved in the session,
        it will use this key to save the input

    * initial_screen
        *type*: boolean

        * description*: if its true, it becomes the initial screen and
        the parent of all screens, in that ussd workflow
    """
    pass


class MenuScreen(object):
    """
    This screen contains text and list of options to select from
    and input field.

    The user is supposed to select one of the options provided.
    each option should have next ussd screen to direct to.

    This is screen is created by hitting this view with the following
    fields:

    * text
        *type*: string

        *description*:  representing whats going to be displayed to the user.

    * menu_options
        *type*: dict
            contain the following content

            * menu_text
                *type*: string

                *description*: this is text going to be displayed when showing options

            * menu_input
                *type*: string or int

                *description*: this is value the user is going to select when choosing
                a option

            * menu_index
                *type*: int -> its optional if menu_input is a int

                *description*: Menu options displayed to users are
                arranged depending on this field

                *constrain*: menu_index should be unique per each screen.
                you can't have two menu options with the same menu_index

            * next_ussd_screen
                *type*: int -> this should be an int representing the pk of an
                 existing ussd screen

                *description*:  represents the next screen to navigate to if
                user enters input
    """


class ListScreen(object):
    """
    This screen contains text and list of options to select from
    and input field.

    The user is supposed to select one of the options provided.
    each option should have next ussd screen to direct to.

    The difference between menu screen and list screen is the options displayed
    in in ListScreen can be dynamic options (i.e the are generated from somewhere)

    This screen is created by hitting this view with the following fields:

    * text
        *type*: string

        *description*:  representing whats going to be displayed to the user.

    * list
        comming soon

    * session_key
        *type*: string

        *description*: uses input will need to be saved in the session,
        it will use this key.

        NB. user input will only be saved in the session with this key only if
        the use selected the generated options not menu_options

    * next_ussd_screen
        *type*: int -> this should be an int representing the pk of an
        existing ussd screen

        *description*:  represents the next screen to navigate to if user enters input

        NB. user will only be directed to this screen only if the user selected the
        generated options not menu_options

    * menu_options
        *type*: MenuOption as described in menu screen

    """


class QuitScreen(object):
    """
    Its the easiest screen to create.
    It displays text only to the user.

    Its the screen responsible for ending session.

    To create this screen you hit this view with the following fields:

    * text
        *type*: string

        *description*:  representing whats going to be displayed to the user.

    """
    pass


class RouterScreen(object):
    """
    This screen is not displayed to the users.

    The purpose of this screen is to route uses to a screen depending on
    the route_option specified.

    This screen is created by hitting this view with the following fields:

    *route_options
        comming soon
    """


class HttpRequest(object):
    """
    This screen is not displayed to the users.

    The purpose of this screen is to make a http request and save
    the response in the session

    This screen is created by hitting this view with the following fields:

    * session_key
        - This key is used to save the response in the session

    * others comming soon
    """
    pass
