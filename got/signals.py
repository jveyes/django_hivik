from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import HistoryHour, Equipo
from django.db.models import Sum

@receiver(post_save, sender=HistoryHour)
@receiver(post_delete, sender=HistoryHour)
def update_equipo_horometro(sender, instance, **kwargs):
    # Obtener el equipo relacionado con la instancia de HistoryHour
    equipo = instance.component
    
    # Calcular la suma de las horas de todos los HistoryHour relacionados con el equipo
    horas_totales = HistoryHour.objects.filter(component=equipo).aggregate(total_horas=Sum('hour'))['total_horas']
    
    # Actualizar el valor de horometro del equipo con la suma calculada
    equipo.horometro = equipo.calculate_horometro() #horas_totales or 0  # Si no hay horas registradas, establece horometro en 0
    equipo.save()
