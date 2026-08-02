from django.db import models
from accounts.models import Inspector

class Project(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Ongoing', 'Ongoing'),
        ('Completed', 'Completed'),
        ('Suspended', 'Suspended'),
    ]
    DISTRICT_CHOICES = [
        ('District I', 'District I — Caloocan'),
        ('District II', 'District II — Marikina'),
        ('District III', 'District III — Valenzuela'),
        ('District IV', 'District IV — Quezon City'),
    ]
    project_name = models.CharField(max_length=200, verbose_name="Project Name")
    description = models.TextField(blank=True, verbose_name="Description")
    location_address = models.CharField(max_length=255, blank=True, verbose_name="Physical Site Address")
    district = models.CharField(max_length=50, choices=DISTRICT_CHOICES, verbose_name="District / Jurisdiction")
    contractor = models.CharField(max_length=200, blank=True, verbose_name="Assigned Contractor Company")
    assigned_inspector = models.ForeignKey(Inspector, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_projects', verbose_name="Assigned DPWH Field Inspector")
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, help_text="GPS Latitude Coordinate (e.g., 14.6502)")
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, help_text="GPS Longitude Coordinate (e.g., 121.0494)")
    geofence_radius = models.DecimalField(max_digits=8, decimal_places=2, default=100.00, help_text="Acceptable geofence radius in meters")
    budget = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Allocated Budget (₱)")
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="Current Progress (%)")
    start_date = models.DateField(null=True, blank=True, verbose_name="Scheduled Start Date")
    end_date = models.DateField(null=True, blank=True, verbose_name="Scheduled End Date")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', verbose_name="Status")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.project_name

    class Meta:
        ordering = ['-created_at']

class ProjectAssignment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='assignments')
    inspector = models.ForeignKey(Inspector, on_delete=models.CASCADE, related_name='assignments')
    assigned_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('project', 'inspector')
        ordering = ['-assigned_date']

    def __str__(self):
        return f"{self.inspector} → {self.project}"
