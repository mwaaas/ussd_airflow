from ussd.tests import UssdTestCase
from datetime import datetime
import calendar
from freezegun import freeze_time


@freeze_time(datetime.now())
class TestScreensUsingFilters(UssdTestCase.BaseUssdTestCase):

    validate_ussd = False

    def get_ussd_client(self):
        return self.ussd_client(
            generate_customer_journey=False,
            extra_payload={
                "customer_journey_conf": "sample_using_date_filters.yml"
            }
        )

    def test_using_filters(self):
        now = datetime.now()
        client = self.get_ussd_client()
        # dial in
        response = client.send('1')

        self.assertEqual(
            "The date today is {now}. We are on the {now_month} th month "
            "and we are on year {now_year}. Month in words is "
            "{now_month_name}. And day in words "
            "{now_day_name}. And next month {three_months}\n"
            "Testing striping date. After striping this "
            "date 2017-01-20 we should get the year, month and day. "
            "The day is {strip_day_name}\n".format(
                now=now,
                now_month=now.month,
                now_year=now.year,
                now_month_name=calendar.month_name[now.month],
                now_day_name=now.strftime("%A"),
                three_months=calendar.month_name[now.month + 3],
                strip_day_name=20
            ),
            response
        )
