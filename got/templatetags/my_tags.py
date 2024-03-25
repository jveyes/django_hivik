from django import template
from got.models import Asset
from django.contrib.auth.models import Group

register = template.Library()


@register.simple_tag(takes_context=True)
def obtener_asset_del_supervisor(context):
    request = context['request']
    user = request.user
    if user.groups.filter(name='maq_members').exists():
        try:
            return Asset.objects.get(supervisor=user)
        except Asset.DoesNotExist:
            pass
    return False


@register.filter(name='has_group')
def has_group(user, group_name):
    group = Group.objects.get(name=group_name)
    return True if group in user.groups.all() else False
