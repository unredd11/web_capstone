from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from datetime import timedelta

from accounts.models import Inspector
from projects.models import Project
from verifications.models import AuditLog, BlockchainRecord, VerificationReport

def is_admin_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@user_passes_test(is_admin_user, login_url='accounts:login')
def overview(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)
    previous_month_end = month_start - timedelta(days=1)
    previous_month_start = previous_month_end.replace(day=1)
    week_start = today - timedelta(days=today.weekday())

    active_projects = Project.objects.filter(status='Ongoing')
    active_projects_this_month = active_projects.filter(created_at__date__gte=month_start).count()
    active_projects_previous_month = active_projects.filter(
        created_at__date__gte=previous_month_start,
        created_at__date__lte=previous_month_end,
    ).count()

    if active_projects_previous_month:
        active_projects_growth = round(
            ((active_projects_this_month - active_projects_previous_month) / active_projects_previous_month) * 100
        )
    elif active_projects_this_month:
        active_projects_growth = 100
    else:
        active_projects_growth = 0

    blockchain_total = BlockchainRecord.objects.count()
    blockchain_verified = BlockchainRecord.objects.filter(commit_status='Committed').count()
    blockchain_pass_rate = round((blockchain_verified / blockchain_total) * 100) if blockchain_total else 0

    total_projects = Project.objects.count()
    project_statuses = []
    for status, color in (
        ('Pending', 'warning'),
        ('Ongoing', 'primary'),
        ('Completed', 'success'),
        ('Suspended', 'danger'),
    ):
        count = Project.objects.filter(status=status).count()
        project_statuses.append({
            'label': status,
            'count': count,
            'percentage': round((count / total_projects) * 100) if total_projects else 0,
            'color': color,
        })

    verification_health = []
    for status, color in (
        ('Committed', 'success'),
        ('Pending', 'warning'),
        ('Failed', 'danger'),
    ):
        count = BlockchainRecord.objects.filter(commit_status=status).count()
        verification_health.append({
            'label': status,
            'count': count,
            'percentage': round((count / blockchain_total) * 100) if blockchain_total else 0,
            'color': color,
        })

    map_projects = [
        {
            'name': project.project_name,
            'latitude': float(project.latitude),
            'longitude': float(project.longitude),
            'status': project.status,
            'progress': float(project.progress_percentage),
        }
        for project in Project.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    ]

    context = {
        'active_page': 'overview',
        'active_projects': active_projects.count(),
        'active_projects_growth': active_projects_growth,
        'registered_inspectors': Inspector.objects.filter(is_active=True).count(),
        'inspectors_this_week': Inspector.objects.filter(date_registered__date__gte=week_start).count(),
        'pending_reports': VerificationReport.objects.filter(status='Pending').count(),
        'blockchain_verified': blockchain_verified,
        'blockchain_pass_rate': blockchain_pass_rate,
        'total_projects': total_projects,
        'project_statuses': project_statuses,
        'blockchain_total': blockchain_total,
        'verification_health': verification_health,
        'reports_requiring_review': VerificationReport.objects.filter(status='Pending').select_related(
            'project', 'inspector__user'
        )[:5],
        'map_projects': map_projects,
        'recent_activity': AuditLog.objects.select_related('user')[:8],
    }
    return render(request, 'dashboard/Overview.html', context)
