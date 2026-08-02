from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test

def is_admin_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@user_passes_test(is_admin_user, login_url='accounts:login')
def overview(request):
    context = {
        'active_page': 'overview',
    }
    return render(request, 'dashboard/overview.html', context)
