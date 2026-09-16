from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date

from accounts.models import Inspector

from projects.models import Project

from .audit import record_audit_event
from .forms import InspectionImageForm, ReportReviewForm
from .models import (
    AuditLog,
    BlockchainRecord,
    VerificationReport,
)

from .services import (
    calculate_distance_meters,
    calculate_phash,
    calculate_sha256,
)

def is_admin_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@user_passes_test(is_admin_user, login_url='accounts:login')
def pending_reports(request):
    reports = VerificationReport.objects.filter(status='Pending').select_related(
        'project', 'inspector__user'
    ).prefetch_related('images')
    return render(
        request,
        'projects/pending_reports.html',
        {'reports': reports, 'active_page': 'pending_reports'},
    )

@user_passes_test(
    is_admin_user,
    login_url='accounts:login',
)
def report_history(request):
    reports = VerificationReport.objects.select_related(
        'project',
        'inspector__user',
        'reviewed_by',
    ).prefetch_related(
        'images',
    )

    search_query = request.GET.get('q', '').strip()
    selected_status = request.GET.get('status', '').strip()
    selected_project = request.GET.get('project', '').strip()
    selected_inspector = request.GET.get(
        'inspector',
        '',
    ).strip()
    date_from_value = request.GET.get(
        'date_from',
        '',
    ).strip()
    date_to_value = request.GET.get(
        'date_to',
        '',
    ).strip()

    if search_query:
        reports = reports.filter(
            Q(
                project__project_name__icontains=(
                    search_query
                )
            )
            | Q(
                inspector__employee_id__icontains=(
                    search_query
                )
            )
            | Q(
                inspector__user__first_name__icontains=(
                    search_query
                )
            )
            | Q(
                inspector__user__last_name__icontains=(
                    search_query
                )
            )
            | Q(
                accomplishment_description__icontains=(
                    search_query
                )
            )
        )

    if selected_status in {
        'Pending',
        'Approved',
        'Rejected',
    }:
        reports = reports.filter(
            status=selected_status
        )

    if selected_project.isdigit():
        reports = reports.filter(
            project_id=int(selected_project)
        )

    if selected_inspector.isdigit():
        reports = reports.filter(
            inspector_id=int(selected_inspector)
        )

    date_from = parse_date(date_from_value)
    date_to = parse_date(date_to_value)

    if date_from:
        reports = reports.filter(
            submitted_at__date__gte=date_from
        )

    if date_to:
        reports = reports.filter(
            submitted_at__date__lte=date_to
        )

    paginator = Paginator(reports, 10)
    page_obj = paginator.get_page(
        request.GET.get('page')
    )

    return render(
        request,
        'verifications/report_history.html',
        {
            'reports': page_obj,
            'page_obj': page_obj,
            'report_count': paginator.count,
            'projects': Project.objects.order_by(
                'project_name'
            ),
            'inspectors': Inspector.objects.select_related(
                'user'
            ).order_by(
                'user__first_name',
                'user__last_name',
            ),
            'search_query': search_query,
            'selected_status': selected_status,
            'selected_project': selected_project,
            'selected_inspector': selected_inspector,
            'date_from': date_from_value,
            'date_to': date_to_value,
            'active_page': 'report_history',
        },
    )

