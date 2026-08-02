from django import forms
from .models import Project, ProjectAssignment
from accounts.models import Inspector

class ProjectForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_inspector'].queryset = Inspector.objects.filter(is_active=True)
        self.fields['assigned_inspector'].empty_label = "-- Select DPWH Field Inspector --"

    class Meta:
        model = Project
        fields = [
            'project_name', 'description', 'location_address', 'district', 
            'contractor', 'assigned_inspector', 'latitude', 'longitude', 
            'geofence_radius', 'budget', 'progress_percentage', 'start_date', 
            'end_date', 'status'
        ]
        widgets = {
            'project_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Construction of New Bridge'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detailed description of structural works and scope'}),
            'location_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brgy. Dalipuga, Iligan City, Lanao del Norte'}),
            'district': forms.Select(attrs={'class': 'form-select'}),
            'contractor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Iligan Construction'}),
            'assigned_inspector': forms.Select(attrs={'class': 'form-select'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '14.6502123', 'step': '0.0000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '121.0494123', 'step': '0.0000001'}),
            'geofence_radius': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '100', 'step': '0.1'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'progress_percentage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01', 'min': '0', 'max': '100'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class AssignInspectorForm(forms.Form):
    inspector = forms.ModelChoiceField(
        queryset=Inspector.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Select an Inspector'
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Assignment notes...'})
    )
