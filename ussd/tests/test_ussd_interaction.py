"""
This tests creation of ussd screens using apis
"""

from django.test import LiveServerTestCase


class TestingFirstScenario(LiveServerTestCase):
    """
        test ussd by creating ussd screens by models instead of creating Handler classes

        # Test the following workflow

        A) welcome screen
        ---------------------------
         Welcome to renders:
                1. Request a loan
                2. Repay a loan
                3. About us
                4. Quit

        B) Option 1 selected
        --------------------------------

            Select one of the loans:
                1. Ksh 300
                2. Ksh 200
                3. Ksh 100
                4. Back

        C) Option 1 selected
        ----------------------------------

            Choose repayment plan
                1. KSH 350 in 7 days
                2. KSH 250 in 5 days
                3. Back

        D) Option 2 selected

            Confirm your loan application of Ksh 300 to be paid by
            interest of Ksh 330 in 7 days
                1. Confirm
                2. Back

        E) select option 1 ( to confirm the loan application)

            Thank you for your loan application . your loan will be
            processed and you will be notified



        The above workflow tests the following screens and functionality:
            - Menu screen
            - Menu and screen
            - Input screen
            - Quit screen

        example of menu lookup:
            {
            status=200,
            loan_offers=[300, 200, 100],
            repayment={300:{7:350, 5:250}, 200:{7: 300}, 100:{8:500} }
            }

        """
    pass