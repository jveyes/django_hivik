from django.urls import path
from . import views

app_name = 'got'

'''
13
'''
urlpatterns = [
    path("", views.AssignedTaskByUserListView.as_view(), name="my-tasks"),
    path("assets/", views.AssetsListView.as_view(), name="asset-list"), 
    path("assets/<int:pk>/", views.AssetsDetailView.as_view(), name="asset-detail"),
    path("sys/<int:pk>/", views.SysDetailView.as_view(), name="sys-detail"),
    path("ots/", views.OtListView.as_view(), name="ot-list"), 
    path("ots/<int:pk>/", views.OtDetailView.as_view(), name="ot-detail"), 
    path("task/<int:pk>/", views.TaskDetailView.as_view(), name="task-detail"), 
    path("task/<int:pk>/reschedule/", views.reschedule_task, name='reschedule-task'), 
    path("ots/create/", views.OtCreate.as_view(), name="ot-create"),
    path("ots/<int:pk>/update/", views.OtUpdate.as_view(), name="ot-update"), 
    path("ots/<int:pk>/delete/", views.OtDelete.as_view(), name="ot-delete"), 
    path('task/<int:pk>/update/', views.TaskUpdate.as_view(), name='task-update'), 
    path('task/<int:pk>/delete/', views.TaskDelete.as_view(), name='task-delete'),
    path("report_pdf/<int:num_ot>/", views.report_pdf, name='report' ),
    path("task/<int:pk>/finish/", views.finish_task, name='finish-task'), 
]