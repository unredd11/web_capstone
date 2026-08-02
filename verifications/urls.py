from django.urls import path
from . import views

app_name = 'verifications'

urlpatterns = [
    path('pending/', views.pending_reports, name='pending'),
]
