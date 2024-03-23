from django import template

register = template.Library()


@register.simple_tag
def mi_etiqueta_de_plantilla():
    # Lógica de la etiqueta
    return "Hola, Mundo!"
