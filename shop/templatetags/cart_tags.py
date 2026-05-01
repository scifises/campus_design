from django import template
from django.db.models import Sum

register = template.Library()


@register.simple_tag
def cart_item_count(user):
    try:
        if user.is_authenticated and hasattr(user, 'cart_items'):
            return user.cart_items.aggregate(total=Sum('quantity'))['total'] or 0
    except Exception:
        pass
    return 0
