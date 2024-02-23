from django.contrib import admin
from .models import Asset, System, Ot, Task, Component, Ruta

# Register models.
class OtAdmin(admin.ModelAdmin):
    list_display = (
        'num_ot',
        'creation_date',
        'description',
        'system',
        'super'
        )

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'ot',
        'responsible',
        'description',
        'start_date',
        'is_overdue'
    )

    list_filter = (
        'start_date', 'finished'
    )

    search_fields = (
        'ot_description', 'description', 'responsible_username'
    )

    date_hierarchy = 'start_date'

    fieldsets = (
        (None, {
            'fields': (
                'ot',
                'responsible',
                'description',
                'news',
                'evidence',
                'start_date'
            )
        }),
        ('Timing', {
            'fields': ('men_time', 'finished')
        }),
    )

admin.site.register(Asset)
admin.site.register(Ruta)
admin.site.register(Component)
admin.site.register(System)
admin.site.register(Ot, OtAdmin)
