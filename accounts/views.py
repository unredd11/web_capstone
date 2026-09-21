from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.db import transaction
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from verifications.audit import record_audit_event

from .forms import InspectorRegistrationForm, InspectorUpdateForm
from .models import Inspector


def is_admin_user(user):
    """Check if user is authenticated and holds administrator privileges."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@user_passes_test(
    is_admin_user,
    login_url='accounts:login',
)
@require_POST
@transaction.atomic
def toggle_inspector_status(request, pk):
    inspector = get_object_or_404(
        Inspector.objects.select_related('user'),
        pk=pk,
    )

    if (
        inspector.is_active
        and inspector.assigned_projects.filter(
            status__in=['Pending', 'Ongoing']
        ).exists()
    ):
        messages.error(
            request,
            'Reassign this inspector’s active projects before '
            'deactivating the account.',
        )
        return redirect('accounts:inspector_list')

    new_status = not inspector.is_active

    inspector.is_active = new_status
    inspector.save(update_fields=['is_active'])

    inspector.user.is_active = new_status
    inspector.user.save(update_fields=['is_active'])

    record_audit_event(
        request=request,
        action_type=(
            'activate_inspector'
            if new_status
            else 'deactivate_inspector'
        ),
        target_entity='Inspector',
        target_id=inspector.pk,
    )

    action = 'activated' if new_status else 'deactivated'

    messages.success(
        request,
        f'{inspector.user.get_full_name()} was {action}.',
    )

    return redirect('accounts:inspector_list')

def admin_login(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('dashboard:overview')

    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # Allow login using Email address in addition to username
        login_username = username_or_email
        if '@' in username_or_email:
            try:
                user_obj = User.objects.get(email__iexact=username_or_email)
                login_username = user_obj.username
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                pass

        user = authenticate(request, username=login_username, password=password)
        if user is not None:
            # STRICT REQUIREMENT: Only admin accounts can log in to manage inspector accounts
            if user.is_staff or user.is_superuser:
                login(request, user)
                record_audit_event(
                    request=request,
                    user=user,
                    action_type='admin_login',
                    target_entity='User',
                    target_id=user.pk,
                )
                messages.success(request, f"Welcome to DPWH VERIFY Admin Portal, {user.get_full_name() or user.username}!")
                next_url = (
                    request.POST.get('next')
                    or request.GET.get('next')
                )
                if next_url and url_has_allowed_host_and_scheme(
                    url=next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(next_url)
                return redirect('dashboard:overview')
            else:
                record_audit_event(
                    request=request,
                    user=user,
                    action_type='admin_login_denied',
                    target_entity='User',
                    target_id=user.pk,
                )
                messages.error(request, "Access Denied: Your account belongs to a Field Inspector. Only authorized DPWH Administrators hold access rights to manage inspector accounts and web dashboard reports.")
        else:
            record_audit_event(
                request=request,
                action_type='admin_login_failed',
                target_entity='Authentication',
            )
            messages.error(request, "Invalid administrator email/username or security password.")

    return render(
        request,
        'accounts/login.html',
        {'next': request.GET.get('next', '')},
    )

@require_POST
def admin_logout(request):
    if request.user.is_authenticated:
        record_audit_event(
            request=request,
            action_type='admin_logout',
            target_entity='User',
            target_id=request.user.pk,
        )
    logout(request)
    messages.info(request, "You have been safely logged out from the DPWH VERIFY Admin Portal.")
    return redirect('accounts:login')

@user_passes_test(is_admin_user, login_url='accounts:login')
@transaction.atomic
def register_inspector(request):
    if request.method == 'POST':
        form = InspectorRegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['email'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
            )
            inspector = Inspector.objects.create(
                user=user,
                employee_id=form.cleaned_data['employee_id'],
                phone=form.cleaned_data['phone'],
                district=form.cleaned_data['district'],
                position=form.cleaned_data['position'],
            )
            record_audit_event(
                request=request,
                action_type='register_inspector',
                target_entity='Inspector',
                target_id=inspector.pk,
            )
            messages.success(request, f"Inspector {user.get_full_name()} registered successfully!")
            return redirect('accounts:inspector_list')
    else:
        form = InspectorRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form, 'active_page': 'register'})

@user_passes_test(is_admin_user, login_url='accounts:login')
@transaction.atomic
def edit_inspector(request, pk):
    inspector = get_object_or_404(
        Inspector.objects.select_related('user'),
        pk=pk,
    )

    if request.method == 'POST':
        form = InspectorUpdateForm(
            request.POST,
            inspector=inspector,
        )

        if form.is_valid():
            form.save()

            record_audit_event(
                request=request,
                action_type='update_inspector',
                target_entity='Inspector',
                target_id=inspector.pk,
            )

            messages.success(
                request,
                'Inspector information updated successfully.',
            )
            return redirect('accounts:inspector_list')
    else:
        form = InspectorUpdateForm(inspector=inspector)

    return render(
        request,
        'accounts/edit_inspector.html',
        {
            'form': form,
            'inspector': inspector,
            'active_page': 'inspector_list',
        },
    )

@user_passes_test(is_admin_user, login_url='accounts:login')
def inspector_list(request):
    inspectors = Inspector.objects.select_related('user').all()
    return render(request, 'accounts/inspector_list.html', {'inspectors': inspectors, 'active_page': 'inspector_list'})
