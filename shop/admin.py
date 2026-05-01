from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Product, CartItem, Order, OrderItem, Review


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'student_id', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Campus Info', {'fields': ('role', 'student_id', 'phone')}),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'seller', 'price', 'category', 'status',
                    'total_sales', 'is_published', 'created_at')
    list_filter = ('status', 'category', 'is_published')
    search_fields = ('title', 'seller__username')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'size', 'quantity', 'added_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'status', 'created_at')
    list_filter = ('status',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'seller', 'quantity', 'size', 'price')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'created_at')
