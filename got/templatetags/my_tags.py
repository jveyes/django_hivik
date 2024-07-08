from django import template
from got.models import Asset, FailureReport, System
from django.contrib.auth.models import Group
from simple_history.models import HistoricalRecords


register = template.Library()


@register.simple_tag(takes_context=True)
def obtener_asset_del_supervisor(context):
    request = context['request']
    user = request.user
    target_groups = ['maq_members', 'serport_members']
    user_groups = user.groups.filter(name__in=target_groups).values_list('name', flat=True)

    if user_groups:
        try:
            return Asset.objects.get(supervisor=user)
        except Asset.DoesNotExist:
            return None
    return None
    # if user.groups.filter(name='maq_members').exists():
    #     try:
    #         return Asset.objects.get(supervisor=user)
    #     except Asset.DoesNotExist:
    #         pass
    # return False


@register.filter(name='has_group')
def has_group(user, group_name):
    group = Group.objects.get(name=group_name)
    return True if group in user.groups.all() else False


@register.filter(name='get_impact_display')
def get_impact_display(impact_code):
    return FailureReport().get_impact_display(impact_code)


@register.filter(name='can_edit_task')
def can_edit_task(user, task):
    return user == task.responsible or user.has_perm('myapp.can_modify_any_task')


@register.filter
def get_mapping_value(mapping, key):
    return mapping.get(key, None)
