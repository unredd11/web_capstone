from django.contrib import admin
from .models import Inspector

@admin.register(Inspector)
class InspectorAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'user', 'district', 'position', 'is_active', 'date_registered')
    list_filter = ('district', 'is_active')
    search_fields = ('employee_id', 'user__first_name', 'user__last_name')
