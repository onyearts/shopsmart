# accounts/utils.py
import random
from django.core.mail import send_mail

def generate_code():
    return str(random.randint(100000, 999999))

