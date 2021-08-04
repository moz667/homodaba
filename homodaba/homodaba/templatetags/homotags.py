from django import template

from homodaba import settings
from homodaba.version import VERSION

register = template.Library()

@register.filter
def set_css_class(widget, class_value):
    widget.field.widget.attrs["class"] = class_value
    return widget

@register.filter
def placeholder(widget, placeholder_value):
    widget.field.widget.attrs["placeholder"] = placeholder_value
    return widget

@register.simple_tag
def some_errors(field_list=[]):
    for field in field_list:
        if len(field.errors) > 0:
            return True
    return False

@register.simple_tag
def get_movie_list_per_page():
    return settings.ADMIN_MOVIE_LIST_PER_PAGE

@register.simple_tag
def homodaba_version():
    return VERSION

