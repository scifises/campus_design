from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum, Count, F
from django.core.paginator import Paginator
from decimal import Decimal

from .models import Product, CartItem, Order, OrderItem, User, Review
from .forms import (
    RegisterForm, LoginForm, ProductForm, CheckoutForm, ReviewForm
)


def _cart_count(user):
    if user.is_authenticated:
        return user.cart_items.aggregate(t=Sum('quantity'))['t'] or 0
    return 0


def _cart_items(user):
    if user.is_authenticated:
        return CartItem.objects.filter(user=user).select_related('product')
    return CartItem.objects.none()


def _cart_total(user):
    return sum(i.subtotal for i in _cart_items(user))


def index(request):
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()

    products = Product.objects.filter(
        status='approved', is_published=True
    ).select_related('seller')

    if query:
        products = products.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(seller__username__icontains=query)
        )
    if category:
        products = products.filter(category=category)

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'index.html', {
        'products': page_obj,
        'page_obj': page_obj,
        'query': query,
        'category': category,
        'cat_choices': Product.CATEGORY_CHOICES,
        'cart_count': _cart_count(request.user),
        'active_page': 'browse',
    })


def product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.select_related('seller'),
        pk=pk, status='approved', is_published=True
    )
    reviews = product.reviews.select_related('user').order_by('-created_at')
    review_form = ReviewForm()
    user_has_reviewed = False
    if request.user.is_authenticated:
        user_has_reviewed = Review.objects.filter(
            user=request.user, product=product
        ).exists()

    related_products = Product.objects.filter(
        seller=product.seller, status='approved', is_published=True
    ).exclude(pk=pk)[:4]

    return render(request, 'product_detail.html', {
        'product': product,
        'reviews': reviews,
        'review_form': review_form,
        'user_has_reviewed': user_has_reviewed,
        'related_products': related_products,
        'cart_count': _cart_count(request.user),
        'active_page': 'browse',
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect(request.GET.get('next', 'index'))
        messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form, 'active_page': 'login'})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to Campus Design, {user.username}!')
            return redirect('index')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form, 'active_page': 'register'})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('index')


@login_required
def cart_view(request):
    items = _cart_items(request.user)
    total = _cart_total(request.user)
    form = CheckoutForm(initial={
        'full_name': request.user.get_full_name() or request.user.username,
        'email': request.user.email,
    })
    return render(request, 'cart.html', {
        'cart_items': items,
        'total': total,
        'cart_count': _cart_count(request.user),
        'form': form,
        'active_page': 'cart',
    })


@login_required
def add_to_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        size = request.POST.get('size', 'M')
        quantity = int(request.POST.get('quantity', 1))
        product = get_object_or_404(
            Product, pk=product_id, status='approved', is_published=True
        )
        item, created = CartItem.objects.get_or_create(
            user=request.user, product=product, size=size,
            defaults={'quantity': quantity}
        )
        if not created:
            item.quantity += quantity
            item.save()
        messages.success(request, f'"{product.title}" added to cart!')
        nxt = request.POST.get('next', '')
        if nxt:
            return redirect(nxt)
        return redirect('index')
    return redirect('index')


