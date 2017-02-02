from ussd.core import register_filter
from jinja2.runtime import Undefined


@register_filter
def update(dict_a, dict_b):
    if isinstance(dict_a, Undefined) or dict_a is None:
        dict_a = {}
    dict_a.update(dict_b)
    return dict_a