from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.admin_login, name='login'),
    path('logout/', views.admin_logout, name='logout'),
    path('register/', views.register_inspector, name='register'),
    path('inspectors/', views.inspector_list, name='inspector_list'),
]
