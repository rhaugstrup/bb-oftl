
from google.appengine.ext.webapp import template

register = template.create_template_register()

@register.filter
def get_range(value):
  return range(value)

@register.filter 
def divide(value, arg):
    return int(value) / int(arg) 

@register.filter 
def multiply(value, arg):
    return int(value) * int(arg) 

@register.filter 
def power(value, arg):
    return int(arg) ** int(value)


