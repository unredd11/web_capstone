from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from .forms import InspectorRegistrationForm
from .models import Inspector

def is_admin_user(user):
    """Check if user is authenticated and holds administrator privileges."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)

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
                user_obj = User.objects.get(email=username_or_email)
                login_username = user_obj.username
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                pass

        user = authenticate(request, username=login_username, password=password)
        if user is not None:
            # STRICT REQUIREMENT: Only admin accounts can log in to manage inspector accounts
            if user.is_staff or user.is_superuser:
                login(request, user)
                messages.success(request, f"Welcome to DPWH VERIFY Admin Portal, {user.get_full_name() or user.username}!")
                next_url = request.GET.get('next', 'dashboard:overview')
                return redirect(next_url)
            else:
                messages.error(request, "Access Denied: Your account belongs to a Field Inspector. Only authorized DPWH Administrators hold access rights to manage inspector accounts and web dashboard reports.")
        else:
            messages.error(request, "Invalid administrator email/username or security password.")

    return render(request, 'accounts/login.html')

def admin_logout(request):
    logout(request)
    messages.info(request, "You have been safely logged out from the DPWH VERIFY Admin Portal.")
    return redirect('accounts:login')

@user_passes_test(is_admin_user, login_url='accounts:login')
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
            Inspector.objects.create(
                user=user,
                employee_id=form.cleaned_data['employee_id'],
                phone=form.cleaned_data['phone'],
                district=form.cleaned_data['district'],
                position=form.cleaned_data['position'],
            )
            messages.success(request, f"Inspector {user.get_full_name()} registered successfully!")
            return redirect('accounts:inspector_list')
    else:
        form = InspectorRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form, 'active_page': 'register'})

@user_passes_test(is_admin_user, login_url='accounts:login')
def inspector_list(request):
    inspectors = Inspector.objects.select_related('user').all()
    return render(request, 'accounts/inspector_list.html', {'inspectors': inspectors, 'active_page': 'inspector_list'})
