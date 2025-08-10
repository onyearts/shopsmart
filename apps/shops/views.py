from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import ProductForm
from accounts.models import ShopOwnerProfile
from django.http import JsonResponse 
from .models import Product
from .forms import EditUserForm, EditShopOwnerForm, EditCustomerForm
from django.contrib import messages
from django.db.models import Q



@login_required
def shop_search(request):
    if not request.user.is_shop_owner:
        return redirect('accounts:login')

    query = request.GET.get('q', '')
    products = Product.objects.filter(shop_owner=request.user.shopownerprofile)
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(extra_note__icontains=query)
        ).order_by('-created_at')

    return render(request, 'shop/search_results.html', {
        'products': products,
        'query': query
    })

@login_required
def shop_search_suggestions(request):
    if not request.user.is_shop_owner:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    query = request.GET.get('q', '')
    suggestions = []
    
    if query and len(query) >= 2:
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query),
            shop_owner=request.user.shopownerprofile
        ).order_by('name')[:5]
        
        suggestions = [product.name for product in products]
    
    return JsonResponse({'suggestions': suggestions})


@login_required
def dashboard(request):
    if not request.user.is_shop_owner:
        return redirect('accounts:login')

    shop_owner = request.user.shopownerprofile
    products = Product.objects.filter(shop_owner=shop_owner)
    recent_products = products.order_by('-created_at')[:5]
    
    # Calculate product stats
    active_products = products.filter(is_active=True)
    low_stock_products = active_products.filter(stock__lte=5, stock__gt=0)
    out_of_stock_products = active_products.filter(stock=0)
    
    # Calculate percentages for stock overview
    total_active = active_products.count()
    in_stock_count = active_products.filter(stock__gt=5).count()
    low_stock_count = low_stock_products.count()
    out_of_stock_count = out_of_stock_products.count()
    
    in_stock_percentage = 0
    if total_active > 0:
        in_stock_percentage = round((in_stock_count / total_active) * 100)

    # Check for partial refresh request
    if request.GET.get('partial') == 'true':
        data = {
            'total_products': products.count(),
            'active_products': active_products.count(),
            'low_stock_products': low_stock_products.count(),
            'out_of_stock_products': out_of_stock_products.count(),
            'in_stock_count': in_stock_count,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count
        }
        return JsonResponse(data)

    context = {
        'products': products,
        'recent_products': recent_products,
        'active_products': active_products,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'in_stock_count': in_stock_count,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'in_stock_percentage': in_stock_percentage
    }
    return render(request, 'shop/dashboard.html', context)


@login_required
def product_add_edit(request):
    if not request.user.is_shop_owner:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    shop_owner = request.user.shopownerprofile

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.shop_owner = shop_owner
            product.save()
            return JsonResponse({'message': 'Product created successfully'})
        else:
            return JsonResponse({'error': form.errors}, status=400)

    form = ProductForm()
    return render(request, 'shop/product-add-edit.html', {'form': form})

@login_required
def product_list(request):
    if not request.user.is_shop_owner:
        return redirect('accounts:login')

    shop_owner = request.user.shopownerprofile
    products = Product.objects.filter(shop_owner=shop_owner).order_by('-created_at')

    return render(request, 'shop/product-list.html', {'products': products})

@login_required
def product_json(request, pk):
    product = get_object_or_404(Product, pk=pk, shop_owner=request.user.shopownerprofile)
    data = {
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': str(product.price),
        'stock': product.stock,
        'extra_note': product.extra_note,
        'is_active': product.is_active,
        'image_url': product.image.url if product.image else ''
    }
    return JsonResponse(data)

@login_required
def product_edit(request, pk):
    shop_owner = request.user.shopownerprofile
    product = get_object_or_404(Product, pk=pk, shop_owner=shop_owner)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('shops:product_list')
    else:
        form = ProductForm(instance=product)

    return render(request, 'shop/product-add-edit.html', {'form': form})


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, shop_owner=request.user.shopownerprofile)
    product.delete()
    return redirect('shops:product_list')

@login_required
def edit_profile(request):
    user = request.user
    is_shop = user.is_shop_owner
    profile = user.shopownerprofile if is_shop else user.customerprofile

    if request.method == 'POST':
        user_form = EditUserForm(request.POST, request.FILES, instance=user)
        profile_form = EditShopOwnerForm(request.POST, instance=profile) if is_shop else EditCustomerForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()

            # If it's an AJAX request (from Axios or fetch)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'message': 'Profile updated successfully'}, status=200)

            messages.success(request, "Profile updated successfully.")
            return redirect('shops:profile')

        # If form errors and it's an AJAX request
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            errors = {**user_form.errors.get_json_data(), **profile_form.errors.get_json_data()}
            return JsonResponse({'errors': errors}, status=400)

    else:
        user_form = EditUserForm(instance=user)
        profile_form = EditShopOwnerForm(instance=profile) if is_shop else EditCustomerForm(instance=profile)

    return render(request, 'shop/edit-profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'is_shop_owner': is_shop
    })


@login_required
def profile(request):
    try:
        profile = (
            request.user.shopownerprofile
            if request.user.is_shop_owner
            else request.user.customerprofile
        )
    except:
        profile = None

    return render(request, 'shop/profile.html', {'profile': profile})


# this is the functionality for the settings page in shop app
@login_required
def settings_view(request):
    return render(request, 'shop/settings.html')

from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'message': 'Password changed successfully'}, status=200)

            messages.success(request, 'Your password was successfully updated!')
            return redirect('shops:profile')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                error_list = form.errors.get_json_data()
                first_error = next(iter(error_list.values()))[0]['message']
                return JsonResponse({'error': first_error}, status=400)
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'shop/password_change.html', {'form': form})
