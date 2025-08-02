from django.urls import path
from . import views

app_name = 'shops'  # This registers the namespace

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('product/add-edit/', views.product_add_edit, name='product_add_edit'),
    path('product/list/', views.product_list, name='product_list'),
    path('product/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('product/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('product/<int:pk>/json/', views.product_json, name='product_json'),
    path('profile/', views.profile, name='profile'),
    path('edit/profile/', views.edit_profile, name='edit_profile'),
    path('change/password/', views.change_password, name='change_password'),
    path('settings/', views.settings_view, name='settings'),
    # other URLs...
]