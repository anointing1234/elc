from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import Account,WrittenReview
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
import re
from django.contrib.auth import get_user_model


class RegisterForm(forms.ModelForm):
    email = forms.EmailField(
        max_length=100,
        help_text='Required. Add a valid email address'
    )
    username = forms.CharField(
        max_length=15
    )
    password = forms.CharField(
        widget=forms.PasswordInput(),
        help_text='Required. Enter a password'
    )

    class Meta:
        model = Account
        fields = ("email", "username", "password")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update widget attributes including the IDs used in your template
        self.fields['email'].widget.attrs.update({
            'class': 'form-control form-control-bg',
            'style': 'border: 1px solid black;',
            'placeholder': 'Enter your email',
            'id': 'register-email-2'
        })
        self.fields['username'].widget.attrs.update({
            'class': 'form-control form-control-bg',
            'style': 'border: 1px solid black;',
            'placeholder': 'Enter your username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control form-control-bg',
            'style': 'border: 1px solid black;',
            'placeholder': 'Create a password',
            'id': 'register-password-2'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Account.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise forms.ValidationError('Password must be at least 8 characters long.')
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['username']
        if commit:
            user.set_password(self.cleaned_data['password'])
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=100)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update widget attributes including IDs matching the template
        self.fields['email'].widget.attrs.update({
            'class': 'form-control form-control-bg',
            'style': 'border: 1px solid black;',
            'placeholder': 'Enter your email',
            'id': 'singin-email-2'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control form-control-bg',
            'style': 'border: 1px solid black;',
            'placeholder': 'Enter your password',
            'id': 'singin-password-2'
        })

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        user = authenticate(email=email, password=password)
        if user is None:
            raise forms.ValidationError("Invalid email or password.")
        self.user_cache = user
        return self.cleaned_data

    def get_user(self):
        return self.user_cache

   


class SendresetcodeForm(forms.Form):
    email = forms.EmailField(
        max_length=100,
        help_text='Required. Enter your email address to receive a password reset code.'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set Bootstrap classes and placeholders
        self.fields['email'].widget.attrs.update({
            'class': 'form-control form-control-bg',
            'style': 'border: 1px solid black;',
            'placeholder': 'Enter your email'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        User = get_user_model()  # Get the custom user model
        if not User.objects.filter(email=email).exists():
            raise ValidationError('No user is associated with this email address.')
        return email
    



class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        label="Email Address",
        help_text="Required. Enter your email address."
    )
    reset_code = forms.CharField(
        label="Reset Code",
        help_text="Required. Enter the reset code you received."
    )
    new_password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(),
        min_length=8,
        help_text="Required. Minimum length is 8 characters."
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(),
        help_text="Required. Please confirm your new password."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set Bootstrap classes and placeholders
        self.fields['email'].widget.attrs.update({
            'class': 'form-control form-control-bg',
            'style': 'border: 1px solid black;',
            'placeholder': 'Enter your email'
        })
        self.fields['reset_code'].widget.attrs.update({
            'class': 'form-control form-control-bg',
            'style': 'border: 1px solid black;',
            'placeholder': 'Enter your reset code'
        })
        self.fields['new_password'].widget.attrs.update({
            'class': 'form-control form-control-bg',
            'style': 'border: 1px solid black;',
            'placeholder': 'Enter your new password'
        })
        self.fields['confirm_password'].widget.attrs.update({
            'class': 'form-control form-control-bg',
            'style': 'border: 1px solid black;',
            'placeholder': 'Confirm your new password'
        })

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            raise ValidationError("The two password fields must match.")

        return cleaned_data



class ReviewForm(forms.ModelForm):
    class Meta:
        model = WrittenReview
        fields = ['name', 'stars', 'content', 'image']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your name',
                'required': 'required'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write your review here...',
                'required': 'required'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'placeholder': 'Upload image',
                'accept': 'image/*'
            }),
        }

    # Custom method to render stars as radio buttons
    def stars_widget(self):
        stars_html = ''
        for i in range(1, 6):  # 1 to 5 stars
            stars_html += f'''
                <input type="radio" id="star-{i}" name="stars" value="{i}" required>
                <label for="star-{i}" class="star">&#9733;</label>  <!-- Unicode star character -->
            '''
        return stars_html