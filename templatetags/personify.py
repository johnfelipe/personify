from django.template.defaulttags import register
from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.utils.safestring import mark_safe
import json

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def jsonify(object):
    if isinstance(object, QuerySet):
        return serialize('json', object)
    return mark_safe(json.dumps(object))
