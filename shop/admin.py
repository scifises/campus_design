from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Sum, Count, F
from .models import User, Product, CartItem, Order, OrderItem, Review, SiteStatistics


# ── 用户管理 ─────────────────────────────────────────────

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role_badge', 'student_id', 'phone', 
                    'is_active', 'total_orders', 'total_spent', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'student_id', 'phone')
    readonly_fields = ('last_login', 'date_joined', 'total_orders', 'total_spent')
    list_per_page = 25
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Campus Info', {
            'fields': ('role', 'student_id', 'phone', 'avatar', 'bio')
        }),
        ('Statistics', {
            'fields': ('total_orders', 'total_spent'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Campus Info', {
            'fields': ('role', 'student_id', 'phone', 'email')
        }),
    )
    
    def role_badge(self, obj):
        colors = {'buyer': '#17a2b8', 'seller': '#28a745', 'admin': '#dc3545'}
        color = colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;border-radius:12px;font-size:12px;">{}</span>',
            color, obj.get_role_display()
        )
    role_badge.short_description = 'Role'
    
    def total_orders(self, obj):
        if obj.role == 'buyer':
            return obj.orders.count()
        elif obj.role == 'seller':
            return obj.sold_items.values('order').distinct().count()
        return '-'
    total_orders.short_description = 'Orders'
    
    def total_spent(self, obj):
        if obj.role == 'buyer':
            result = obj.orders.filter(status__in=['paid', 'completed']).aggregate(t=Sum('total_amount'))
            return f"RM {result['t'] or 0}"
        elif obj.role == 'seller':
            result = obj.sold_items.filter(order__status__in=['paid', 'completed']).aggregate(
                t=Sum(F('price') * F('quantity')))
            return f"RM {result['t'] or 0}"
        return '-'
    total_spent.short_description = 'Amount'
    
    actions = ['activate_users', 'deactivate_users']
    
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"Activated {queryset.count()} users.")
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {queryset.count()} users.")
    deactivate_users.short_description = "Deactivate selected users"


# ── 商品管理 ─────────────────────────────────────────────

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('image_preview', 'title', 'seller', 'price', 'category', 
                    'status_badge', 'total_sales', 'rating', 'is_published', 'created_at')
    list_filter = ('status', 'category', 'is_published', 'created_at')
    search_fields = ('title', 'seller__username', 'description')
    list_per_page = 20
    list_editable = ('price', 'is_published')
    readonly_fields = ('total_sales', 'rating', 'created_at', 'updated_at', 'image_preview_large')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'description', 'seller', 'category')
        }),
        ('Pricing & Image', {
            'fields': ('price', 'image', 'image_preview_large')
        }),
        ('Status', {
            'fields': ('status', 'is_published')
        }),
        ('Statistics', {
            'fields': ('total_sales', 'rating'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:40px;height:40px;object-fit:cover;border-radius:6px;">', obj.image.url)
        return "👕"
    image_preview.short_description = 'Image'
    
    def image_preview_large(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width:200px;max-height:200px;border-radius:8px;">', obj.image.url)
        return "No image"
    image_preview_large.short_description = 'Preview'
    
    def status_badge(self, obj):
        colors = {'pending': '#ffc107', 'approved': '#28a745', 'rejected': '#dc3545'}
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;border-radius:12px;font-size:12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    actions = ['approve_products', 'reject_products']
    
    def approve_products(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, f"Approved {queryset.count()} products.")
    approve_products.short_description = "Approve selected products"
    
    def reject_products(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f"Rejected {queryset.count()} products.")
    reject_products.short_description = "Reject selected products"


# ── 购物车管理 ─────────────────────────────────────────────

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'size', 'quantity', 'subtotal_display', 'added_at')
    list_filter = ('size', 'added_at')
    search_fields = ('user__username', 'product__title')
    list_per_page = 30
    raw_id_fields = ('user', 'product')
    
    def subtotal_display(self, obj):
        return f"RM {obj.subtotal}"
    subtotal_display.short_description = 'Subtotal'


# ── 订单管理 ─────────────────────────────────────────────

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'seller', 'quantity', 'size', 'price', 'subtotal_display')
    fields = ('product', 'seller', 'size', 'quantity', 'price', 'subtotal_display')
    
    def subtotal_display(self, obj):
        return f"RM {obj.subtotal}"
    subtotal_display.short_description = 'Subtotal'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'full_name', 'total_amount', 'item_count', 
                    'status_badge', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('id', 'user__username', 'full_name', 'email', 'phone')
    list_per_page = 20
    readonly_fields = ('created_at', 'updated_at', 'item_count', 'seller_count')
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Info', {
            'fields': ('user', 'status', 'payment_method', 'total_amount')
        }),
        ('Recipient Info', {
            'fields': ('full_name', 'email', 'phone', 'address')
        }),
        ('Additional', {
            'fields': ('notes', 'item_count', 'seller_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107', 'paid': '#17a2b8', 'shipped': '#6f42c1',
            'completed': '#28a745', 'cancelled': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;border-radius:12px;font-size:12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    actions = ['mark_paid', 'mark_shipped', 'mark_completed', 'mark_cancelled']
    
    def mark_paid(self, request, queryset):
        queryset.update(status='paid')
        self.message_user(request, f"Marked {queryset.count()} orders as paid.")
    mark_paid.short_description = "Mark as Paid"
    
    def mark_shipped(self, request, queryset):
        queryset.update(status='shipped')
        self.message_user(request, f"Marked {queryset.count()} orders as shipped.")
    mark_shipped.short_description = "Mark as Shipped"
    
    def mark_completed(self, request, queryset):
        queryset.update(status='completed')
        self.message_user(request, f"Marked {queryset.count()} orders as completed.")
    mark_completed.short_description = "Mark as Completed"
    
    def mark_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, f"Marked {queryset.count()} orders as cancelled.")
    mark_cancelled.short_description = "Mark as Cancelled"


# ── 订单项管理 ─────────────────────────────────────────────

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'seller', 'size', 'quantity', 'price', 'subtotal_display')
    list_filter = ('size', 'order__status')
    search_fields = ('order__id', 'product__title', 'seller__username')
    list_per_page = 30
    raw_id_fields = ('order', 'product', 'seller')
    
    def subtotal_display(self, obj):
        return f"RM {obj.subtotal}"
    subtotal_display.short_description = 'Subtotal'


# ── 评价管理 ─────────────────────────────────────────────

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating_stars', 'comment_preview', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'product__title', 'comment')
    list_per_page = 25
    raw_id_fields = ('user', 'product')
    
    def rating_stars(self, obj):
        return '⭐' * obj.rating
    rating_stars.short_description = 'Rating'
    
    def comment_preview(self, obj):
        if obj.comment:
            return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
        return '-'
    comment_preview.short_description = 'Comment'


# ── 网站统计 ─────────────────────────────────────────────

@admin.register(SiteStatistics)
class SiteStatisticsAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_users', 'new_users', 'total_orders', 
                    'new_orders', 'revenue', 'page_views')
    list_filter = ('date',)
    list_per_page = 30
    readonly_fields = ('date',)
    date_hierarchy = 'date'
    
    def has_add_permission(self, request):
        return False  # 统计数据自动生成，不允许手动添加


# ── Admin Site 配置 ─────────────────────────────────────

admin.site.site_header = 'Campus Design Admin'
admin.site.site_title = 'Campus Design'
admin.site.index_title = 'Management Console'
