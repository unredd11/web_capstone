from django.contrib import admin
from .models import VerificationReport

@admin.register(VerificationReport)
class VerificationReportAdmin(admin.ModelAdmin):
    list_display = ('project', 'inspector', 'status', 'image_hash', 'submitted_at')
    list_filter = ('status',)
