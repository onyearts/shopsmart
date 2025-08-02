from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'  # This registers the namespace

urlpatterns = [
    path('register/customer/', views.register_customer, name='register_customer'),
    path('register/shop/', views.register_shop_owner, name='register_shop_owner'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify/', views.verify_code, name='verify'),
    path('verify/success/', views.verify_success, name='verify_success'),
    path('resend-code/', views.resend_verification_code, name='resend_code'),
    # Other settings...
    path('settings/password/', auth_views.PasswordChangeView.as_view(template_name='accounts/password_change.html'), name='password_change'),
    path('settings/password/done/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), name='password_change_done'),
]