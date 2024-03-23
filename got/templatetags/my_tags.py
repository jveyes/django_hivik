from django import template
from got.models import Asset

register = template.Library()


@register.simple_tag(takes_context=True)
def obtener_asset_del_supervisor(context):
    request = context['request']
    user = request.user
    if user.groups.filter(name='maquinistas_serport').exists():
        try:
            return Asset.objects.get(supervisor=user)
        except Asset.DoesNotExist:
            pass
    return None
