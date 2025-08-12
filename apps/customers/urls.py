from django.urls import path
from . import views  

app_name = 'customers'  # This registers the namespace

urlpatterns = [
    path('dashboard/', views.customers_dashboard, name='dashboard'),
    path('products/', views.product_list, name='product_list'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/', views.add_wishlist, name='add_wishlist'),
    path('wishlist/remove/', views.remove_wishlist, name='remove_wishlist'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('product/<int:pk>/review/', views.submit_review, name='submit_review'),
    path('search-suggestions/', views.search_suggestions, name='search_suggestions'),

    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
]