from django import template

from homodaba import settings
from homodaba.version import VERSION

register = template.Library()

@register.simple_tag
def get_movie_list_per_page():
    return settings.ADMIN_MOVIE_LIST_PER_PAGE

@register.simple_tag
def homodaba_version():
    return VERSION