from ussd.core import register_filter


@register_filter
def format_number(value):
    """
    formats the number into the commas and 2 decimal places
    :param value:
    :return:
    """
    val = '0' if value == '' else value
    return "{:,.2f}".format(int(val))


@register_filter
def format_currency(value, currency):
    """
    formats the number into the commas and 2 decimal places
    :param value:
    :param currency:
    :return:
    """
    val = '0' if value == '' else value
    curr = 'KSH' if currency == '' else currency

    return "{currency} {value:,.2f}".format(currency=curr, value=int(val))
