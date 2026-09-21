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

    def clean(self):
        cleaned_data = super().clean()

        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')
        radius = cleaned_data.get('geofence_radius')
        budget = cleaned_data.get('budget')
        progress = cleaned_data.get('progress_percentage')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        inspector = cleaned_data.get('assigned_inspector')
        district = cleaned_data.get('district')

        if (latitude is None) != (longitude is None):
            raise forms.ValidationError(
                'Latitude and longitude must be provided together.'
            )

        if latitude is not None and not -90 <= latitude <= 90:
            self.add_error(
                'latitude',
                'Latitude must be between -90 and 90.',
            )

        if longitude is not None and not -180 <= longitude <= 180:
            self.add_error(
                'longitude',
                'Longitude must be between -180 and 180.',
            )

        if radius is not None and radius <= 0:
            self.add_error(
                'geofence_radius',
                'Geofence radius must be greater than zero.',
            )

        if budget is not None and budget < 0:
            self.add_error(
                'budget',
                'Budget cannot be negative.',
            )

        if progress is not None and not 0 <= progress <= 100:
            self.add_error(
                'progress_percentage',
                'Progress must be between 0 and 100.',
            )

        if start_date and end_date and end_date < start_date:
            self.add_error(
                'end_date',
                'End date cannot be earlier than the start date.',
            )

        if inspector and district and inspector.district != district:
            self.add_error(
                'assigned_inspector',
                'The inspector must belong to the project district.',
            )

        return cleaned_data

class AssignInspectorForm(forms.Form):
    inspector = forms.ModelChoiceField(
        queryset=Inspector.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Select an Inspector',
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Assignment notes...',
            }
        ),
    )

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project

        queryset = Inspector.objects.filter(
            is_active=True,
        ).select_related('user')

        if project:
            queryset = queryset.filter(
                district=project.district,
            )

        self.fields['inspector'].queryset = queryset
