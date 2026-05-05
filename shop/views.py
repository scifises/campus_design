from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum, Count, F
from django.core.paginator import Paginator
from django.http import Http404
from decimal import Decimal
from urllib.parse import urlparse

from .models import Product, CartItem, Order, OrderItem, User, Review
from .forms import (
    RegisterForm, LoginForm, ProductForm, CheckoutForm, ReviewForm,
    CustomPasswordChangeForm, CustomPasswordResetForm, CustomSetPasswordForm
)


# ── 辅助函数 ─────────────────────────────────────────────

def _cart_count(user):
    if user.is_authenticated:
        return user.cart_items.aggregate(t=Sum('quantity'))['t'] or 0
    return 0


def _cart_items(user):
    if user.is_authenticated:
        return CartItem.objects.filter(user=user).select_related('product')
    return CartItem.objects.none()


def _cart_total(user):
    """计算购物车总价（服务端验证）"""
    items = _cart_items(user)
    total = Decimal('0.00')
    for item in items:
        if item.product.is_available:  # 只计算上架且审核通过的商品
            total += item.product.price * item.quantity
    return total


def _is_safe_url(url, request):
    """验证重定向URL是否安全（防止开放重定向攻击）"""
    if not url:
        return False
    parsed = urlparse(url)
    # 只允许相对路径或本站URL
    if parsed.netloc and parsed.netloc != request.get_host():
        return False
    return True


# ── 首页 & 商品详情 ─────────────────────────────────────────────

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


# ── 用户认证 ─────────────────────────────────────────────

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


# ── 修改密码 ─────────────────────────────────────────────

@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('index')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'password_change.html', {
        'form': form,
        'active_page': 'password',
    })


# ── 忘记密码 ─────────────────────────────────────────────

def password_reset_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                from_email=None,
                email_template_name='emails/password_reset_email.html',
                subject_template_name='emails/password_reset_subject.txt',
            )
            return redirect('password_reset_done')
    else:
        form = CustomPasswordResetForm()
    return render(request, 'password_reset.html', {
        'form': form,
        'active_page': 'login',
    })


def password_reset_done_view(request):
    return render(request, 'password_reset_done.html', {
        'active_page': 'login',
    })


def password_reset_confirm_view(request, uidb64, token):
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_decode
    from django.contrib.auth import get_user_model

    User = get_user_model()

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = CustomSetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Password reset successfully! Please login.')
                return redirect('password_reset_complete')
        else:
            form = CustomSetPasswordForm(user)
        return render(request, 'password_reset_confirm.html', {
            'form': form,
            'validlink': True,
            'active_page': 'login',
        })
    else:
        return render(request, 'password_reset_confirm.html', {
            'validlink': False,
            'active_page': 'login',
        })


def password_reset_complete_view(request):
    return render(request, 'password_reset_complete.html', {
        'active_page': 'login',
    })


# ── 购物车 ─────────────────────────────────────────────

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
        
        # 【修复】验证 quantity 参数
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity < 1:
                quantity = 1
            elif quantity > 99:
                quantity = 99  # 限制单次添加数量
        except (ValueError, TypeError):
            quantity = 1
        
        # 【修复】验证 size 参数
        valid_sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
        if size not in valid_sizes:
            size = 'M'
        
        product = get_object_or_404(
            Product, pk=product_id, status='approved', is_published=True
        )
        
        # 【修复】检查购物车商品总数限制
        current_count = _cart_count(request.user)
        if current_count + quantity > 999:
            messages.warning(request, 'Cart limit reached! Maximum 999 items.')
            return redirect('product_detail', pk=product_id)
        
        item, created = CartItem.objects.get_or_create(
            user=request.user, product=product, size=size,
            defaults={'quantity': quantity}
        )
        if not created:
            # 【修复】检查单个商品数量上限
            if item.quantity + quantity > 99:
                messages.warning(request, f'Maximum 99 items per product!')
                return redirect('product_detail', pk=product_id)
            item.quantity += quantity
            item.save()
        
        messages.success(request, f'"{product.title}" added to cart!')
        
        # 【修复】验证重定向URL安全性
        nxt = request.POST.get('next', '')
        if nxt and _is_safe_url(nxt, request):
            return redirect(nxt)
        return redirect('index')
    return redirect('index')


