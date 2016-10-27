"""
This modules tests input screen
"""

from django.test import LiveServerTestCase


class TestingInputScreenHappyCase(LiveServerTestCase):
    """
    Test input is entered and stored in the session

    A) Input screen
    ---------------------

            Enter your name:

    B) Enter "Wahu"
    -------------------------
            Your name is Wahu.

    """


class TestingTranslation(LiveServerTestCase):
    """
    Testing ussd text changes depending with the language

    1. language : en
    ------------------------
    ------------------------

    A) Input screen
    -------------------------
        Enter your age:

    B) Enter 22
    -------------------------
        Your age is 22.

    2. language : sw
    ------------------------
    ------------------------

    A) Input screen
    -------------------------
        Weka amuri yako:

    B) Enter 22
    -------------------------

        Uko na miaka 22

    """


class TestingInputValidation(LiveServerTestCase):
    """
    Testing input is validation raises an error.


    A) Input Screen
    -----------------------------------

        Enter your birth date. eg. dd/mm/yy

    B) Enter invalid date 12/30/1920
    -----------------------------------------

        You have entered invalid date, please try again

    C) Enter a valid one date   30/12/1920
    -------------------------------------------

        Your birth date is 1920
    """