"""
URL configuration for web_capstone project.
"""
from django.contrib import admin
from django.urls import path, include
from accounts import views as account_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', account_views.admin_login, name='direct_login'),
    path('logout/', account_views.admin_logout, name='direct_logout'),
    path('accounts/', include('accounts.urls')),
    path('', include('dashboard.urls')),
    path('projects/', include('projects.urls')),
    path('verifications/', include('verifications.urls')),
]
