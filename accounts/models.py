from django.db import models
from django.contrib.auth.models import User

class Inspector(models.Model):
    DISTRICT_CHOICES = [
        ('LDN 1st DEO', 'Lanao del Norte 1st DEO (Iligan City Area)'),
        ('LDN 2nd DEO', 'Lanao del Norte 2nd DEO (Tubod Area)'),
        ('Region X RO', 'DPWH Region X Regional Office (Northern Mindanao)'),
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