@user_passes_test(
    is_admin_user,
    login_url='accounts:login',
)
def audit_log_list(request):
    audit_logs = AuditLog.objects.select_related(
        'user'
    )

    search_query = request.GET.get('q', '').strip()
    selected_action = request.GET.get(
        'action',
        '',
    ).strip()
    date_from_value = request.GET.get(
        'date_from',
        '',
    ).strip()
    date_to_value = request.GET.get(
        'date_to',
        '',
    ).strip()

    if search_query:
        audit_logs = audit_logs.filter(
            Q(
                user__username__icontains=search_query
            )
            | Q(
                user__first_name__icontains=(
                    search_query
                )
            )
            | Q(
                user__last_name__icontains=(
                    search_query
                )
            )
            | Q(
                action_type__icontains=search_query
            )
            | Q(
                target_entity__icontains=search_query
            )
            | Q(
                device_info__icontains=search_query
            )
        )

    if selected_action:
        audit_logs = audit_logs.filter(
            action_type=selected_action
        )

    date_from = parse_date(date_from_value)
    date_to = parse_date(date_to_value)

    if date_from:
        audit_logs = audit_logs.filter(
            timestamp__date__gte=date_from
        )

    if date_to:
        audit_logs = audit_logs.filter(
            timestamp__date__lte=date_to
        )

    actions = AuditLog.objects.order_by().values_list(
        'action_type',
        flat=True,
    ).distinct()

    paginator = Paginator(audit_logs, 20)
    page_obj = paginator.get_page(
        request.GET.get('page')
    )

    return render(
        request,
        'verifications/audit_log_list.html',
        {
            'audit_logs': page_obj,
            'page_obj': page_obj,
            'audit_count': paginator.count,
            'actions': actions,
            'search_query': search_query,
            'selected_action': selected_action,
            'date_from': date_from_value,
            'date_to': date_to_value,
            'active_page': 'audit_logs',
        },
    )


@user_passes_test(is_admin_user, login_url='accounts:login')
def report_detail(request, pk):
    report = get_object_or_404(
        VerificationReport.objects.select_related(
            'project',
            'inspector__user',
            'reviewed_by',
            'resubmission_of',
        ).prefetch_related(
            'images__blockchain_record',
            'resubmissions',
        ),
        pk=pk,
    )

    return render(
        request,
        'verifications/report_detail.html',
        {
            'report': report,
            'image_form': InspectionImageForm(),
            'active_page': 'pending_reports',
        },
    )

@user_passes_test(is_admin_user, login_url='accounts:login')
@transaction.atomic
def upload_inspection_image(request, pk):
    report = get_object_or_404(
        VerificationReport.objects.select_for_update().select_related('project'),
        pk=pk,
    )

    if request.method != 'POST':
        return redirect('verifications:report_detail', pk=report.pk)

    if report.status != 'Pending':
        messages.error(request, 'Images cannot be added after a report has been reviewed.')
        return redirect('verifications:report_detail', pk=report.pk)

    if report.project.latitude is None or report.project.longitude is None:
        messages.error(request, 'Add project coordinates before uploading inspection evidence.')
        return redirect('verifications:report_detail', pk=report.pk)

    form = InspectionImageForm(request.POST, request.FILES)
    if not form.is_valid():
        error_message = ' '.join(
            str(error)
            for errors in form.errors.values()
            for error in errors
        )
        messages.error(request, error_message or 'Please correct the image information.')
        return redirect('verifications:report_detail', pk=report.pk)

    uploaded_file = form.cleaned_data['image_file']
    try:
        sha256_hash = calculate_sha256(uploaded_file)
        perceptual_hash = calculate_phash(uploaded_file)
    except (OSError, ValueError):
        messages.error(request, 'The uploaded image could not be processed.')
        return redirect('verifications:report_detail', pk=report.pk)

    image = form.save(commit=False)
    image.report = report
    image.sha256_hash = sha256_hash
    image.perceptual_hash = perceptual_hash
    image.file_size = uploaded_file.size
    image.mime_type = getattr(uploaded_file, 'content_type', '')

    distance = calculate_distance_meters(
        report.project.latitude,
        report.project.longitude,
        image.latitude,
        image.longitude,
    )
    image.geofence_distance = round(distance, 2)
    image.geofence_status = (
        'Inside'
        if distance <= float(report.project.geofence_radius)
        else 'Outside'
    )

    image.save()

    blockchain_record, blockchain_created = (
        BlockchainRecord.objects.get_or_create(
            inspection_image=image,
            defaults={
                'chaincode_name': 'evidence',
                'commit_status': 'Pending',
                'metadata_json': {
                    'report_id': report.pk,
                    'image_id': image.pk,
                    'project_id': report.project_id,
                    'inspector_id': report.inspector_id,
                    'sha256_hash': image.sha256_hash,
                    'perceptual_hash': image.perceptual_hash,
                    'latitude': str(image.latitude),
                    'longitude': str(image.longitude),
                    'captured_at': image.captured_at.isoformat(),
                    'geofence_distance': (
                        str(image.geofence_distance)
                        if image.geofence_distance is not None
                        else None
                    ),
                    'geofence_status': image.geofence_status,
                },
            },
        )
    )

    if blockchain_created:
        record_audit_event(
            request=request,
            action_type='prepare_blockchain_record',
            target_entity='BlockchainRecord',
            target_id=blockchain_record.pk,
        )

    report.image_hash = image.sha256_hash
    report.latitude = image.latitude
    report.longitude = image.longitude
    report.save(update_fields=['image_hash', 'latitude', 'longitude'])

    AuditLog.objects.create(
        user=request.user,
        action_type='upload_image',
        target_entity='InspectionImage',
        target_id=image.pk,
        ip_address=request.META.get('REMOTE_ADDR'),
        device_info=request.META.get('HTTP_USER_AGENT', '')[:255],
    )

    messages.success(
        request,
        f'Image uploaded successfully. Geofence result: {image.geofence_status}.',
    )
    return redirect('verifications:report_detail', pk=report.pk)

