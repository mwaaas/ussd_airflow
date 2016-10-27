"""
This module is involved in testing Menu screen only
"""

from django.test import LiveServerTestCase


class TestingFirstCase(LiveServerTestCase):
    """
    Testing a basic functionality of menu screens

        # Test the following workflow

        A) welcome screen
        ---------------------------
         Welcome to  our grocery\n please select your order:
                1. fruits
                2. food
                3. drinks
                4. quit

        B) select fruits
        --------------------------------

            Select one of the following fruits:
                1. Ovacado
                2. Mango
                3. Passion
                4. Back

        C) select Passion
        ----------------------------------

            You have selected  Passion fruit, thanks.

        """
    pass


class TestingSecondCase(LiveServerTestCase):
    """
    Testing it supports custom inputs.


    A) First screen
    ------------------------------
        Welcome to our grocery\n please select your order:
            1. fruits
            2. food
            3. drinks
            *. quit

    B) Select b
    ------------------------------
        Thank you for using our app you have not selected anything


    """


class TestingThirdCase(LiveServerTestCase):
    """
    Testing it supports multiple language

    1. language: en

    A) First screen
    -------------------------
            Welcome to our grocery\n please select your order:
            1. fruits
            2. food
            3. drinks
            *. quit

    B) Select b
    ------------------------------
        Thank you for using our app you have not selected anything


    2. language: sw

        A) First screen
    -------------------------
            chagua order yako:
            1. matunda
            2. chakula
            3. kinyaji
            *. sitaki

    B) Select b
    ------------------------------
        Asante kwa kutumia app yet haujachagua kitu chochote


    """


class TestingItValidatesInputAndDisplaysErrorMessage(LiveServerTestCase):
    pass