from django.contrib import admin
from .models import AuditLog, BlockchainRecord, InspectionImage, VerificationReport


class InspectionImageInline(admin.TabularInline):
    model = InspectionImage
    extra = 0
    fields = (
        'image_file', 'sha256_hash', 'perceptual_hash', 'latitude', 'longitude',
        'captured_at', 'geofence_status',
    )
    readonly_fields = ('sha256_hash', 'perceptual_hash')

@admin.register(VerificationReport)
class VerificationReportAdmin(admin.ModelAdmin):
    list_display = ('project', 'inspector', 'progress_percentage', 'status', 'submitted_at', 'reviewed_by')
    list_filter = ('status',)
    search_fields = ('project__project_name', 'inspector__employee_id', 'accomplishment_description')
    readonly_fields = ('submitted_at',)
    inlines = (InspectionImageInline,)


@admin.register(InspectionImage)
class InspectionImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'report', 'captured_at', 'geofence_status', 'sha256_hash')
    list_filter = ('geofence_status', 'mime_type')
    search_fields = ('sha256_hash', 'perceptual_hash', 'report__project__project_name')


@admin.register(BlockchainRecord)
class BlockchainRecordAdmin(admin.ModelAdmin):
    list_display = ('inspection_image', 'transaction_id', 'block_number', 'commit_status', 'committed_at')
    list_filter = ('commit_status', 'chaincode_name')
    search_fields = ('transaction_id', 'inspection_image__sha256_hash')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action_type', 'target_entity', 'target_id', 'ip_address')
    list_filter = ('action_type', 'target_entity')
    search_fields = ('user__username', 'action_type', 'target_entity', 'device_info')
    readonly_fields = ('timestamp',)
