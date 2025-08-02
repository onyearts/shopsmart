from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.urls import reverse
from .models import ShopOwnerProfile, CustomerProfile, User, PendingUser
from .forms import (
    UserRegistrationForm,
    ShopOwnerRegistrationForm,
    CustomerRegistrationForm,
    LoginForm,
)
import random


def is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest' or \
           request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


def send_verification_email(email, code):
    print(f"DEBUG: Sending verification code {code} to {email}")
    subject = 'Verify Your Email - ShopSmart'
    message = f'Your ShopSmart verification code is: {code}\nPlease enter this code to complete your registration. \nThis code is valid for 15 minutes. If you did not request this, please ignore this email.'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)


def register_customer(request):
    if request.method == 'POST':
        PendingUser.cleanup_expired()
        
        user_form = UserRegistrationForm(request.POST)
        profile_form = CustomerRegistrationForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            email = user_form.cleaned_data['email']

            # Check if user exists
            existing_user = User.objects.filter(email=email).first()
            if existing_user:
                if existing_user.is_active:
                    return render(request, 'accounts/register_customer.html', {
                        'user_form': user_form,
                        'profile_form': profile_form,
                        'error': 'Email already in use.'
                    })
                existing_user.delete()

            # Check pending
            try:
                pending_user = PendingUser.objects.get(email=email)
                if not pending_user.is_expired():
                    return render(request, 'accounts/register_customer.html', {
                        'user_form': user_form,
                        'profile_form': profile_form,
                        'error': 'Verification already sent. Please check your email or wait 15 minutes.'
                    })
                else:
                    pending_user.delete()
            except PendingUser.DoesNotExist:
                pass

            # Create pending user
            code = str(random.randint(100000, 999999))
            PendingUser.objects.create(
                email=email,
                first_name=user_form.cleaned_data['first_name'],
                last_name=user_form.cleaned_data['last_name'],
                password=user_form.cleaned_data['password1'],
                user_type='customer',
                profile_data=profile_form.cleaned_data,
                verification_code=code
            )
            send_verification_email(email, code)

            return redirect(f'/accounts/verify/?email={email}')

        # Collect all form errors for the top alert
        all_errors = []
        for field, errors in user_form.errors.items():
            all_errors.extend(errors)
        for field, errors in profile_form.errors.items():
            all_errors.extend(errors)

        top_error_message = ' '.join(all_errors) if all_errors else 'Please correct the form errors below.'

        return render(request, 'accounts/register_customer.html', {
            'user_form': user_form,
            'profile_form': profile_form,
            'error': top_error_message
        })

    else:
        user_form = UserRegistrationForm()
        profile_form = CustomerRegistrationForm()

    return render(request, 'accounts/register_customer.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


def register_shop_owner(request):
    if request.method == 'POST':
        # First clean up any expired pending users (>24 hours old)
        PendingUser.cleanup_expired()
        
        user_form = UserRegistrationForm(request.POST)
        profile_form = ShopOwnerRegistrationForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            email = user_form.cleaned_data['email'].strip()  # Ensure cleaned email
            
            # Check for existing users (both active and inactive)
            existing_user = User.objects.filter(email=email).first()
            if existing_user:
                if existing_user.is_active:
                    return JsonResponse({'error': 'Email already in use.'}, status=400)
                # Delete inactive user if exists
                existing_user.delete()
                
            # Check for pending users
            try:
                pending_user = PendingUser.objects.get(email=email)
                if not pending_user.is_expired():
                    return JsonResponse({
                        'error': 'Verification already sent. Please check your email or wait 15 minutes.',
                        'can_resend': True,
                        'email': email  # Ensure email is included
                    }, status=400)
                else:
                    # Delete expired pending user
                    pending_user.delete()
            except PendingUser.DoesNotExist:
                pass

            # Create new pending user with validated email
            code = str(random.randint(100000, 999999))
            pending = PendingUser.objects.create(
                email=email,
                first_name=user_form.cleaned_data['first_name'],
                last_name=user_form.cleaned_data['last_name'],
                password=user_form.cleaned_data['password1'],
                user_type='shop',
                profile_data=profile_form.cleaned_data,
                verification_code=code
            )
            send_verification_email(email, code)

            print(f"DEBUG - Email before redirect: {email}")  # Before JsonResponse
            print(f"DEBUG - Response data: { {'redirect_url': f'/accounts/verify/?email={email}'} }")

            # Ensure email is URL encoded and not empty
            if not email:
                return JsonResponse({
                    'error': 'Email is required for verification'
                }, status=400)
                
            return JsonResponse({
                'redirect_url': reverse('accounts:verify') + f'?email={email}',
                'email': email,
                'message': 'Verification code sent'
            })


        
        # Return form errors
        all_errors = []
        for field, errors in user_form.errors.items():
            all_errors.extend(errors)
        for field, errors in profile_form.errors.items():
            all_errors.extend(errors)
        error_message = all_errors[0] if all_errors else 'Please correct the form errors.'
        return JsonResponse({'error': error_message}, status=400)

    else:
        user_form = UserRegistrationForm()
        profile_form = ShopOwnerRegistrationForm()

    return render(request, 'accounts/register_shop.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


#*****************************************
# Verification code handling
def verify_code(request):
    email = request.GET.get('email') or request.POST.get('email')
    if not email:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Email parameter missing'}, status=400)
        return render(request, 'accounts/verify.html', {'error': 'Email parameter missing'})

    if request.method == 'POST':
        code = request.POST.get('code')
        if not code or len(code) != 6:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Valid 6-digit code is required'}, status=400)
            return render(request, 'accounts/verify.html', {
                'email': email, 
                'error': 'Valid 6-digit code is required'
            })

        try:
            pending = PendingUser.objects.get(email=email)
            if pending.verification_code == code:
                if pending.is_expired():
                    error_msg = 'Verification code has expired. Please request a new one.'
                else:
                    # Create actual user
                    user = User.objects.create_user(
                        email=pending.email,
                        password=pending.password,
                        first_name=pending.first_name,
                        last_name=pending.last_name,
                        is_customer=pending.user_type == 'customer',
                        is_shop_owner=pending.user_type == 'shop',
                        is_approved=pending.user_type != 'shop'
                    )
                    
                    # Create profile
                    if pending.user_type == 'customer':
                        CustomerProfile.objects.create(user=user, **pending.profile_data)
                        login(request, user)
                        # For customers, redirect with user_type
                        return redirect(reverse('accounts:verify_success') + '?user_type=customer')
                    else:
                        ShopOwnerProfile.objects.create(user=user, is_approved=False, **pending.profile_data)
                        # For shop owners, redirect with user_type
                        return redirect(reverse('accounts:verify_success') + '?user_type=shop')

                    pending.delete()
            else:
                error_msg = 'Invalid verification code.'
        except PendingUser.DoesNotExist:
            error_msg = 'Verification session expired. Please register again.'

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': error_msg}, status=400)
        return render(request, 'accounts/verify.html', {
            'email': email,
            'error': error_msg
        })

    return render(request, 'accounts/verify.html', {'email': email})





# success page after verification
def verify_success(request):
    user_type = request.GET.get('user_type')
    
    if user_type == 'shop':
        message = "Success! Your account has been created. Please wait for admin approval (usually within 5 hours)."
        show_login = False
    elif user_type == 'customer':
        message = "Your account has been successfully verified. You can now login."
        show_login = True
    else:
        # Fallback for direct access or other cases
        if request.user.is_authenticated:
            if request.user.is_shop_owner and not request.user.shopownerprofile.is_approved:
                message = "Success! Your account has been created. Please wait for admin approval (usually within 5 hours)."
                show_login = False
            else:
                message = "Your account has been successfully verified. You can now login."
                show_login = True
        else:
            return redirect('accounts:login')
    
    return render(request, 'accounts/verify_success.html', {
        'message': message,
        'show_login': show_login
    })


# resend verification code
@require_POST
def resend_verification_code(request):
    email = request.POST.get('email')
    try:
        pending = PendingUser.objects.get(email=email)
        
        # Generate new 6-digit code
        new_code = f"{random.randint(100000, 999999)}"
        pending.verification_code = new_code
        pending.created_at = timezone.now()
        pending.save()

        # Send new email
        send_mail(
            subject='Your New ShopSmart Verification Code',
            message=f"Your new verification code is: {new_code} \nPlease enter this code to complete your registration. \nThis code is valid for 15 minutes. If you did not request this, please ignore this email.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

        return JsonResponse({'message': 'A new code has been sent to your email.'}, status=200)
    
    except PendingUser.DoesNotExist:
        return JsonResponse({'error': 'Verification session expired. Please register again.'}, status=400)


#*****************************************
# login and logout views
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            user = form.cleaned_data.get('user')

            if user.is_shop_owner:
                try:
                    if not user.shopownerprofile.is_approved:
                        if is_ajax(request):
                            return JsonResponse({'error': 'Your account is not yet approved by admin.'}, status=403)
                        form.add_error(None, "Your account is not yet approved by admin.")
                        return render(request, 'accounts/login.html', {'form': form})
                except ShopOwnerProfile.DoesNotExist:
                    if is_ajax(request):
                        return JsonResponse({'error': 'Your shop profile is missing. Please contact support.'}, status=400)
                    form.add_error(None, "Your shop profile is missing. Contact support.")
                    return render(request, 'accounts/login.html', {'form': form})

            login(request, user)

            # Updated redirect logic
            # In your login_view function:
            if user.is_shop_owner:
                redirect_url = reverse('shops:dashboard')
            elif user.is_customer:
                redirect_url = reverse('customers:dashboard')  # Using URL name
            else:
                redirect_url = reverse('accounts:profile')

            if is_ajax(request):
                return JsonResponse({
                    'message': 'Welcome back!',
                    'redirect_url': redirect_url
                }, status=200)

            return redirect(redirect_url)

        elif is_ajax(request):
            return JsonResponse({'error': 'Invalid email or password.'}, status=400)

    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('landing:index')
