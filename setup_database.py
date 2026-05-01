import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus_design.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from decimal import Decimal
from shop.models import User, Product, CartItem, Order, OrderItem, Review

print("=" * 60)
print("  Campus Design — Database Initializer")
print("=" * 60)

if User.objects.exists():
    ans = input("\nData exists. Clear & rebuild? (y/N): ").strip().lower()
    if ans == 'y':
        Review.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        CartItem.objects.all().delete()
        Product.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        print("Data cleared.\n")
    else:
        print("Cancelled.")
        sys.exit()

print("Creating users...")
admin = User.objects.create_user(
    username='admin', email='admin@campusdesign.com',
    password='admin123', role='admin', is_staff=True, is_superuser=True)
print(f"  admin / admin123 (Admin)")

s1 = User.objects.create_user(
    username='yvonne', email='yvonne@student.um.edu.my',
    password='seller123', role='seller', student_id='S2208001',
    phone='+60 12-345 6789', first_name='Yvonne', last_name='Luo')
print(f"  yvonne / seller123 (Seller)")

s2 = User.objects.create_user(
    username='choonmin', email='choonmin@student.um.edu.my',
    password='seller123', role='seller', student_id='S2208002',
    phone='+60 16-789 0123', first_name='Cheong Choon', last_name='Min')
print(f"  choonmin / seller123 (Seller)")

b1 = User.objects.create_user(
    username='alice', email='alice@student.um.edu.my',
    password='buyer123', role='buyer', student_id='S2208003')
print(f"  alice / buyer123 (Buyer)")

print("\nCreating products...")
data = [
    ('Pop Art Doodles', 'Colorful pop art inspired doodles on a white tee. Features quirky birds and bold colors.',
     s1, Decimal('35.00'), 'products/shirt1.jpg', 'tshirt', Decimal('4.9'), 20, True, 'approved'),
    ('Abstract Line Art', 'Minimalist abstract line art design. Clean and modern aesthetic.',
     s2, Decimal('64.00'), 'products/shirt2.jpg', 'tshirt', Decimal('4.8'), 15, True, 'approved'),
    ('Cyber Design', 'Futuristic cyber-themed artwork with neon accents.',
     s1, Decimal('35.00'), 'products/shirt1.jpg', 'tshirt', Decimal('4.5'), 20, True, 'approved'),
    ('Campus Sunset Hoodie', 'Beautiful campus sunset scene printed on premium cotton hoodie.',
     s2, Decimal('55.00'), None, 'hoodie', Decimal('0.0'), 0, False, 'pending'),
    ('Minimalism Cap', 'Simple and elegant cap with minimal geometric design.',
     s1, Decimal('25.00'), None, 'cap', Decimal('0.0'), 0, True, 'approved'),
    ('Art Tote Bag', 'Tote bag featuring original student artwork.',
     s2, Decimal('30.00'), None, 'tote', Decimal('0.0'), 0, True, 'approved'),
]
created = []
for title, desc, seller, price, img, cat, rat, sales, pub, st in data:
    p = Product.objects.create(title=title, description=desc, seller=seller,
        price=price, image=img, category=cat, rating=rat, total_sales=sales,
        is_published=pub, status=st)
    created.append(p)
    icon = "approved" if st == 'approved' else "pending"
    print(f"  {title} — RM {price} [{icon}]")

print("\nCreating reviews...")
Review.objects.create(user=b1, product=created[0], rating=5, comment='Love the design!')
Review.objects.create(user=b1, product=created[1], rating=4, comment='Very clean design.')
Review.objects.create(user=s1, product=created[1], rating=5, comment='Bought for a friend.')

print("\nCreating sample order...")
order = Order.objects.create(user=b1, total_amount=Decimal('99.00'), status='paid',
    full_name='Alice Wong', email='alice@student.um.edu.my',
    address='Block A, Room 301, University Malaya, 50603 KL', phone='+60 11-234 5678')
OrderItem.objects.create(order=order, product=created[0], seller=s1, quantity=1, size='M', price=Decimal('35.00'))
OrderItem.objects.create(order=order, product=created[2], seller=s1, quantity=1, size='L', price=Decimal('35.00'))
OrderItem.objects.create(order=order, product=created[1], seller=s2, quantity=1, size='M', price=Decimal('64.00'))
print(f"  Order #{order.id} — RM {order.total_amount}")

print("\n" + "=" * 60)
print("  DONE!")
print("=" * 60)
print(f"""
  Users:      {User.objects.count()}
  Products:   {Product.objects.count()}
  Reviews:    {Review.objects.count()}
  Orders:     {Order.objects.count()}

  Test accounts:
    admin     / admin123   (Admin)
    yvonne    / seller123  (Seller)
    choonmin  / seller123  (Seller)
    alice     / buyer123   (Buyer)

  Next: python manage.py runserver
""")
