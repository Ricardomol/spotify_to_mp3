from django import template
import json
register = template.Library()
register.filter('json', json.dumps)