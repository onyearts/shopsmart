from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.core.mail import send_mail, EmailMessage
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
import logging

logger = logging.getLogger(__name__)

def is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest' or \
           request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

def send_verification_email(email, code):
    try:
        subject = 'Verify Your Email - ShopSmart'
        message = f'''
        Your ShopSmart verification code is: 
        
        {code}
        
        Please enter this code to complete your registration.
        This code is valid for 15 minutes.
        
        If you did not request this, please ignore this email.
        '''
        
        email_message = EmailMessage(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
        )
        email_message.extra_headers = {
            'Reply-To': settings.DEFAULT_FROM_EMAIL,
            'X-Priority': '3',
        }
        result = email_message.send(fail_silently=False)
        logger.info(f"Verification email sent to {email} with code {code}, result: {result}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {email}: {str(e)}")
        return False

def register_customer(request):
    if request.method == 'POST':
        PendingUser.cleanup_expired()
        
        user_form = UserRegistrationForm(request.POST)
        profile_form = CustomerRegistrationForm(request.POST)   

        if user_form.is_valid() and profile_form.is_valid():
            email = user_form.cleaned_data['email'].strip().lower()

            # Existing user check logic remains the same...
            
            # Create profile_data with guaranteed phone
            profile_data = {
                'phone': profile_form.cleaned_data['phone'],  # Already validated
                'preferred_location': profile_form.cleaned_data.get('preferred_location', '')
            }

            # Additional phone validation (redundant but safe)
            if not profile_data['phone'] or not str(profile_data['phone']).startswith('+233'):
                return render(request, 'accounts/register_customer.html', {
                    'user_form': user_form,
                    'profile_form': profile_form,
                    'error': 'Invalid phone number format'
                })

            code = str(random.randint(100000, 999999))
            PendingUser.objects.create(
                email=email,
                first_name=user_form.cleaned_data['first_name'],
                last_name=user_form.cleaned_data['last_name'],
                password=user_form.cleaned_data['password1'],
                user_type='customer',
                profile_data=profile_data,  # Now guaranteed to have phone
                verification_code=code
            )
            if not send_verification_email(email, code):
                return render(request, 'accounts/register_customer.html', {
                    'user_form': user_form,
                    'profile_form': profile_form,
                    'error': 'Failed to send verification email. Please try again later.'
                })

            return redirect(f'/accounts/verify/?email={email}')

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
        PendingUser.cleanup_expired()
        
        user_form = UserRegistrationForm(request.POST)
        profile_form = ShopOwnerRegistrationForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            email = user_form.cleaned_data['email'].strip().lower()
            
            existing_user = User.objects.filter(email__iexact=email).first()
            if existing_user:
                if existing_user.is_active:
                    if is_ajax(request):
                        return JsonResponse({'error': 'Email already in use.'}, status=400)
                    return render(request, 'accounts/register_shop.html', {
                        'user_form': user_form,
                        'profile_form': profile_form,
                        'error': 'Email already in use.'
                    })
                existing_user.delete()
                logger.info(f"Deleted inactive user with email {email} during shop owner registration")
                
            try:
                pending_user = PendingUser.objects.get(email__iexact=email)
                if not pending_user.is_expired():
                    if is_ajax(request):
                        return JsonResponse({
                            'error': 'Verification already sent. Please check your email or wait 15 minutes.',
                            'can_resend': True,
                            'email': email
                        }, status=400)
                    return render(request, 'accounts/register_shop.html', {
                        'user_form': user_form,
                        'profile_form': profile_form,
                        'error': 'Verification already sent. Please check your email or wait 15 minutes.'
                    })
                pending_user.delete()
                logger.info(f"Deleted expired pending user with email {email}")
            except PendingUser.DoesNotExist:
                pass

            profile_data = profile_form.cleaned_data
            logger.info(f"Shop registration profile_data: {profile_data}")  # Added logging
            
            if not profile_data.get('phone') or not profile_data['phone'].startswith('+233'):
                if is_ajax(request):
                    return JsonResponse({'error': 'Invalid phone number. Please provide a valid Ghanaian phone number (e.g., +233241234567).'}, status=400)
                return render(request, 'accounts/register_shop.html', {
                    'user_form': user_form,
                    'profile_form': profile_form,
                    'error': 'Invalid phone number. Please provide a valid Ghanaian phone number (e.g., +233241234567).'
                })

            code = str(random.randint(100000, 999999))
            pending = PendingUser.objects.create(
                email=email,
                first_name=user_form.cleaned_data['first_name'],
                last_name=user_form.cleaned_data['last_name'],
                password=user_form.cleaned_data['password1'],
                user_type='shop',
                profile_data=profile_data,
                verification_code=code
            )
            if not send_verification_email(email, code):
                if is_ajax(request):
                    return JsonResponse({'error': 'Failed to send verification email. Please try again later.'}, status=400)
                return render(request, 'accounts/register_shop.html', {
                    'user_form': user_form,
                    'profile_form': profile_form,
                    'error': 'Failed to send verification email. Please try again later.'
                })

            if is_ajax(request):
                return JsonResponse({
                    'redirect_url': reverse('accounts:verify') + f'?email={email}',
                    'email': email,
                    'message': 'Verification code sent'
                })
            return redirect(f'/accounts/verify/?email={email}')

        all_errors = []
        for field, errors in user_form.errors.items():
            all_errors.extend(errors)
        for field, errors in profile_form.errors.items():
            all_errors.extend(errors)
        error_message = all_errors[0] if all_errors else 'Please correct the form errors.'
        
        if is_ajax(request):
            return JsonResponse({'error': error_message}, status=400)
        return render(request, 'accounts/register_shop.html', {
            'user_form': user_form,
            'profile_form': profile_form,
            'error': error_message
        })

    else:
        user_form = UserRegistrationForm()
        profile_form = ShopOwnerRegistrationForm()

    return render(request, 'accounts/register_shop.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })




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
            pending = PendingUser.objects.get(email__iexact=email.strip().lower())
            if pending.verification_code == code:
                if pending.is_expired():
                    error_msg = 'Verification code has expired. Please request a new one.'
                    pending.delete()
                    logger.info(f"Deleted expired pending user with email {email}")
                else:
                    email_normalized = email.strip().lower()
                    existing_user = User.objects.filter(email__iexact=email_normalized).first()
                    if existing_user:
                        if existing_user.is_active:
                            error_msg = 'This email is already registered and active. Please log in.'
                            pending.delete()
                            logger.info(f"Deleted pending user with email {email} due to active user")
                        else:
                            existing_user.delete()
                            logger.info(f"Deleted inactive user with email {email} to allow re-registration")
                            if User.objects.filter(email__iexact=email_normalized).exists():
                                error_msg = 'Another user with this email exists. Please contact support.'
                                pending.delete()
                                logger.error(f"Multiple users found for email {email}")
                                raise Exception(error_msg)

                    user = User.objects.create_user(
                        email=pending.email,
                        password=pending.password,
                        first_name=pending.first_name,
                        last_name=pending.last_name,
                        is_customer=pending.user_type == 'customer',
                        is_shop_owner=pending.user_type == 'shop',
                        is_approved=pending.user_type != 'shop'
                    )
                    
                    profile_data = pending.profile_data or {}
                    logger.info(f"Creating profile for {email} with data: {profile_data}")

                    if pending.user_type == 'customer':
                        phone = (
                            profile_data.get('phone') 
                            or request.POST.get('phone') 
                            or '+233000000000'
                        )
                        
                        if not isinstance(phone, str) or not phone.startswith('+233'):
                            error_msg = 'Invalid phone number in system records'
                            user.delete()
                            pending.delete()
                            logger.error(f"Phone validation failed for {email}: {phone}")
                            raise Exception(error_msg)

                        try:
                            CustomerProfile.objects.create(
                                user=user,
                                phone=phone,
                                preferred_location=profile_data.get('preferred_location', 'Accra')
                            )
                            login(request, user)
                            pending.delete()
                            return redirect(reverse('accounts:verify_success') + '?user_type=customer')
                        except Exception as e:
                            error_msg = f'Profile creation failed: {str(e)}'
                            logger.error(f"Final creation error for {email}: {str(e)}")
                            user.delete()
                            pending.delete()
                            raise Exception(error_msg)
                    
                    else:  # Shop owner registration
                        phone = (
                            profile_data.get('phone')
                            or request.POST.get('phone')
                            or '+233000000000'
                        )
                        
                        if not isinstance(phone, str) or not phone.startswith('+233'):
                            error_msg = 'Invalid phone number for shop owner'
                            user.delete()
                            pending.delete()
                            logger.error(f"Shop phone validation failed for {email}: {phone}")
                            raise Exception(error_msg)

                        try:
                            ShopOwnerProfile.objects.create(
                                user=user,
                                phone=phone,
                                shop_name=profile_data.get('shop_name', 'New Shop'),
                                address=profile_data.get('address', ''),
                                postal_code=profile_data.get('postal_code', ''),
                                city=profile_data.get('city', ''),
                                is_approved=False
                            )
                            pending.delete()
                            logger.info(f"Created shop owner profile for {email}")
                            return redirect(reverse('accounts:verify_success') + '?user_type=shop')
                        except Exception as e:
                            error_msg = f'Failed to create shop profile: {str(e)}'
                            logger.error(f"Shop profile error for {email}: {str(e)}")
                            user.delete()
                            pending.delete()
                            raise Exception(error_msg)

            else:
                error_msg = 'Invalid verification code.'
        except PendingUser.DoesNotExist:
            error_msg = 'Verification session expired. Please register again.'
            logger.info(f"No pending user found for email {email}")
        except Exception as e:
            error_msg = f'Error during verification: {str(e)}'
            logger.error(f"Verification error for email {email}: {str(e)}")

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': error_msg}, status=400)
        return render(request, 'accounts/verify.html', {
            'email': email,
            'error': error_msg
        })

    return render(request, 'accounts/verify.html', {'email': email})




def verify_success(request):
    user_type = request.GET.get('user_type')
    
    if user_type == 'shop':
        message = "Success! Your account has been created. Please wait for admin approval (usually within 5 hours)."
        show_login = False
    elif user_type == 'customer':
        message = "Your account has been successfully verified. You can now login."
        show_login = True
    else:
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

@require_POST
def resend_verification_code(request):
    email = request.POST.get('email')
    if not email:
        return JsonResponse({'error': 'Email is required'}, status=400)
    
    try:
        pending = PendingUser.objects.get(email__iexact=email.strip().lower())
        if User.objects.filter(email__iexact=email.strip().lower(), is_active=True).exists():
            pending.delete()
            logger.info(f"Deleted pending user with email {email} due to existing active user")
            return JsonResponse({'error': 'This email is already registered and active. Please log in.'}, status=400)
        
        new_code = f"{random.randint(100000, 999999)}"
        pending.verification_code = new_code
        pending.created_at = timezone.now()
        pending.save()

        if not send_verification_email(email, new_code):
            return JsonResponse({'error': 'Failed to send verification email. Please try again later.'}, status=400)

        return JsonResponse({'message': 'A new code has been sent to your email.'}, status=200)
    
    except PendingUser.DoesNotExist:
        return JsonResponse({'error': 'Verification session expired. Please register again.'}, status=400)

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

            if user.is_shop_owner:
                redirect_url = reverse('shops:dashboard')
            elif user.is_customer:
                redirect_url = reverse('customers:dashboard')
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