from ussd.core import register_filter
from jinja2.runtime import Undefined


@register_filter
def append(list_a, obj):
    if isinstance(list_a, Undefined) or list_a is None or \
            (len(list_a) == 1 and isinstance(list_a[0], Undefined)):
        list_a = []
    list_a.append(obj)
    return list_a
