from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from datetime import timedelta
from django.core.validators import RegexValidator

# Import or define send_verification_email
from django.core.mail import send_mail

def send_verification_email(email, code):
    subject = "Your Verification Code"
    message = f"Your verification code is: {code}"
    from_email = "no-reply@example.com"
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)


# Add this validator at the top of your models.py
phone_validator = RegexValidator(
    regex=r'^(0\d{9}|\+233\d{9})$',  # Updated regex
    message="Phone number must be 10 digits starting with 0 (e.g., 0241234567) or 12 digits with +233 (e.g., +233241234567)"
)


def format_ghana_phone_number(phone):
    """Convert a 10-digit Ghanaian phone number to +233 format"""
    if not phone:
        return None
    phone = str(phone).strip()
    if phone.startswith('0') and len(phone) == 10:
        return f"+233{phone[1:]}"
    elif phone.startswith('233') and len(phone) == 12:
        return f"+{phone}"
    elif phone.startswith('+233') and len(phone) == 13:
        return phone
    return None

class PendingUser(models.Model):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    password = models.CharField(max_length=255)  # hashed password
    user_type = models.CharField(max_length=10, choices=(('customer', 'Customer'), ('shop', 'Shop')))
    profile_data = models.JSONField()
    verification_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    verification_sent_at = models.DateTimeField(auto_now_add=True)  # Track when verification was last sent

    def is_expired(self):
        """Check if verification code has expired (15 minutes)"""
        return timezone.now() > self.created_at + timedelta(minutes=15)
    
    def should_cleanup(self):
        """Check if record should be deleted (24 hours after creation)"""
        return timezone.now() > self.created_at + timedelta(hours=24)

    def resend_verification(self):
        """Resend verification code and update timestamp"""
        self.verification_sent_at = timezone.now()
        self.save()
        send_verification_email(self.email, self.verification_code)

    @classmethod
    def cleanup_expired(cls):
        """Delete all pending users that should be cleaned up"""
        expiration_time = timezone.now() - timedelta(hours=24)
        expired_users = cls.objects.filter(created_at__lt=expiration_time)
        count = expired_users.count()
        expired_users.delete()
        return count

    def __str__(self):
        return f"Pending {self.user_type} - {self.email} (Expires: {self.verification_sent_at + timedelta(minutes=15)})"


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)

        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')
        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None  # Disable username field
    email = models.EmailField(unique=True)

    is_shop_owner = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pics/', default='default-user.png')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email


class ShopOwnerProfile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='shopownerprofile'
    )
    shop_name = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(
        max_length=10,
        validators=[phone_validator],
        unique=True
    )
    postal_code = models.CharField(max_length=10, blank=True, null=True)  # NEW
    city = models.CharField(max_length=100, blank=True, null=True) 
    map_address = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.shop_name} ({self.user.get_full_name()})"

    class Meta:
        verbose_name = 'Shop Owner Profile'
        verbose_name_plural = 'Shop Owner Profiles'

    def save(self, *args, **kwargs):
        self.phone = format_ghana_phone_number(self.phone)
        super().save(*args, **kwargs)

    def get_phone_display(self):
        if not self.phone:
            return "Not provided"
        return f"{self.phone[:4]} {self.phone[4:6]} {self.phone[6:9]} {self.phone[9:]}"

    def get_whatsapp_link(self):
        if not self.phone:
            return None
        return f"https://wa.me/{self.phone.replace('+', '')}"


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='customerprofile'
    )
    phone = models.CharField(
        max_length=10,
        validators=[phone_validator],
        unique=True
    )
    preferred_location = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"

    class Meta:
        verbose_name = 'Customer Profile'
        verbose_name_plural = 'Customer Profiles'
    
    def save(self, *args, **kwargs):
        self.phone = format_ghana_phone_number(self.phone)
        super().save(*args, **kwargs)

    def get_phone_display(self):
        if not self.phone:
            return "Not provided"
        return f"{self.phone[:4]} {self.phone[4:6]} {self.phone[6:9]} {self.phone[9:]}"

    def get_whatsapp_link(self):
        if not self.phone:
            return None
        return f"https://wa.me/{self.phone.replace('+', '')}"