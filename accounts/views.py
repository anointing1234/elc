from django.shortcuts import render,get_object_or_404, redirect
from django.urls import reverse
from .form import RegisterForm,LoginForm,SendresetcodeForm,PasswordResetForm,ReviewForm 
from django.http import JsonResponse
import requests 
from decimal import Decimal, InvalidOperation
import logging
import json
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import logout as auth_logout,login as auth_login,authenticate
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.core.mail import EmailMessage
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal,InvalidOperation
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.conf.urls.static import static
from django.core.mail import EmailMultiAlternatives
import pytz
from datetime import datetime, timedelta
from pytz import timezone as pytz_timezone
import logging
from django.db import transaction
from django.db.models import F,Sum
from django.contrib.auth.decorators import login_required
from .models import Product,ShoppingCart,BankDetails,Order,PasswordResetCode,WrittenReview 
import logging
from django.core.mail import send_mail



def authenticate_view(request):
    login_form = LoginForm()
    register_form = RegisterForm()
    return render(request, 'auth/authenticate.html', {
        'login_form': login_form,
        'register_form': register_form,
    })






def register(request):
    if request.method == 'POST':
        register_form = RegisterForm(request.POST)
        
        if register_form.is_valid():
            register_form.save()
            return JsonResponse({'success': True, 'message': 'Registration successful!', 'redirect_url': '/accounts/login_view'})  # Redirect URL
        else:
            # Collect all form errors
            error_messages = []
            if register_form.errors:
                for field, errors in register_form.errors.items():
                    for error in errors:
                        error_messages.append(f"{field.capitalize()}: {error}")
            error_message = "\n".join(error_messages)

            return JsonResponse({'success': False, 'message': error_message})

    return JsonResponse({'success': False, 'message': 'Invalid request.'})


 

def login_view(request):
    if request.method == 'POST':
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            user = login_form.get_user()
            auth_login(request, user)
            return JsonResponse({
                'success': True,
                'message': 'Login successful!',
                'redirect_url': '/shop/home'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid email  or password.'
            })
    else:
        register_form = RegisterForm()
        login_form = LoginForm()
    return render(request, 'auth/authenticate.html', {
        'login_form': login_form,
        'register_form': register_form,
        })


def logout_view(request):
    auth_logout(request)
    register_form = RegisterForm()
    login_form = LoginForm()
    return render(request, 'auth/authenticate.html', {
        'login_form': login_form,
        'register_form': register_form,
    })




def contact_form(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        name = request.POST.get('cname')
        email = request.POST.get('cemail')
        phone = request.POST.get('cphone', 'Not provided')
        subject = request.POST.get('csubject', 'No Subject')
        message = request.POST.get('cmessage')

        if not name or not email or not message:
            return JsonResponse({'success': False, 'message': 'Please fill in all required fields.'})

        # Construct email message
        email_subject = f"New Contact Form Submission: {subject}"
        email_body = f"""
        Name: {name}
        Email: {email}
        Phone: {phone}
        Message:
        {message}
        """

        try:
            send_mail(
                subject=email_subject,
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,  # Ensure this is a valid sender
                recipient_list=['yakubudestiny9@gmail.com'],  # Send to the user
                fail_silently=False,
            )
            return JsonResponse({'success': True, 'message': 'Your message has been sent successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error sending email: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)




def send_reset_code_view(request):
    if request.method == 'POST':
        form = SendresetcodeForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # Check if the email is registered
            User = get_user_model()  # Get the custom user model
            if not User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'message': 'This email address is not registered.'})

            # Generate a reset code
            reset_code = get_random_string(length=7)  # Generate a random string as the reset code
            
            # Store the reset code in the database
            PasswordResetCode.objects.update_or_create(
                email=email,
                defaults={'reset_code': reset_code}
            )
            
            # Send the email
            send_mail(
                'Password Reset Code',
                f'Your password reset code is: {reset_code}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            return JsonResponse({'success': True, 'message': 'A password reset code has been sent to your email.'})
        else:
            return JsonResponse({'success': False, 'message': form.errors['email'][0]})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})











def reset_password_view(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)  # Use a different variable name
        if form.is_valid():
            email = form.cleaned_data['email']
            reset_code = form.cleaned_data['reset_code']
            new_password = form.cleaned_data['new_password']

            # Check if the reset code is valid for the given email
            try:
                reset_entry = PasswordResetCode.objects.get(email=email, reset_code=reset_code)
            except PasswordResetCode.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Invalid reset code or email.'})

            # Update the user's password
            User = get_user_model()
            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)  # Set the new password
                user.save()

                # Optionally, delete the reset code after use
                reset_entry.delete()

                messages.success(request, "Your password has been reset successfully.")
                return JsonResponse({'success': True, 'message': 'Your password has been reset successfully.'})
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'User  not found.'})

    else:
        form = PasswordResetForm()  # This is now correctly instantiated

    return render(request,'auth/reset_password.html', {'form': form})


def forgot_password(request):
    sendmailreset = SendresetcodeForm()
    return render(request,'auth/send_password.html',{'sendmailreset': sendmailreset})