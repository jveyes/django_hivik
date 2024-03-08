from django.urls import path
from . import views

app_name = 'got'

'''
13
'''
urlpatterns = [
    # Home
    path("", views.AssignedTaskByUserListView.as_view(), name="my-tasks"),

    # Assets
    path("assets/", views.AssetsListView.as_view(), name="asset-list"), 
    path("assets/<int:pk>/", views.AssetsDetailView.as_view(), name="asset-detail"),

    # Systems
    path("sys/<int:pk>/", views.SysDetailView.as_view(), name="sys-detail"),
    path('sys/<int:pk>/update/', views.SysUpdate.as_view(), name='sys-update'), 
    path('sys/<int:pk>/delete/', views.SysDelete.as_view(), name='sys-delete'),

    # Equipos
    path('equipo/<str:pk>/', views.EquipoDetailView.as_view(), name='equipo-detail'),
    path('equipo/<str:pk>/update/', views.EquipoUpdate.as_view(), name='equipo-update'), 
    path('equipo/<str:pk>/delete/', views.EquipoDelete.as_view(), name='equipo-delete'),

    # Ots
    path("ots/", views.OtListView.as_view(), name="ot-list"), 
    path("ots/<int:pk>/", views.OtDetailView.as_view(), name="ot-detail"), 
    path("ots/create/", views.OtCreate.as_view(), name="ot-create"),
    path("ots/<int:pk>/update/", views.OtUpdate.as_view(), name="ot-update"), 
    path("ots/<int:pk>/delete/", views.OtDelete.as_view(), name="ot-delete"), 

    # Tasks
    path("task/<int:pk>/", views.TaskDetailView.as_view(), name="task-detail"), 
    path("task/<int:pk>/reschedule/", views.reschedule_task, name='reschedule-task'),
    path('task/<int:pk>/update/', views.TaskUpdate.as_view(), name='task-update'), 
    path('task/<int:pk>/delete/', views.TaskDelete.as_view(), name='task-delete'),
    path("task/<int:pk>/finish/", views.finish_task, name='finish-task'), 

    # Rutinas
    path('ruta/<str:pk>/update/', views.RutaUpdate.as_view(), name='ruta-update'), 
    path('ruta/<int:pk>/delete/', views.RutaDelete.as_view(), name='ruta-delete'),


    # Reportes
    path("report_pdf/<int:num_ot>/", views.report_pdf, name='report' ),
]