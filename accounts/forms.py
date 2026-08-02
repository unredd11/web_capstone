from django import forms
from django.contrib.auth.models import User
from .models import Inspector

class InspectorRegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    employee_id = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. DPWH-2025-001'}))
    phone = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+63 9XX XXX XXXX'}))
    district = forms.ChoiceField(choices=Inspector.DISTRICT_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    position = forms.CharField(max_length=100, initial='Field Inspector', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Job Title'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password') != cleaned_data.get('confirm_password'):
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def clean_employee_id(self):
        eid = self.cleaned_data.get('employee_id')
        if Inspector.objects.filter(employee_id=eid).exists():
            raise forms.ValidationError('This Employee ID already exists.')
        return eid
