from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    ROLE_CHOICES = (
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')
    student_id = models.CharField(max_length=20, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Product(models.Model):
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

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='tshirt')
    rating = models.DecimalField(
        max_digits=3, decimal_places=1, default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_sales = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class CartItem(models.Model):
    SIZE_CHOICES = (
        ('XS', 'XS'), ('S', 'S'), ('M', 'M'),
        ('L', 'L'), ('XL', 'XL'), ('XXL', 'XXL'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=5, choices=SIZE_CHOICES, default='M')
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product', 'size')

    def __str__(self):
        return f"{self.user.username} - {self.product.title} ({self.size}) x{self.quantity}"

    @property
    def subtotal(self):
        return self.product.price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    full_name = models.CharField(max_length=200, default='')
    email = models.EmailField(default='')
    address = models.TextField(default='')
    phone = models.CharField(max_length=20, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} — {self.user.username}"


class OrderItem(models.Model):
    SIZE_CHOICES = CartItem.SIZE_CHOICES

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sold_items')
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=5, choices=SIZE_CHOICES, default='M')
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.title} x{self.quantity}"

    @property
    def subtotal(self):
        return self.price * self.quantity


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} — {self.product.title}: {self.rating}⭐"
