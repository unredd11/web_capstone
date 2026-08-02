from django.db import models
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
    image_hash = models.CharField(max_length=64, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.project} — {self.status}"

    class Meta:
        ordering = ['-submitted_at']
