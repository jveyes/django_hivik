from django import template
from got.models import Asset, FailureReport, System
from django.contrib.auth.models import Group
from simple_history.models import HistoricalRecords


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


@register.filter(name='get_impact_display')
def get_impact_display(impact_code):
    return FailureReport().get_impact_display(impact_code)


@register.filter
def is_instance_of(item, cls_name):
    try:
        cls = eval(cls_name)
        return isinstance(item, cls)
    except NameError:
        # Handle the case where cls_name is not defined
        if cls_name == 'HistoricalSystem':
            return isinstance(item, type(System.history.first()))
        return False
