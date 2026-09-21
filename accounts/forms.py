import re

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q

from .models import Inspector


class InspectorRegistrationForm(forms.Form):
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    employee_id = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    district = forms.ChoiceField(
        choices=Inspector.DISTRICT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    position = forms.CharField(
        max_length=100,
        initial='Field Inspector',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    password = forms.CharField(
        validators=[validate_password],
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()

        if User.objects.filter(
            Q(email__iexact=email) | Q(username__iexact=email)
        ).exists():
            raise forms.ValidationError(
                'An account with this email already exists.'
            )

        return email

    def clean_employee_id(self):
        employee_id = self.cleaned_data['employee_id'].strip().upper()

        if not re.fullmatch(r'DPWH-[A-Z0-9-]{3,15}', employee_id):
            raise forms.ValidationError(
                'Use a DPWH employee ID such as DPWH-2026-001.'
            )

        if Inspector.objects.filter(
            employee_id__iexact=employee_id
        ).exists():
            raise forms.ValidationError(
                'This employee ID already exists.'
            )

        return employee_id

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()

        if phone and not re.fullmatch(r'[+0-9 ()-]{7,15}', phone):
            raise forms.ValidationError(
                'Enter a valid telephone number.'
            )

        return phone

    def clean(self):
        cleaned_data = super().clean()

        if (
            cleaned_data.get('password')
            and cleaned_data.get('confirm_password')
            and cleaned_data['password']
            != cleaned_data['confirm_password']
        ):
            self.add_error(
                'confirm_password',
                'Passwords do not match.',
            )

        return cleaned_data


class InspectorUpdateForm(forms.Form):
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    district = forms.ChoiceField(
        choices=Inspector.DISTRICT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    position = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, inspector, **kwargs):
        super().__init__(*args, **kwargs)
        self.inspector = inspector

        if not self.is_bound:
            self.initial.update({
                'first_name': inspector.user.first_name,
                'last_name': inspector.user.last_name,
                'email': inspector.user.email,
                'phone': inspector.phone,
                'district': inspector.district,
                'position': inspector.position,
            })

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()

        duplicate = User.objects.filter(
            Q(email__iexact=email) | Q(username__iexact=email)
        ).exclude(pk=self.inspector.user_id)

        if duplicate.exists():
            raise forms.ValidationError(
                'Another account already uses this email.'
            )

        return email

    def save(self):
        user = self.inspector.user
        email = self.cleaned_data['email']

        user.first_name = self.cleaned_data['first_name'].strip()
        user.last_name = self.cleaned_data['last_name'].strip()
        user.email = email
        user.username = email
        user.save()

        self.inspector.phone = self.cleaned_data['phone']
        self.inspector.district = self.cleaned_data['district']
        self.inspector.position = self.cleaned_data['position'].strip()
        self.inspector.save()

        return self.inspector