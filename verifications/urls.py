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
        'api/mobile/reports/',
        api_views.mobile_report_history,
        name='mobile_report_history',
    ),
    path(
        'api/mobile/reports/<int:report_id>/',
        api_views.mobile_report_detail,
        name='mobile_report_detail',
    ),

    path(
        'pending/',
        views.pending_reports,
        name='pending',
    ),
    path(
        'history/',
        views.report_history,
        name='report_history',
    ),
    path(
        'history/export/',
        views.export_reports_csv,
        name='export_reports_csv',
    ),
    path(
        'audit/',
        views.audit_log_list,
        name='audit_log_list',
    ),
    path(
        'audit/export/',
        views.export_audit_logs_csv,
        name='export_audit_logs_csv',
    ),
    path(
        '<int:pk>/',
        views.report_detail,
        name='report_detail',
    ),
    path(
        '<int:pk>/review/',
        views.review_report,
        name='review_report',
    ),
]
