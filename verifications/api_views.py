import json
from decimal import Decimal, InvalidOperation
from functools import wraps

from django.contrib.auth import authenticate, get_user_model
from django.core import signing
from django.core.signing import BadSignature, SignatureExpired
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from accounts.models import Inspector
from projects.models import Project
from .forms import InspectionImageForm
from .models import (
    AuditLog,
    BlockchainRecord,
    InspectionImage,
    VerificationReport,
)
from .services import (
    calculate_distance_meters,
    calculate_phash,
    calculate_sha256,
)


TOKEN_SALT = 'mobile-inspector-api'
TOKEN_MAX_AGE = 24 * 60 * 60
User = get_user_model()
def api_error(message, status=400, details=None):
    response = {
        'success': False,
        'message': message,
    }

    if details:
        response['details'] = details

    return JsonResponse(response, status=status)


def inspector_token_required(view_function):
    @wraps(view_function)
    def wrapped_view(request, *args, **kwargs):
        authorization = request.headers.get('Authorization', '')

        if not authorization.startswith('Bearer '):
            return api_error(
                'A Bearer authentication token is required.',
                status=401,
            )

        token = authorization.removeprefix('Bearer ').strip()

        try:
            token_data = signing.loads(
                token,
                salt=TOKEN_SALT,
                max_age=TOKEN_MAX_AGE,
            )
        except SignatureExpired:
            return api_error(
                'Your login token has expired. Please log in again.',
                status=401,
            )
        except BadSignature:
            return api_error(
                'The authentication token is invalid.',
                status=401,
            )

        try:
            user = User.objects.select_related(
                'inspector_profile'
            ).get(
                pk=token_data['user_id'],
                is_active=True,
            )

            inspector = user.inspector_profile
        except (
            User.DoesNotExist,
            Inspector.DoesNotExist,
            KeyError,
        ):
            return api_error(
                'The inspector account does not exist.',
                status=401,
            )

        if not inspector.is_active:
            return api_error(
                'This inspector account is inactive.',
                status=403,
            )

        request.api_user = user
        request.inspector = inspector

        return view_function(request, *args, **kwargs)

    return wrapped_view


@csrf_exempt
def mobile_login(request):
    if request.method != 'POST':
        return api_error(
            'Only POST requests are allowed.',
            status=405,
        )

    try:
        request_data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return api_error('Invalid JSON request.')

    username = str(request_data.get('username', '')).strip()
    password = str(request_data.get('password', ''))

    if not username or not password:
        return api_error(
            'Username and password are required.'
        )

    user = authenticate(
        request,
        username=username,
        password=password,
    )

    if user is None:
        return api_error(
            'Invalid username or password.',
            status=401,
        )

    try:
        inspector = user.inspector_profile
    except Inspector.DoesNotExist:
        return api_error(
            'This account is not registered as an inspector.',
            status=403,
        )

    if not user.is_active or not inspector.is_active:
        return api_error(
            'This inspector account is inactive.',
            status=403,
        )

    token = signing.dumps(
        {
            'user_id': user.pk,
            'employee_id': inspector.employee_id,
        },
        salt=TOKEN_SALT,
        compress=True,
    )

    AuditLog.objects.create(
        user=user,
        action_type='mobile_login',
        target_entity='Inspector',
        target_id=inspector.pk,
        ip_address=request.META.get('REMOTE_ADDR'),
        device_info=request.META.get(
            'HTTP_USER_AGENT',
            '',
        )[:255],
    )

    return JsonResponse(
        {
            'success': True,
            'message': 'Login successful.',
            'token': token,
            'expires_in_seconds': TOKEN_MAX_AGE,
            'inspector': {
                'id': inspector.pk,
                'employee_id': inspector.employee_id,
                'full_name': user.get_full_name(),
                'district': inspector.district,
                'position': inspector.position,
            },
        }
    )


@csrf_exempt
@inspector_token_required
def mobile_projects(request):
    if request.method != 'GET':
        return api_error(
            'Only GET requests are allowed.',
            status=405,
        )

    projects = Project.objects.filter(
        Q(assigned_inspector=request.inspector)
        | Q(assignments__inspector=request.inspector)
    ).distinct()

    project_data = []

    for project in projects:
        project_data.append(
            {
                'id': project.pk,
                'project_name': project.project_name,
                'description': project.description,
                'location_address': project.location_address,
                'district': project.district,
                'contractor': project.contractor,
                'latitude': (
                    str(project.latitude)
                    if project.latitude is not None
                    else None
                ),
                'longitude': (
                    str(project.longitude)
                    if project.longitude is not None
                    else None
                ),
                'geofence_radius': str(
                    project.geofence_radius
                ),
                'progress_percentage': str(
                    project.progress_percentage
                ),
                'status': project.status,
            }
        )

    return JsonResponse(
        {
            'success': True,
            'count': len(project_data),
            'projects': project_data,
        }
    )


