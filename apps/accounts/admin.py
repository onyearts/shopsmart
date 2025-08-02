from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import ShopOwnerProfile, CustomerProfile, User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_shop_owner', 'is_customer', 'is_approved')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_shop_owner', 'is_customer', 'is_approved')
    search_fields = ('email', 'first_name', 'last_name')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'profile_picture')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_approved', 'is_shop_owner', 'is_customer', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

    ordering = ('email',)


@admin.register(ShopOwnerProfile)
class ShopOwnerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'shop_name', 'phone', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('user__email', 'shop_name', 'phone')
    list_editable = ('is_approved',)
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_selected', 'disapprove_selected']
    
    def approve_selected(self, request, queryset):
        queryset.update(is_approved=True)
    approve_selected.short_description = "Approve selected shop owners"
    
    def disapprove_selected(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove_selected.short_description = "Disapprove selected shop owners"


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'preferred_location', 'created_at')
    search_fields = ('user__email', 'phone', 'preferred_location')
    readonly_fields = ('created_at', 'updated_at')
    list_filter = ('created_at',)
