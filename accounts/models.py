from django.db import models
from django.contrib.auth.models import User

class Inspector(models.Model):
    DISTRICT_CHOICES = [
        ('District I', 'District I — Caloocan'),
        ('District II', 'District II — Marikina'),
        ('District III', 'District III — Valenzuela'),
        ('District IV', 'District IV — Quezon City'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='inspector_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=15, blank=True)
    district = models.CharField(max_length=50, choices=DISTRICT_CHOICES)
    position = models.CharField(max_length=100, default='Field Inspector')
    is_active = models.BooleanField(default=True)
    date_registered = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"

    class Meta:
        ordering = ['-date_registered']
