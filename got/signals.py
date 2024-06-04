from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import HistoryHour
from django.db.models import Avg


@receiver(post_save, sender=HistoryHour)
@receiver(post_delete, sender=HistoryHour)
def update_equipo_horometro(sender, instance, **kwargs):
    # Obtener el equipo relacionado con la instancia de HistoryHour
    equipo = instance.component

    # Calcular la suma de las horas de todos los HistoryHour relacionados
    # horas_totales =
    # HistoryHour.objects.filter(component=equipo)
    # .aggregate(total_horas=Sum('hour'))['total_horas']
    # promedio_horas = HistoryHour.objects.filter(component=equipo).aggregate(
    #     promedio_horas=Avg('hour'))['promedio_horas']

    ultimos_30_registros = HistoryHour.objects.filter(
        component=equipo).order_by('-report_date')[:10]

    # Calcula el promedio de horas de los últimos 30 registros.
    promedio_horas = ultimos_30_registros.aggregate(
        promedio_horas=Avg('hour'))['promedio_horas']

    equipo.prom_hours = promedio_horas or 0

    # Actualizar el valor de horometro del equipo con la suma calculada
    equipo.horometro = equipo.calculate_horometro()
    equipo.save()