@csrf_exempt
@inspector_token_required
def mobile_submit_report(request):
    if request.method != 'POST':
        return api_error(
            'Only POST requests are allowed.',
            status=405,
        )

    project_id = request.POST.get('project_id')
    progress_value = request.POST.get(
        'progress_percentage'
    )
    accomplishment_description = request.POST.get(
        'accomplishment_description',
        '',
    ).strip()

    if not project_id:
        return api_error('project_id is required.')

    try:
        project_id = int(project_id)
    except (TypeError, ValueError):
        return api_error('project_id must be a number.')

    project = Project.objects.filter(
        Q(assigned_inspector=request.inspector)
        | Q(assignments__inspector=request.inspector),
        pk=project_id,
    ).distinct().first()

    if project is None:
        return api_error(
            'The project does not exist or is not assigned to you.',
            status=403,
        )

    if (
        project.latitude is None
        or project.longitude is None
    ):
        return api_error(
            'The project does not have geofence coordinates.'
        )

    try:
        progress_percentage = Decimal(progress_value)
    except (InvalidOperation, TypeError):
        return api_error(
            'progress_percentage must be a valid number.'
        )

    if progress_percentage < 0 or progress_percentage > 100:
        return api_error(
            'progress_percentage must be between 0 and 100.'
        )

    if not accomplishment_description:
        return api_error(
            'accomplishment_description is required.'
        )

    image_form = InspectionImageForm(
        request.POST,
        request.FILES,
    )

    if not image_form.is_valid():
        return api_error(
            'The inspection image information is invalid.',
            details=image_form.errors.get_json_data(),
        )

    uploaded_file = image_form.cleaned_data['image_file']

    try:
        sha256_hash = calculate_sha256(uploaded_file)
        perceptual_hash = calculate_phash(uploaded_file)
    except (OSError, ValueError):
        return api_error(
            'The uploaded image could not be processed.'
        )

    inspection_image = image_form.save(commit=False)

    distance = calculate_distance_meters(
        project.latitude,
        project.longitude,
        inspection_image.latitude,
        inspection_image.longitude,
    )

    geofence_status = (
        'Inside'
        if distance <= float(project.geofence_radius)
        else 'Outside'
    )

    with transaction.atomic():
        report = VerificationReport.objects.create(
            project=project,
            inspector=request.inspector,
            progress_percentage=progress_percentage,
            accomplishment_description=(
                accomplishment_description
            ),
            status='Pending',
        )

        inspection_image.report = report
        inspection_image.sha256_hash = sha256_hash
        inspection_image.perceptual_hash = perceptual_hash
        inspection_image.geofence_distance = round(
            distance,
            2,
        )
        inspection_image.geofence_status = geofence_status
        inspection_image.file_size = uploaded_file.size
        inspection_image.mime_type = getattr(
            uploaded_file,
            'content_type',
            '',
        )
        inspection_image.save()

        report.image_hash = inspection_image.sha256_hash
        report.latitude = inspection_image.latitude
        report.longitude = inspection_image.longitude
        report.save(
            update_fields=[
                'image_hash',
                'latitude',
                'longitude',
            ]
        )

        BlockchainRecord.objects.create(
            inspection_image=inspection_image,
            chaincode_name='evidence',
            commit_status='Pending',
            metadata_json={
                'report_id': report.pk,
                'image_id': inspection_image.pk,
                'project_id': project.pk,
                'inspector_id': request.inspector.pk,
                'sha256_hash': sha256_hash,
                'perceptual_hash': perceptual_hash,
                'geofence_status': geofence_status,
                'geofence_distance': round(distance, 2),
            },
        )

        AuditLog.objects.create(
            user=request.api_user,
            action_type='mobile_report_submission',
            target_entity='VerificationReport',
            target_id=report.pk,
            ip_address=request.META.get('REMOTE_ADDR'),
            device_info=request.META.get(
                'HTTP_USER_AGENT',
                '',
            )[:255],
        )

    return JsonResponse(
        {
            'success': True,
            'message': 'Inspection report submitted.',
            'report': {
                'id': report.pk,
                'status': report.status,
                'project_id': project.pk,
                'progress_percentage': str(
                    report.progress_percentage
                ),
            },
            'image': {
                'id': inspection_image.pk,
                'sha256_hash': sha256_hash,
                'perceptual_hash': perceptual_hash,
                'geofence_distance': round(distance, 2),
                'geofence_status': geofence_status,
            },
            'blockchain': {
                'status': 'Pending',
                'message': (
                    'Evidence is ready for Fabric submission.'
                ),
            },
        },
        status=201,
    )