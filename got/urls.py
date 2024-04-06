from django.urls import path
from . import views

app_name = 'got'

'''
13
'''
urlpatterns = [
    # ---------------------------- Main views ------------------------------ #
    path(
        "",
        views.AssignedTaskByUserListView.as_view(),
        name="my-tasks"
    ),

    # ---------------------------- Assets view ----------------------------- #
    path(  # LIST VIEW
        "assets/",
        views.AssetsListView.as_view(),
        name="asset-list"
    ),
    path(  # DETAIL VIEW
        "assets/<int:pk>/",
        views.AssetDetailView.as_view(),
        name="asset-detail"
    ),

    # ---------------------------- Systems view ----------------------------- #
    path("sys/<int:pk>/", views.SysDetailView.as_view(), name="sys-detail"),
    path('sys/<int:pk>/update/', views.SysUpdate.as_view(), name='sys-update'),
    path('sys/<int:pk>/delete/', views.SysDelete.as_view(), name='sys-delete'),

    # ---------------------------- Equipos view ----------------------------- #
    path(  # UPDATE VIEW
        'equipo/<str:pk>/update/',
        views.EquipoUpdate.as_view(),
        name='equipo-update'
    ),
    path(  # DELETE VIEW
        'equipo/<str:pk>/delete/',
        views.EquipoDelete.as_view(),
        name='equipo-delete'
    ),

    # ---------------------------- OTs view --------------------------------- #
    path("ots/", views.OtListView.as_view(), name="ot-list"),
    path("ots/<int:pk>/", views.OtDetailView.as_view(), name="ot-detail"),
    path("ots/create/<int:pk>/", views.OtCreate.as_view(), name="ot-create"),
    path("ots/<int:pk>/update/", views.OtUpdate.as_view(), name="ot-update"),
    path("ots/<int:pk>/delete/", views.OtDelete.as_view(), name="ot-delete"),

    # ---------------------------- Taks view ----------------------------- #
    path(  # DETALLE DE ACTIVIDADES
        "task/<int:pk>/",
        views.TaskDetailView.as_view(),
        name="task-detail"
    ),
    path(
        "task/<int:pk>/reschedule/",
        views.reschedule_task,
        name='reschedule-task'),
    path('task/<str:pk>/create/',
         views.TaskCreate.as_view(),
         name='task-create'),
    path(
        'task/<int:pk>/update/',
        views.TaskUpdate.as_view(),
        name='task-update'),
    path(
        'task/<int:pk>/delete/',
        views.TaskDelete.as_view(),
        name='task-delete'),
    path('task/<int:pk>/finish/', views.finish_task, name='finish-task'),

    path(
        'task-rut/<int:pk>/update/',
        views.TaskUpdaterut.as_view(),
        name='update-task'),
    path(
        'delete_task/<int:pk>/',
        views.TaskDeleterut.as_view(),
        name='delete-task'),

    # ---------------------------- Rutinas view ----------------------------- #
    path('rutas/', views.RutaListView.as_view(), name="ruta-list"),
    path(
        'ruta/<str:pk>/create/',
        views.RutaCreate.as_view(),
        name='ruta-create'
        ),
    path(
        'ruta/<str:pk>/update/',
        views.RutaUpdate.as_view(),
        name='ruta-update'
        ),
    path(
        'ruta/<str:pk>/update/',
        views.RutaUpdateOT.as_view(),
        name='ruta-update-ot'
        ),
    path(
        'ruta/<str:pk>/delete/',
        views.RutaDelete.as_view(), name='ruta-delete'
        ),
    path(
        'ruta/<int:ruta_id>/crear_ot/',
        views.crear_ot_desde_ruta,
        name='crear_ot_desde_ruta'
    ),

    # ---------------------------- Reportes --------------------------------- #
    path("report_pdf/<int:num_ot>/", views.report_pdf, name='report'),
    path("dashboard/", views.indicadores, name='dashboard'),

    # ---------------------------- History hour view ------------------------ #
    path("reportehoras/<str:component>/", views.reporthours, name='horas'),
    path(
        "reportehorasasset/<int:asset_id>/",
        views.reportHoursAsset,
        name='horas-asset'
        ),

    # ---------------------------- Reportes de falla view ------------------- #
    # LISTADO REPORTES DE FALLA
    path(
        "report-failure/",
        views.FailureListView.as_view(),
        name="failure-report-list"
    ),
    # DETALLE REPORTES DE FALLA
    path(
        "report-failure/<int:pk>/",
        views.FailureDetailView.as_view(),
        name="failure-report-detail"
    ),
    # FORMULARIO CREACION DE REPORTE DE FALLA
    path(
        'report-failure/<int:asset_id>/create/',
        views.FailureReportForm.as_view(),
        name='failure-report-create'
    ),
    # FORMULARIO ACTUALIZACION DE REPORTE DE FALLA
    path(
        'report-failure/<int:pk>/update/',
        views.FailureReportUpdate.as_view(),
        name='failure-report-update'
    ),
    path(
        'report-failure/<int:fail_id>/crear_ot/',
        views.crear_ot_failure_report,
        name='failure-report-crear-ot'
    ),
]
