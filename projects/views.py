from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Project, ProjectAssignment
from .forms import ProjectForm, AssignInspectorForm

def project_list(request):
    projects = Project.objects.all()
    return render(request, 'projects/project_list.html', {'projects': projects, 'active_page': 'project_list'})

def project_add(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            if project.assigned_inspector:
                ProjectAssignment.objects.get_or_create(project=project, inspector=project.assigned_inspector)
            messages.success(request, 'Project created successfully!')
            return redirect('projects:project_list')
    else:
        form = ProjectForm()
    return render(request, 'projects/project_form.html', {'form': form, 'title': 'Add New Project', 'active_page': 'project_add'})

def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            project = form.save()
            if project.assigned_inspector:
                ProjectAssignment.objects.get_or_create(project=project, inspector=project.assigned_inspector)
            messages.success(request, 'Project updated successfully!')
            return redirect('projects:project_list')
    else:
        form = ProjectForm(instance=project)
    return render(request, 'projects/project_form.html', {'form': form, 'title': f'Edit: {project.project_name}', 'project': project, 'active_page': 'project_list'})

def assign_inspector(request, pk):
    project = get_object_or_404(Project, pk=pk)
    assignments = ProjectAssignment.objects.filter(project=project).select_related('inspector__user')
    if request.method == 'POST':
        form = AssignInspectorForm(request.POST)
        if form.is_valid():
            inspector = form.cleaned_data['inspector']
            project.assigned_inspector = inspector
            project.save()
            if ProjectAssignment.objects.filter(project=project, inspector=inspector).exists():
                messages.warning(request, f'{inspector} is already assigned to this project.')
            else:
                ProjectAssignment.objects.create(
                    project=project,
                    inspector=inspector,
                    notes=form.cleaned_data['notes'],
                )
                messages.success(request, f'{inspector} assigned to {project.project_name}!')
            return redirect('projects:assign_inspector', pk=pk)
    else:
        form = AssignInspectorForm()
    return render(request, 'projects/assign_inspector.html', {
        'form': form, 'project': project, 'assignments': assignments, 'active_page': 'project_list'
    })