@login_required
def update_cart(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(CartItem, pk=item_id, user=request.user)
        
        # 【修复】验证 quantity 参数
        try:
            qty = int(request.POST.get('quantity', 1))
            if qty < 0:
                qty = 0
            elif qty > 99:
                qty = 99
        except (ValueError, TypeError):
            qty = item.quantity
        
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


# ── 结账 & 订单 ─────────────────────────────────────────────

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
        messages.error(request, 'Please fill in all required fields correctly.')
        return redirect('cart')
    
    # 【修复】服务端计算总价，不依赖客户端
    total = _cart_total(request.user)
    if total <= 0:
        messages.error(request, 'Invalid order amount!')
        return redirect('cart')
    
    # 【修复】验证所有商品仍然可用
    for item in items:
        if not item.product.is_available:
            messages.error(request, f'"{item.product.title}" is no longer available!')
            return redirect('cart')
    
    order = Order.objects.create(
        user=request.user,
        total_amount=total,  # 使用服务端计算的金额
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
            price=item.product.price,  # 使用商品当前价格
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


# ── 订单历史 ─────────────────────────────────────────────

@login_required
def order_history(request):
    """买家查看自己的历史订单"""
    orders = Order.objects.filter(user=request.user).prefetch_related(
        'items__product', 'items__seller'
    )
    
    status = request.GET.get('status', '').strip()
    if status and status in dict(Order.STATUS_CHOICES):
        orders = orders.filter(status=status)
    
    paginator = Paginator(orders, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'order_history.html', {
        'orders': page_obj,
        'page_obj': page_obj,
        'status': status,
        'status_choices': Order.STATUS_CHOICES,
        'cart_count': _cart_count(request.user),
        'active_page': 'orders',
    })


@login_required
def order_detail(request, order_id):
    """订单详情 - 权限严格控制"""
    user = request.user
    
    if user.role == 'admin':
        order = get_object_or_404(
            Order.objects.prefetch_related('items__product', 'items__seller', 'user'),
            pk=order_id
        )
    elif user.role == 'seller':
        order = get_object_or_404(
            Order.objects.filter(items__seller=user).distinct()
                .prefetch_related('items__product', 'items__seller', 'user'),
            pk=order_id
        )
    else:
        order = get_object_or_404(
            Order.objects.prefetch_related('items__product', 'items__seller'),
            pk=order_id, user=user
        )
    
    context = {
        'order': order,
        'cart_count': _cart_count(request.user),
        'active_page': 'orders',
    }
    
    if user.role == 'seller':
        seller_items = order.items.filter(seller=user)
        context['seller_items'] = seller_items
        context['seller_total'] = sum(item.subtotal for item in seller_items)
    
    return render(request, 'order_detail.html', context)


# ── 评价 ─────────────────────────────────────────────

@login_required
def add_review(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=pk, status='approved')
        
        # 【修复】禁止卖家评价自己的商品
        if product.seller == request.user:
            messages.warning(request, 'You cannot review your own product!')
            return redirect('product_detail', pk=pk)
        
        if Review.objects.filter(user=request.user, product=product).exists():
            messages.warning(request, 'You have already reviewed this product.')
            return redirect('product_detail', pk=pk)
        
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.save()
            
            # 更新商品评分
            avg = product.reviews.aggregate(a=Sum('rating') / Count('id'))['a']
            Product.objects.filter(pk=pk).update(rating=round(avg, 1))
            messages.success(request, 'Review submitted!')
        else:
            messages.error(request, 'Invalid review data.')
    return redirect('product_detail', pk=pk)


# ── 卖家功能 ─────────────────────────────────────────────

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
def design_studio(request):
    """设计工作室"""
    return render(request, 'seller/design_studio.html', {
        'active_page': 'seller',
    })


@login_required
@user_passes_test(_is_seller, login_url='/')
def seller_order_history(request):
    """卖家查看销售记录"""
    order_items = OrderItem.objects.filter(
        seller=request.user
    ).select_related(
        'order', 'product', 'order__user'
    ).order_by('-order__created_at')
    
    status = request.GET.get('status', '').strip()
    if status and status in dict(Order.STATUS_CHOICES):
        order_items = order_items.filter(order__status=status)
    
    orders_data = {}
    for item in order_items:
        order = item.order
        if order.id not in orders_data:
            orders_data[order.id] = {
                'order': order,
                'items': [],
                'seller_total': 0
            }
        orders_data[order.id]['items'].append(item)
        orders_data[order.id]['seller_total'] += item.subtotal
    
    orders_list = list(orders_data.values())
    
    paginator = Paginator(orders_list, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'seller/order_history.html', {
        'orders_data': page_obj,
        'page_obj': page_obj,
        'status': status,
        'status_choices': Order.STATUS_CHOICES,
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
    
    # 【修复】禁止编辑已有订单的商品（可能导致价格不一致）
    if OrderItem.objects.filter(product=product).exists():
        messages.warning(request, 'Cannot edit products with existing orders!')
        return redirect('seller_inventory')
    
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


# ── 管理员功能 ─────────────────────────────────────────────

def _is_admin(u):
    return u.is_authenticated and u.role == 'admin'


@login_required
@user_passes_test(_is_admin, login_url='/')
def admin_management(request):
    """管理员管理面板"""
    tab = request.GET.get('tab', 'dashboard')
    search = request.GET.get('search', '').strip()
    
    # 统计数据
    total_users = User.objects.count()
    buyer_count = User.objects.filter(role='buyer').count()
    seller_count = User.objects.filter(role='seller').count()
    total_products = Product.objects.count()
    approved_count = Product.objects.filter(status='approved').count()
    pending_count = Product.objects.filter(status='pending').count()
    total_orders = Order.objects.count()
    completed_orders = Order.objects.filter(status='completed').count()
    total_revenue = Order.objects.filter(
        status__in=['paid', 'completed']
    ).aggregate(t=Sum('total_amount'))['t'] or 0
    
    context = {
        'tab': tab,
        'search': search,
        'total_users': total_users,
        'buyer_count': buyer_count,
        'seller_count': seller_count,
        'total_products': total_products,
        'approved_count': approved_count,
        'pending_count': pending_count,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'total_revenue': total_revenue,
        'active_page': 'admin',
    }
    
    if tab == 'dashboard':
        context['recent_users'] = User.objects.all().order_by('-date_joined')[:5]
        context['recent_orders'] = Order.objects.all().select_related('user')[:5]
    
    elif tab == 'users':
        users = User.objects.all().order_by('-date_joined')
        role_filter = request.GET.get('role', '')
        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(student_id__icontains=search)
            )
        if role_filter in ['buyer', 'seller', 'admin']:
            users = users.filter(role=role_filter)
        paginator = Paginator(users, 20)
        context['users'] = paginator.get_page(request.GET.get('page'))
        context['role_filter'] = role_filter
    
    elif tab == 'buyers':
        buyers = User.objects.filter(role='buyer').order_by('-date_joined')
        if search:
            buyers = buyers.filter(
                Q(username__icontains=search) | Q(email__icontains=search)
            )
        paginator = Paginator(buyers, 20)
        context['buyers'] = paginator.get_page(request.GET.get('page'))
    
    elif tab == 'sellers':
        sellers = User.objects.filter(role='seller').order_by('-date_joined')
        if search:
            sellers = sellers.filter(
                Q(username__icontains=search) | Q(email__icontains=search)
            )
        paginator = Paginator(sellers, 20)
        context['sellers'] = paginator.get_page(request.GET.get('page'))
    
    elif tab == 'products':
        products = Product.objects.all().select_related('seller').order_by('-created_at')
        status_filter = request.GET.get('status', '')
        category_filter = request.GET.get('category', '')
        if search:
            products = products.filter(
                Q(title__icontains=search) | Q(seller__username__icontains=search)
            )
        if status_filter in ['pending', 'approved', 'rejected']:
            products = products.filter(status=status_filter)
        if category_filter in dict(Product.CATEGORY_CHOICES):
            products = products.filter(category=category_filter)
        paginator = Paginator(products, 20)
        context['products'] = paginator.get_page(request.GET.get('page'))
        context['status_filter'] = status_filter
        context['category_filter'] = category_filter
    
    elif tab == 'orders':
        orders = Order.objects.all().select_related('user').prefetch_related('items').order_by('-created_at')[:50]
        context['orders'] = orders
    
    elif tab == 'reviews':
        reviews = Review.objects.all().select_related('user', 'product').order_by('-created_at')
        paginator = Paginator(reviews, 20)
        context['reviews'] = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'admin_panel/management.html', context)


@login_required
@user_passes_test(_is_admin, login_url='/')
def admin_order_history(request):
    """管理员订单历史"""
    orders = Order.objects.all().select_related('user').prefetch_related(
        'items__product', 'items__seller'
    ).order_by('-created_at')
    
    status = request.GET.get('status', '').strip()
    if status and status in dict(Order.STATUS_CHOICES):
        orders = orders.filter(status=status)
    
    search = request.GET.get('search', '').strip()
    if search:
        orders = orders.filter(
            Q(id__icontains=search) |
            Q(user__username__icontains=search) |
            Q(full_name__icontains=search)
        )
    
    paginator = Paginator(orders, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(
        status__in=['paid', 'completed']
    ).aggregate(t=Sum('total_amount'))['t'] or 0
    
    return render(request, 'admin_panel/order_history.html', {
        'orders': page_obj,
        'page_obj': page_obj,
        'status': status,
        'search': search,
        'status_choices': Order.STATUS_CHOICES,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
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
        # 【修复】禁止禁用自己
        if u.pk == request.user.pk:
            messages.error(request, 'Cannot disable your own account!')
            return redirect(request.META.get('HTTP_REFERER', 'admin_management'))
        u.is_active = not u.is_active
        u.save()
        w = 'activated' if u.is_active else 'deactivated'
        messages.info(request, f'User "{u.username}" {w}.')
    return redirect(request.META.get('HTTP_REFERER', 'admin_management'))


# ── 404 & 500 错误处理 ─────────────────────────────────────────────

def handler404(request, exception):
    return render(request, 'errors/404.html', status=404)


def handler500(request):
    return render(request, 'errors/500.html', status=500)
