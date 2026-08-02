from django.contrib import admin
from .models import Project, ProjectAssignment

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('project_name', 'district', 'contractor', 'status', 'budget', 'created_at')
    list_filter = ('status', 'district')
    search_fields = ('project_name', 'contractor')

@admin.register(ProjectAssignment)
class ProjectAssignmentAdmin(admin.ModelAdmin):
    list_display = ('project', 'inspector', 'assigned_date')
