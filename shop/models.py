from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class User(AbstractUser):
    """用户模型 - 支持买家、卖家、管理员三种角色"""
    ROLE_CHOICES = (
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
        ('admin', 'Admin'),
    )
    
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES, 
        default='buyer',
        verbose_name='Role'
    )
    student_id = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name='Student ID'
    )
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name='Phone Number'
    )
    avatar = models.ImageField(
        upload_to='avatars/', 
        blank=True, 
        null=True,
        verbose_name='Avatar'
    )
    bio = models.TextField(
        blank=True, 
        default='',
        verbose_name='Bio'
    )
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def total_orders(self):
        """买家订单总数"""
        return self.orders.count()
    
    @property
    def total_spent(self):
        """买家总消费"""
        from django.db.models import Sum
        result = self.orders.filter(
            status__in=['paid', 'completed']
        ).aggregate(total=Sum('total_amount'))
        return result['total'] or 0
    
    @property
    def total_products(self):
        """卖家商品总数"""
        return self.products.count()
    
    @property
    def total_earnings(self):
        """卖家总收入"""
        from django.db.models import Sum, F
        result = self.sold_items.filter(
            order__status__in=['paid', 'completed']
        ).aggregate(total=Sum(F('price') * F('quantity')))
        return result['total'] or 0


class Product(models.Model):
    """商品模型 - 卖家设计的作品"""
    CATEGORY_CHOICES = (
        ('tshirt', 'T-Shirt'),
        ('hoodie', 'Hoodie'),
        ('cap', 'Cap'),
        ('tote', 'Tote Bag'),
        ('other', 'Other'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    title = models.CharField(
        max_length=200,
        verbose_name='Title'
    )
    description = models.TextField(
        blank=True, 
        default='',
        verbose_name='Description'
    )
    seller = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='products',
        verbose_name='Seller'
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name='Price (RM)'
    )
    image = models.ImageField(
        upload_to='products/', 
        blank=True, 
        null=True,
        verbose_name='Image'
    )
    category = models.CharField(
        max_length=20, 
        choices=CATEGORY_CHOICES, 
        default='tshirt',
        verbose_name='Category'
    )
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=1, 
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        verbose_name='Rating'
    )
    total_sales = models.PositiveIntegerField(
        default=0,
        verbose_name='Total Sales'
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name='Published'
    )
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='Status'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - RM {self.price}"
    
    @property
    def review_count(self):
        return self.reviews.count()
    
    @property
    def is_available(self):
        return self.status == 'approved' and self.is_published


class CartItem(models.Model):
    """购物车模型"""
    SIZE_CHOICES = (
        ('XS', 'Extra Small'), 
        ('S', 'Small'), 
        ('M', 'Medium'),
        ('L', 'Large'), 
        ('XL', 'Extra Large'), 
        ('XXL', '2X Large'),
    )
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='cart_items',
        verbose_name='User'
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        verbose_name='Product'
    )
    size = models.CharField(
        max_length=5, 
        choices=SIZE_CHOICES, 
        default='M',
        verbose_name='Size'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name='Quantity'
    )
    added_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Added At'
    )

    class Meta:
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        unique_together = ('user', 'product', 'size')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} - {self.product.title} ({self.size}) x{self.quantity}"

    @property
    def subtotal(self):
        return self.product.price * self.quantity


class Order(models.Model):
    """订单模型"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_CHOICES = (
        ('online', 'Online Payment'),
        ('cash', 'Cash on Delivery'),
        ('transfer', 'Bank Transfer'),
    )

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='orders',
        verbose_name='Buyer'
    )
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name='Total Amount'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='Status'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default='online',
        verbose_name='Payment Method'
    )
    full_name = models.CharField(
        max_length=200, 
        default='',
        verbose_name='Recipient Name'
    )
    email = models.EmailField(
        default='',
        verbose_name='Email'
    )
    address = models.TextField(
        default='',
        verbose_name='Shipping Address'
    )
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        default='',
        verbose_name='Phone'
    )
    notes = models.TextField(
        blank=True, 
        default='',
        verbose_name='Order Notes'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} — {self.user.username} — RM {self.total_amount}"
    
    @property
    def item_count(self):
        return self.items.count()
    
    @property
    def seller_count(self):
        return self.items.values('seller').distinct().count()


class OrderItem(models.Model):
    """订单项模型"""
    SIZE_CHOICES = CartItem.SIZE_CHOICES

    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name='Order'
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        verbose_name='Product'
    )
    seller = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sold_items',
        verbose_name='Seller'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name='Quantity'
    )
    size = models.CharField(
        max_length=5, 
        choices=SIZE_CHOICES, 
        default='M',
        verbose_name='Size'
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name='Unit Price'
    )

    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'

    def __str__(self):
        return f"{self.product.title} x{self.quantity} ({self.size})"

    @property
    def subtotal(self):
        return self.price * self.quantity


class Review(models.Model):
    """评价模型"""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='reviews',
        verbose_name='User'
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='reviews',
        verbose_name='Product'
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Rating'
    )
    comment = models.TextField(
        blank=True, 
        default='',
        verbose_name='Comment'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )

    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} — {self.product.title}: {self.rating}⭐"


class SiteStatistics(models.Model):
    """网站统计数据（用于管理员仪表板）"""
    date = models.DateField(
        unique=True,
        verbose_name='Date'
    )
    total_users = models.PositiveIntegerField(
        default=0,
        verbose_name='Total Users'
    )
    new_users = models.PositiveIntegerField(
        default=0,
        verbose_name='New Users'
    )
    total_orders = models.PositiveIntegerField(
        default=0,
        verbose_name='Total Orders'
    )
    new_orders = models.PositiveIntegerField(
        default=0,
        verbose_name='New Orders'
    )
    revenue = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        verbose_name='Revenue'
    )
    page_views = models.PositiveIntegerField(
        default=0,
        verbose_name='Page Views'
    )

    class Meta:
        verbose_name = 'Site Statistics'
        verbose_name_plural = 'Site Statistics'
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} — Users: {self.total_users}, Orders: {self.total_orders}"
