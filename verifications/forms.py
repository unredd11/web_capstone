from django import forms
from PIL import Image, UnidentifiedImageError

from .models import InspectionImage

class ReportReviewForm(forms.Form):
    DECISION_CHOICES = [
        ('Approved', 'Approve'),
        ('Rejected', 'Reject'),
    ]

    decision = forms.ChoiceField(
        choices=DECISION_CHOICES,
        widget=forms.RadioSelect,
    )

    review_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter review notes...',
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        decision = cleaned_data.get('decision')
        review_notes = cleaned_data.get('review_notes', '').strip()

        if decision == 'Rejected' and not review_notes:
            self.add_error(
                'review_notes',
                'A reason is required when rejecting a report.',
            )

        return cleaned_data

class InspectionImageForm(forms.ModelForm):
    MAX_IMAGE_SIZE = 10 * 1024 * 1024
    ALLOWED_CONTENT_TYPES = {'image/jpeg', 'image/png'}

    def clean_image_file(self):
        image_file = self.cleaned_data['image_file']
        content_type = getattr(image_file, 'content_type', '')

        if content_type not in self.ALLOWED_CONTENT_TYPES:
            raise forms.ValidationError('Only JPEG and PNG images are allowed.')

        if image_file.size > self.MAX_IMAGE_SIZE:
            raise forms.ValidationError('The image must not exceed 10 MB.')

        try:
            image_file.seek(0)
            with Image.open(image_file) as image:
                image.verify()
        except (UnidentifiedImageError, OSError):
            raise forms.ValidationError('The uploaded file is not a valid image.')
        finally:
            image_file.seek(0)

        return image_file

    class Meta:
        model = InspectionImage

        fields = [
            'image_file',
            'latitude',
            'longitude',
            'altitude',
            'gps_accuracy',
            'captured_at',
        ]

        widgets = {
            'image_file': forms.ClearableFileInput(
                attrs={
                    'class': 'form-control',
                    'accept': 'image/jpeg,image/png',
                }
            ),
            'latitude': forms.NumberInput(
                attrs={'class': 'form-control', 'step': 'any'}
            ),
            'longitude': forms.NumberInput(
                attrs={'class': 'form-control', 'step': 'any'}
            ),
            'altitude': forms.NumberInput(
                attrs={'class': 'form-control', 'step': 'any'}
            ),
            'gps_accuracy': forms.NumberInput(
                attrs={'class': 'form-control', 'step': 'any'}
            ),
            'captured_at': forms.DateTimeInput(
                attrs={
                    'class': 'form-control',
                    'type': 'datetime-local',
                }
            ),
        }
