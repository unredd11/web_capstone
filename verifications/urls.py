from django.urls import path
from . import api_views, views

app_name = 'verifications'

urlpatterns = [
    path(
        'api/mobile/login/',
        api_views.mobile_login,
        name='mobile_login',
    ),
    path(
        'api/mobile/projects/',
        api_views.mobile_projects,
        name='mobile_projects',
    ),
    path(
        'api/mobile/reports/submit/',
        api_views.mobile_submit_report,
        name='mobile_submit_report',
    ),

    path(
        'pending/',
        views.pending_reports,
        name='pending',
    ),
    path(
        '<int:pk>/',
        views.report_detail,
        name='report_detail',
    ),
    path(
        '<int:pk>/images/upload/',
        views.upload_inspection_image,
        name='upload_image',
    ),
    path(
        '<int:pk>/review/',
        views.review_report,
        name='review_report',
    ),
]