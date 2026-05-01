from django.urls import path
from . import views

urlpatterns = [
    path('',                        views.index,            name='index'),
    path('product/<int:pk>/',       views.product_detail,   name='product_detail'),
    path('product/<int:pk>/review/',views.add_review,       name='add_review'),

    path('login/',                  views.login_view,       name='login'),
    path('register/',               views.register_view,    name='register'),
    path('logout/',                 views.logout_view,      name='logout'),

    path('cart/',                   views.cart_view,        name='cart'),
    path('cart/add/',               views.add_to_cart,      name='add_to_cart'),
    path('cart/update/<int:item_id>/',  views.update_cart,      name='update_cart'),
    path('cart/remove/<int:item_id>/',  views.remove_from_cart, name='remove_from_cart'),
    path('checkout/',               views.checkout,         name='checkout'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
    path('orders/', views.order_history, name='order_history'),

    path('seller/',                 views.seller_dashboard, name='seller_dashboard'),
    path('seller/upload/',          views.upload_design,    name='upload_design'),
    path('seller/inventory/',       views.seller_inventory, name='seller_inventory'),
    path('seller/edit/<int:pk>/',   views.edit_design,      name='edit_design'),
    path('seller/unpublish/<int:pk>/', views.unpublish_design, name='unpublish_design'),

    path('management/',             views.admin_management, name='admin_management'),
    path('management/approve/<int:pk>/', views.approve_design, name='approve_design'),
    path('management/reject/<int:pk>/',  views.reject_design,  name='reject_design'),
    path('management/toggle-user/<int:pk>/', views.toggle_user_active, name='toggle_user_active'),
    # 修改密码 + 忘记密码
    path('password-change/', views.password_change_view, name='password_change'),
    path('password-reset/', views.password_reset_view, name='password_reset'),
    path('password-reset/done/', views.password_reset_done_view, name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('password-reset/complete/', views.password_reset_complete_view, name='password_reset_complete'),

]
