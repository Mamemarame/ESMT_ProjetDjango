from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('project/create/', views.create_project, name='create_project'),
    path('project/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    path('project/<int:project_id>/create-task/', views.create_task, name='create_task'),
    path('task/<int:task_id>/update/', views.update_task_status, name='update_task_status'),
    path('notifications/read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('project/<int:project_id>/edit/', views.edit_project, name='edit_project'),
    path('task/<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('task/<int:task_id>/delete/', views.delete_task, name='delete_task'),
]