@user_passes_test(is_admin_user, login_url='accounts:login')
@transaction.atomic
def review_report(request, pk):
    report = get_object_or_404(
        VerificationReport.objects.select_for_update(),
        pk=pk,
    )

    if request.method != 'POST':
        return redirect('verifications:report_detail', pk=report.pk)

    if report.status != 'Pending':
        messages.warning(request, 'This report has already been reviewed.')
        return redirect('verifications:report_detail', pk=report.pk)

    form = ReportReviewForm(request.POST)
    if not form.is_valid():
        error_message = ' '.join(
            str(error)
            for errors in form.errors.values()
            for error in errors
        )
        messages.error(request, error_message or 'Please correct the review information.')
        return redirect('verifications:report_detail', pk=report.pk)

    if form.cleaned_data['decision'] == 'Approved' and not report.images.exists():
        messages.error(request, 'A report cannot be approved without an inspection image.')
        return redirect('verifications:report_detail', pk=report.pk)

    if (
        form.cleaned_data['decision'] == 'Approved'
        and report.images.exclude(geofence_status='Inside').exists()
    ):
        messages.error(request, 'A report cannot be approved unless all images are inside the geofence.')
        return redirect('verifications:report_detail', pk=report.pk)

    report.status = form.cleaned_data['decision']
    report.review_notes = form.cleaned_data['review_notes']
    report.reviewed_by = request.user
    report.reviewed_at = timezone.now()

    report.save(
        update_fields=['status', 'review_notes', 'reviewed_by', 'reviewed_at']
    )

    if report.status == 'Approved':
        project = Project.objects.select_for_update().get(
            pk=report.project_id
        )

        if (
            report.progress_percentage
            > project.progress_percentage
        ):
            project.progress_percentage = (
                report.progress_percentage
            )

            if project.progress_percentage >= 100:
                project.status = 'Completed'
            elif project.status == 'Pending':
                project.status = 'Ongoing'

            project.save(
                update_fields=[
                    'progress_percentage',
                    'status',
                    'updated_at',
                ]
            )

    record_audit_event(
        request=request,
        action_type=report.status.lower(),
        target_entity='VerificationReport',
        target_id=report.pk,
    )

    messages.success(request, f'Report #{report.pk} was {report.status.lower()}.')
    return redirect('verifications:report_detail', pk=report.pk)
