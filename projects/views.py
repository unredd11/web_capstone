from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from verifications.audit import record_audit_event

from .forms import ProjectForm, AssignInspectorForm
from .models import Project, ProjectAssignment

def is_admin_user(user):
    return user.is_authenticated and (
        user.is_staff or user.is_superuser
    )

@user_passes_test(is_admin_user, login_url='accounts:login')
def project_list(request):
    projects = Project.objects.all()
    return render(request, 'projects/project_list.html', {'projects': projects, 'active_page': 'project_list'})

@user_passes_test(is_admin_user, login_url='accounts:login')
@transaction.atomic
def project_add(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            record_audit_event(
                request=request,
                action_type='create_project',
                target_entity='Project',
                target_id=project.pk,
            )
            if project.assigned_inspector:
                _, assignment_created = ProjectAssignment.objects.get_or_create(
                    project=project,
                    inspector=project.assigned_inspector,
                )
                if assignment_created:
                    record_audit_event(
                        request=request,
                        action_type='assign_inspector',
                        target_entity='Project',
                        target_id=project.pk,
                    )
            messages.success(request, 'Project created successfully!')
            return redirect('projects:project_list')
    else:
        form = ProjectForm()
    return render(request, 'projects/project_form.html', {'form': form, 'title': 'Add New Project', 'active_page': 'project_add'})

@user_passes_test(is_admin_user, login_url='accounts:login')
@transaction.atomic
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            project = form.save()
            record_audit_event(
                request=request,
                action_type='update_project',
                target_entity='Project',
                target_id=project.pk,
            )
            if project.assigned_inspector:
                _, assignment_created = ProjectAssignment.objects.get_or_create(
                    project=project,
                    inspector=project.assigned_inspector,
                )
                if assignment_created:
                    record_audit_event(
                        request=request,
                        action_type='assign_inspector',
                        target_entity='Project',
                        target_id=project.pk,
                    )
            messages.success(request, 'Project updated successfully!')
            return redirect('projects:project_list')
    else:
        form = ProjectForm(instance=project)
    return render(request, 'projects/project_form.html', {'form': form, 'title': f'Edit: {project.project_name}', 'project': project, 'active_page': 'project_list'})

@user_passes_test(is_admin_user, login_url='accounts:login')
@transaction.atomic
def assign_inspector(request, pk):
    project = get_object_or_404(Project, pk=pk)
    assignments = ProjectAssignment.objects.filter(project=project).select_related('inspector__user')
    if request.method == 'POST':
        form = AssignInspectorForm(request.POST)
        if form.is_valid():
            inspector = form.cleaned_data['inspector']
            previous_inspector_id = project.assigned_inspector_id
            project.assigned_inspector = inspector
            project.save(update_fields=['assigned_inspector', 'updated_at'])
            _, assignment_created = ProjectAssignment.objects.get_or_create(
                project=project,
                inspector=inspector,
                defaults={'notes': form.cleaned_data['notes']},
            )
            if previous_inspector_id == inspector.pk:
                messages.warning(request, f'{inspector} is already assigned to this project.')
            else:
                record_audit_event(
                    request=request,
                    action_type=(
                        'assign_inspector'
                        if previous_inspector_id is None
                        else 'reassign_inspector'
                    ),
                    target_entity='Project',
                    target_id=project.pk,
                )
                messages.success(request, f'{inspector} assigned to {project.project_name}!')
            return redirect('projects:assign_inspector', pk=pk)
    else:
        form = AssignInspectorForm()
    return render(request, 'projects/assign_inspector.html', {
        'form': form, 'project': project, 'assignments': assignments, 'active_page': 'project_list'
    })
