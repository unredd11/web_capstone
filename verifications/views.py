from django.shortcuts import render
from .models import VerificationReport

def pending_reports(request):
    reports = VerificationReport.objects.filter(status='Pending').select_related('project', 'inspector__user')
    return render(request, 'projects/pending_reports.html', {'reports': reports, 'active_page': 'pending_reports'})
