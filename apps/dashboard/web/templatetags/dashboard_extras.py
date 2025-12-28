from django import template

register = template.Library()

@register.filter(name='list_split')
def list_split(value, arg):
    return value.split(arg)

@register.filter(name='replace')
def replace(value, arg):
    if len(arg.split(',')) != 2:
        return value
    old, new = arg.split(',')
    return value.replace(old, new)

@register.filter(name='get_attr')
def get_attr(obj, attr):
    return getattr(obj, attr, None)
