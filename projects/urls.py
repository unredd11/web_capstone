from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('add/', views.project_add, name='project_add'),
    path('<int:pk>/', views.project_detail, name='project_detail'),
    path('<int:pk>/edit/', views.project_edit, name='project_edit'),
    path(
        '<int:pk>/documents/<int:document_pk>/delete/',
        views.project_document_delete,
        name='project_document_delete',
    ),
    path('<int:pk>/assign/', views.assign_inspector, name='assign_inspector'),
]
