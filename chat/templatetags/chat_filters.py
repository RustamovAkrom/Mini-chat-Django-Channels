from django import template

register = template.Library()


@register.filter
def endswith(value, suffix):
    if not value:
        return False
    return value.lower().endswith(suffix.lower())
