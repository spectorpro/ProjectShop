from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Mailing
from django.utils import timezone


# --- Форма для рассылки (отдельно) ---
class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ['start_time', 'end_time', 'message', 'recipients']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError('Время начала должно быть строго раньше времени окончания.')

        now = timezone.now()
        if start_time and start_time < now:
            raise forms.ValidationError('Время начала не может быть в прошлом.')

        return cleaned_data


# --- Форма регистрации (отдельно, на одном уровне с MailingForm) ---
class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
