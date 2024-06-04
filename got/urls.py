from django.urls import path
from . import views

app_name = 'got'

urlpatterns = [
    # ---------------------------- Main views ------------------------------ #
    path("", views.AssignedTaskByUserListView.as_view(), name="my-tasks"),

    # ---------------------------- Assets view ----------------------------- #
    path("asset/", views.AssetsListView.as_view(), name="asset-list"),
    path("asset/<str:pk>/", views.AssetDetailView.as_view(), name="asset-detail"),
    path("asset/<str:pk>/schedule/", views.schedule, name="schedule"),


    # ---------------------------- Systems view ----------------------------- #
    path("sys/<int:pk>/", views.SysDetailView.as_view(), name="sys-detail"),
    path('sys/<int:pk>/<str:view_type>/', views.SysDetailView.as_view(), name='sys-detail-view'),
    path('system/<int:pk>/update/', views.SysUpdate.as_view(), name='sys-update'),
    path('sys/<int:pk>/delete/', views.SysDelete.as_view(), name='sys-delete'),

    # ---------------------------- Equipos view ----------------------------- #
    path('equipo/<str:pk>/update/', views.EquipoUpdate.as_view(), name='equipo-update'),
    path('equipo/<str:pk>/delete/', views.EquipoDelete.as_view(), name='equipo-delete'),
    path('system/<int:pk>/new_equipo/', views.EquipoCreateView.as_view(), name='equipo-create'),
    # ---------------------------- OTs view --------------------------------- #
    path("ots/", views.OtListView.as_view(), name="ot-list"),
    path("ots/<int:pk>/", views.OtDetailView.as_view(), name="ot-detail"),
    path("ots/create/<str:pk>/", views.OtCreate.as_view(), name="ot-create"),
    path("ots/<int:pk>/update/", views.OtUpdate.as_view(), name="ot-update"),
    path("ots/<int:pk>/delete/", views.OtDelete.as_view(), name="ot-delete"),

    # ---------------------------- Taks view ----------------------------- #
    path("task/<int:pk>/", views.TaskDetailView.as_view(), name="task-detail"),
    path('task/<str:pk>/create/', views.TaskCreate.as_view(), name='task-create'),
    path('task/<int:pk>/update/', views.TaskUpdate.as_view(), name='task-update'),
    path('task/<int:pk>/delete/', views.TaskDelete.as_view(), name='task-delete'),

    path("task/<int:pk>/reschedule/", views.Reschedule_task.as_view(), name='reschedule-task'),
    path('task/<int:pk>/finish/', views.Finish_task.as_view(), name='finish-task'),
    path('task/<int:pk>/finish-ot/', views.Finish_task_ot.as_view(), name='finish-task-ot'),

    path('task-rut/<int:pk>/update/', views.TaskUpdaterut.as_view(), name='update-task'),
    path('delete_task/<int:pk>/', views.TaskDeleterut.as_view(), name='delete-task'),

    # ---------------------------- Rutinas view ----------------------------- #
    path('rutas/', views.RutaListView, name="ruta-list"),
    path('ruta/<str:pk>/create/', views.RutaCreate.as_view(), name='ruta-create'),
    path('ruta/<str:pk>/update/', views.RutaUpdate.as_view(), name='ruta-update'),
    path('ruta/<str:pk>/delete/',views.RutaDelete.as_view(), name='ruta-delete'),
    path('ruta/<int:ruta_id>/crear_ot/',views.crear_ot_desde_ruta,name='crear_ot_desde_ruta'),

    # ---------------------------- Reportes --------------------------------- #
    path("report_pdf/<int:num_ot>/", views.report_pdf, name='report'),
    path("dash/", views.indicadores, name='dashboard'),

    # ---------------------------- History hour view ------------------------ #
    path("reportehoras/<str:component>/", views.reporthours, name='horas'),
    path("reportehorasasset/<str:asset_id>/",views.reportHoursAsset,name='horas-asset'),

    # ---------------------------- Reportes de falla view ------------------- #
    # LISTADO REPORTES DE FALLA
    path("report-failure/", views.FailureListView.as_view(), name="failure-report-list"),
    # DETALLE REPORTES DE FALLA
    path("report-failure/<str:pk>/", views.FailureDetailView.as_view(), name="failure-report-detail"),
    # FORMULARIO CREACION DE REPORTE DE FALLA
    path('report-failure/<str:asset_id>/create/', views.FailureReportForm.as_view(), name='failure-report-create'),
    # FORMULARIO ACTUALIZACION DE REPORTE DE FALLA
    path('report-failure/<int:pk>/update/', views.FailureReportUpdate.as_view(), name='failure-report-update'),
    path('report-failure/<int:fail_id>/crear_ot/', views.crear_ot_failure_report, name='failure-report-crear-ot'),
    path('historial-cambios/', views.HistorialCambiosView.as_view(), name='historial-cambios'),
    path('bitacora/<int:asset_id>/', views.BitacoraView.as_view(), name='bitacora'),

    # ---------------------------- Operaciones ----------------------- #
    path("operations/", views.OperationListView, name="operation-list"),
    path('operation/<int:pk>/update/', views.OperationUpdate.as_view(), name='operation-update'),
    path("operation/<int:pk>/delete/", views.OperationDelete.as_view(), name="operation-delete"),

    path('assets/<str:asset_id>/generate-pdf/', views.generate_asset_pdf, name='generate_asset_pdf'),


    path('add-location/', views.add_location, name='add-location'),
    path('location/<int:pk>/', views.view_location, name='view-location'),
]
