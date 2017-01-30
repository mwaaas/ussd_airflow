from ussd.core import register_filter
from datetime import datetime
import calendar


@register_filter
def day(date_time):
    return date_time.day


@register_filter
def month(date_time):
    return date_time.month


@register_filter
def year(date_time):
    return date_time.year


@register_filter
def month_name(no_month):
    if isinstance(no_month, datetime):
        no_month = no_month.month
    return calendar.month_name[no_month]


@register_filter
def day_name(date_time):
    return date_time.strftime("%A")


@register_filter
def add_month(month, months_to_add):
    next_month = month + months_to_add

    if next_month > 12:
        next_month -= 12
    elif next_month < 1:
        next_month += 12
    return next_month


@register_filter
def strip(strftime, strptime):
    return datetime.strptime(
        strftime,
        strptime
    )
