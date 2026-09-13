from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import InspectionImageForm, ReportReviewForm
from .models import AuditLog, VerificationReport
from .services import calculate_distance_meters, calculate_phash, calculate_sha256


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


@user_passes_test(is_admin_user, login_url='accounts:login')
def report_detail(request, pk):
    report = get_object_or_404(
        VerificationReport.objects.select_related(
            'project', 'inspector__user', 'reviewed_by'
        ).prefetch_related('images'),
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

    AuditLog.objects.create(
        user=request.user,
        action_type=report.status.lower(),
        target_entity='VerificationReport',
        target_id=report.pk,
        ip_address=request.META.get('REMOTE_ADDR'),
        device_info=request.META.get('HTTP_USER_AGENT', '')[:255],
    )

    messages.success(request, f'Report #{report.pk} was {report.status.lower()}.')
    return redirect('verifications:report_detail', pk=report.pk)