@login_required
def update_cart(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(CartItem, pk=item_id, user=request.user)
        qty = int(request.POST.get('quantity', 1))
        if qty <= 0:
            item.delete()
            messages.info(request, 'Item removed from cart.')
        else:
            item.quantity = qty
            item.save()
    return redirect('cart')


@login_required
def remove_from_cart(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(CartItem, pk=item_id, user=request.user)
        name = item.product.title
        item.delete()
        messages.info(request, f'"{name}" removed from cart.')
    return redirect('cart')


@login_required
def checkout(request):
    if request.method != 'POST':
        return redirect('cart')
    items = _cart_items(request.user)
    if not items.exists():
        messages.warning(request, 'Your cart is empty!')
        return redirect('cart')
    form = CheckoutForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Please fill in all required fields.')
        return redirect('cart')
    order = Order.objects.create(
        user=request.user,
        total_amount=_cart_total(request.user),
        status='paid',
        full_name=form.cleaned_data['full_name'],
        email=form.cleaned_data['email'],
        address=form.cleaned_data['address'],
        phone=form.cleaned_data.get('phone', ''),
    )
    for item in items:
        OrderItem.objects.create(
            order=order, product=item.product,
            seller=item.product.seller,
            quantity=item.quantity, size=item.size,
            price=item.product.price,
        )
        Product.objects.filter(pk=item.product.pk).update(
            total_sales=F('total_sales') + item.quantity
        )
    items.delete()
    messages.success(request, 'Order placed successfully!')
    return redirect('order_success', order_id=order.id)


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    return render(request, 'order_success.html', {
        'order': order,
        'cart_count': _cart_count(request.user),
        'active_page': 'order',
    })

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related(
        'items__product', 'items__seller'
    )
    return render(request, 'order_history.html', {
        'orders': orders,
        'cart_count': _cart_count(request.user),
        'active_page': 'orders',
    })


@login_required
def add_review(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=pk, status='approved')
        if Review.objects.filter(user=request.user, product=product).exists():
            messages.warning(request, 'You have already reviewed this product.')
            return redirect('product_detail', pk=pk)
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.save()
            avg = product.reviews.aggregate(a=Sum('rating') / Count('id'))['a']
            Product.objects.filter(pk=pk).update(rating=round(avg, 1))
            messages.success(request, 'Review submitted!')
        else:
            messages.error(request, 'Invalid review data.')
    return redirect('product_detail', pk=pk)


def _is_seller(u):
    return u.is_authenticated and u.role == 'seller'


@login_required
@user_passes_test(_is_seller, login_url='/')
def seller_dashboard(request):
    products = Product.objects.filter(seller=request.user)
    total_earnings = OrderItem.objects.filter(
        seller=request.user,
        order__status__in=['paid', 'shipped', 'completed']
    ).aggregate(t=Sum(F('price') * F('quantity')))['t'] or 0
    items_sold = OrderItem.objects.filter(
        seller=request.user
    ).aggregate(t=Sum('quantity'))['t'] or 0
    return render(request, 'seller/dashboard.html', {
        'products': products,
        'total_earnings': total_earnings,
        'items_sold': items_sold,
        'active_page': 'seller',
    })


@login_required
@user_passes_test(_is_seller, login_url='/')
def upload_design(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.status = 'pending'
            product.save()
            messages.success(request, 'Design submitted for approval!')
            return redirect('seller_dashboard')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm()
    return render(request, 'seller/upload.html', {
        'form': form,
        'active_page': 'seller',
    })


@login_required
@user_passes_test(_is_seller, login_url='/')
def seller_inventory(request):
    products = Product.objects.filter(seller=request.user)
    return render(request, 'seller/inventory.html', {
        'products': products,
        'active_page': 'seller',
    })


@login_required
@user_passes_test(_is_seller, login_url='/')
def edit_design(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Design updated!')
            return redirect('seller_inventory')
    else:
        form = ProductForm(instance=product)
    return render(request, 'seller/upload.html', {
        'form': form,
        'editing': True,
        'product': product,
        'active_page': 'seller',
    })


@login_required
@user_passes_test(_is_seller, login_url='/')
def unpublish_design(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=pk, seller=request.user)
        product.is_published = not product.is_published
        product.save()
        w = 'published' if product.is_published else 'unpublished'
        messages.info(request, f'Design has been {w}.')
    return redirect('seller_inventory')


def _is_admin(u):
    return u.is_authenticated and u.role == 'admin'


@login_required
@user_passes_test(_is_admin, login_url='/')
def admin_management(request):
    tab = request.GET.get('tab', 'users')
    return render(request, 'admin_panel/management.html', {
        'users': User.objects.all().order_by('-date_joined'),
        'pending_products': Product.objects.filter(
            status='pending').select_related('seller'),
        'all_products': Product.objects.all().select_related('seller'),
        'orders': Order.objects.all().select_related('user'),
        'tab': tab,
        'total_users': User.objects.count(),
        'total_orders': Order.objects.count(),
        'total_revenue': Order.objects.filter(
            status__in=['paid', 'completed']
        ).aggregate(t=Sum('total_amount'))['t'] or 0,
        'active_page': 'admin',
    })


@login_required
@user_passes_test(_is_admin, login_url='/')
def approve_design(request, pk):
    if request.method == 'POST':
        p = get_object_or_404(Product, pk=pk)
        p.status = 'approved'
        p.save()
        messages.success(request, f'"{p.title}" approved!')
    return redirect('admin_management')


@login_required
@user_passes_test(_is_admin, login_url='/')
def reject_design(request, pk):
    if request.method == 'POST':
        p = get_object_or_404(Product, pk=pk)
        p.status = 'rejected'
        p.save()
        messages.info(request, f'"{p.title}" rejected.')
    return redirect('admin_management')


@login_required
@user_passes_test(_is_admin, login_url='/')
def toggle_user_active(request, pk):
    if request.method == 'POST':
        u = get_object_or_404(User, pk=pk)
        u.is_active = not u.is_active
        u.save()
        w = 'activated' if u.is_active else 'deactivated'
        messages.info(request, f'User "{u.username}" {w}.')
    return redirect('admin_management')
