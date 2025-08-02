# accounts/utils.py
import random
from django.core.mail import send_mail

def generate_code():
    return str(random.randint(100000, 999999))

def send_verification_email(email, code):
    subject = "Verify your ShopSmart account"
    message = f"Use this 6-digit code to verify your email: {code}"
    from_email = "noreply@shopsmart.com"
    send_mail(subject, message, from_email, [email])
