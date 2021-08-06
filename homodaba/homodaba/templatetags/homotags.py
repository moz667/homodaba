from django import template

from homodaba import settings
from homodaba.version import VERSION

from data.models import get_or_create_user_tag

register = template.Library()

@register.simple_tag
def search_filters_as_url_args(filters, exlude_filter):
    url_args = []
    if filters:
        # Director es un poco tricky porque lleva el imdb_id
        if filters['director'] and filters['director_query'] and exlude_filter != 'director':
            url_args.append("&director=%s" % filters['director_query'])
        
        for key in ['tag', 'genre', 'cr_system', 'user_tag']:
            if filters[key] and exlude_filter != key:
                url_args.append("&%s=%s" % (key, filters[key]))

    return ''.join(url_args)

@register.simple_tag
def movie_contain_user_tag(movie, user, tag_type):
    tag = get_or_create_user_tag(user, tag_type)

    for t in movie.user_tags.all():
        if t.name == tag.name:
            return True

    return False

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

