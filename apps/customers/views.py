import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST

from accounts.models import User     # assuming shop owners are in User model
from django.db.models import Count
from shops.models import Product
from .models import Wishlist
from .models import Wishlist, Review
from .forms import ReviewForm

@login_required
def customers_dashboard(request):
    if not request.user.is_customer:
        return redirect('accounts:login')

    total_products = Product.objects.count()
    total_shops = User.objects.filter(is_shop_owner=True).count()

    # Recently added products (limit to 5)
    recent_products = Product.objects.order_by('-created_at')[:5]

    # Shop owners with most products
    top_shops = (
    User.objects.filter(is_shop_owner=True)
    .annotate(product_count=Count('shopownerprofile__products'))
    .order_by('-product_count')[:5]
    )



    context = {
        'total_products': total_products,
        'total_shops': total_shops,
        'recent_products': recent_products,
        'top_shops': top_shops,
    }
    return render(request, 'customers/dashboard.html', context)



def product_list(request):
    qs = Product.objects.filter(is_active=True).select_related('shop_owner')
    paginator = Paginator(qs.order_by('-id'), 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Get wishlist product IDs if user is authenticated
    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_product_ids = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)

    return render(request, 'customers/products.html', {
        'products': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'wishlist_product_ids': list(wishlist_product_ids),  # 👈 this is what was missing
    })


@login_required
def submit_review(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review, created = Review.objects.update_or_create(
                user=request.user,
                product=product,
                defaults=form.cleaned_data
            )
    return redirect('customers:product_detail', pk=pk)

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    review_form = ReviewForm()
    
    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_product_ids = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)

    related_products = Product.objects.filter(
        shop_owner=product.shop_owner
    ).exclude(pk=product.pk).order_by('?')[:4]

    return render(request, 'customers/product_detail.html', {
        'product': product,
        'wishlist_product_ids': list(wishlist_product_ids),
        'related_products': related_products,
        'review_form': review_form
    })



@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)

    # Check if current product is in wishlist
    in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()

    # Get 4 related products (same shop owner)
    related_products = Product.objects.filter(
        shop_owner=product.shop_owner
    ).exclude(pk=product.pk).order_by('?')[:4]

    # Get wishlist product IDs (to highlight related product hearts)
    wishlist_product_ids = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)

    return render(request, 'customers/product_detail.html', {
        'product': product,
        'in_wishlist': in_wishlist,
        'related_products': related_products,
        'wishlist_product_ids': list(wishlist_product_ids),  # for related products
    })


@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'customers/wishlist.html', {
        'wishlist_items': items
    })


@require_POST
def add_wishlist(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=403)

    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        if not product_id:
            return JsonResponse({'error': 'Product ID required'}, status=400)

        product = Product.objects.get(pk=product_id)
        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)

        if not created:
            wishlist_item.delete()
            return JsonResponse({'message': 'Removed from wishlist'})
        else:
            return JsonResponse({'message': 'Added to wishlist'})
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)




@login_required
def remove_wishlist(request, pk):
    product = get_object_or_404(Product, pk=pk)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    messages.success(request, 'Removed from wishlist')
    return redirect('customers:wishlist')