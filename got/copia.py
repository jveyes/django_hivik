from django.db import transaction
from django.shortcuts import get_object_or_404
from got.models import System, Ruta, Task  # Asegúrate de cambiar 'yourapp' al nombre de tu aplicación

def copiar_rutas_de_sistema(system_id):
    # Obtener el sistema original
    sistema_origen = get_object_or_404(System, id=system_id)
    asset = sistema_origen.asset
    
    # Encontrar todos los sistemas del mismo asset, excluyendo el sistema original
    sistemas_destino = System.objects.filter(asset=asset).exclude(id=system_id)
    
    with transaction.atomic():
        for sistema in sistemas_destino:
            # Copiar todas las rutas asociadas al sistema original
            for ruta in sistema_origen.rutas.all():
                ruta_nueva = Ruta.objects.create(
                    name=ruta.name,
                    control=ruta.control,
                    frecuency=ruta.frecuency,
                    intervention_date=ruta.intervention_date,
                    suministros=ruta.suministros,
                    astillero=ruta.astillero,
                    system=sistema,
                    equipo=ruta.equipo.code,
                    dependencia=ruta.dependencia,
                )
                
                # Copiar todas las tareas asociadas a cada ruta
                for tarea in ruta.task_set.all():
                    Task.objects.create(
                        ot=tarea.ot,
                        ruta=ruta_nueva,
                        responsible=tarea.responsible,
                        description=tarea.description,
                        procedimiento=tarea.procedimiento,
                        hse=tarea.hse,
                        news=tarea.news,
                        evidence=tarea.evidence,
                        start_date=tarea.start_date,
                        men_time=tarea.men_time,
                        finished=tarea.finished
                    )
    print(f"Rutas y tareas copiadas exitosamente a otros sistemas en el mismo activo {asset.name}.")
