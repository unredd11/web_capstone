from django.db import models
from django.conf import settings
from accounts.models import Inspector
from projects.models import Project

class VerificationReport(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='reports')
    inspector = models.ForeignKey(Inspector, on_delete=models.CASCADE, related_name='reports')
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    accomplishment_description = models.TextField(blank=True)
    image_hash = models.CharField(max_length=64, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_verification_reports',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.project} — {self.status}"

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Inspection report'
        verbose_name_plural = 'Inspection reports'


class InspectionImage(models.Model):
    GEOFENCE_STATUS_CHOICES = [
        ('Unknown', 'Unknown'),
        ('Inside', 'Inside'),
        ('Outside', 'Outside'),
    ]

    report = models.ForeignKey(
        VerificationReport,
        on_delete=models.CASCADE,
        related_name='images',
    )
    image_file = models.FileField(upload_to='inspection_images/%Y/%m/%d/')
    sha256_hash = models.CharField(max_length=64, db_index=True)
    perceptual_hash = models.CharField(max_length=64, blank=True, db_index=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    altitude = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    gps_accuracy = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    captured_at = models.DateTimeField()
    geofence_distance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    geofence_status = models.CharField(
        max_length=10,
        choices=GEOFENCE_STATUS_CHOICES,
        default='Unknown',
    )
    file_size = models.PositiveBigIntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image {self.pk} for report {self.report_id}"

    class Meta:
        ordering = ['-captured_at']


class BlockchainRecord(models.Model):
    COMMIT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Committed', 'Committed'),
        ('Failed', 'Failed'),
    ]

    inspection_image = models.OneToOneField(
        InspectionImage,
        on_delete=models.CASCADE,
        related_name='blockchain_record',
    )
    transaction_id = models.CharField(max_length=128, unique=True, null=True, blank=True)
    block_number = models.PositiveBigIntegerField(null=True, blank=True)
    chaincode_name = models.CharField(max_length=100, blank=True)
    commit_status = models.CharField(
        max_length=20,
        choices=COMMIT_STATUS_CHOICES,
        default='Pending',
    )
    committed_at = models.DateTimeField(null=True, blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.transaction_id or f"Pending blockchain record {self.pk}"

    class Meta:
        ordering = ['-created_at']


class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verification_audit_logs',
    )
    action_type = models.CharField(max_length=50)
    target_entity = models.CharField(max_length=100)
    target_id = models.PositiveBigIntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_info = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action_type} - {self.target_entity}:{self.target_id}"

    class Meta:
        ordering = ['-timestamp']
