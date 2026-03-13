from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'first_name', 'last_name', 'phone', 'email', 'role', 'avatar', 'password1', 'password2']


class ProfileUpdateForm(forms.ModelForm):
    """Formulaire de mise à jour du profil (nom, email, avatar)."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Prénom'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nom'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email'}),
        }