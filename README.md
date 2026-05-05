# 🎨 Campus Design

A modern **Student T-shirt Marketplace** built with Django, featuring a complete e-commerce platform for campus creativity.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Django](https://img.shields.io/badge/Django-4.2-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📸 Screenshots

### Homepage
Browse unique designs from campus artists with a clean, modern interface.

### Design Studio
Create your own designs with our built-in canvas editor featuring multiple drawing tools.

## ✨ Features

### 👥 User System
- **Three user roles:** Buyer, Seller, Admin
- User registration and login
- Password reset via email
- User profiles with avatar and bio

### 🛒 E-Commerce
- Product browsing with category filters
- Search functionality
- Shopping cart with size selection
- Order management
- Order history with detailed views
- Product reviews and ratings

### 🎨 Design Studio (For Sellers)
- **HTML5 Canvas drawing board**
- **11 drawing tools:**
  - 🖌️ Brush
  - ✏️ Pencil
  - 🧹 Eraser
  - 📏 Line
  - ⬜ Rectangle
  - ⭕ Circle
  - 🔺 Triangle
  - 🔤 Text
  - 🪣 Fill bucket
  - 💉 Eyedropper
  - 💨 Spray
- Color picker with 12 preset colors
- Custom background color
- Adjustable brush size (1-100px)
- Opacity control (1-100%)
- Text customization (font, size, bold, italic)
- Shape options (fill/stroke)
- Undo/Redo (up to 50 steps)
- Save as PNG / Create product directly

### 👨‍💼 Admin Panel
- **Comprehensive dashboard** with statistics
- **User management:** View all buyers and sellers
- **Product management:** Approve/reject designs
- **Order management:** Track all orders
- **Review management:** Monitor customer feedback
- Search and filter functionality
- Bulk actions

### 📦 Order System
- Buyers can view their order history
- Sellers can view sales records
- Admins can view all orders
- Detailed order information
- Order status tracking

## 🚀 Installation

### Prerequisites
- Python 3.11+
- pip

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/scifises/campus_design.git
cd campus_design
```

2. **Create virtual environment**
```bash
python -m venv .venv
```

3. **Activate virtual environment**
```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

5. **Run migrations**
```bash
python manage.py migrate
```

6. **Create superuser (admin)**
```bash
python manage.py createsuperuser
```

7. **Run the server**
```bash
python manage.py runserver
```

8. **Access the application**
- Website: http://127.0.0.1:8000/
- Admin Panel: http://127.0.0.1:8000/admin/

## 📁 Project Structure

```
campus_design/
├── campus_design/          # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── shop/                   # Main application
│   ├── models.py           # Database models
│   ├── views.py            # View functions
│   ├── urls.py             # URL routing
│   ├── forms.py            # Form classes
│   ├── admin.py            # Admin configuration
│   └── migrations/         # Database migrations
├── templates/              # HTML templates
│   ├── base.html           # Base template
│   ├── index.html          # Homepage
│   ├── seller/             # Seller templates
│   ├── admin_panel/        # Admin templates
│   └── ...
├── media/                  # Uploaded files
│   └── products/           # Product images
├── static/                 # Static files
├── manage.py               # Django management
└── requirements.txt        # Dependencies
```

## 🎯 Usage Guide

### For Buyers
1. Register an account or login
2. Browse products on the homepage
3. Add items to cart with size selection
4. Checkout and complete order
5. View order history in "My Orders"

### For Sellers
1. Register as a seller
2. Access the **Seller Hub** dashboard
3. Use **Design Studio** to create designs
4. Upload designs for approval
5. Track sales in "Sales History"

### For Admins
1. Login with admin credentials
2. Access **Admin Panel** or **Django Admin**
3. Manage users, products, and orders
4. Approve or reject new designs
5. Monitor site statistics

## 🔧 Tech Stack

- **Backend:** Django 4.2
- **Database:** SQLite (development)
- **Frontend:** Bootstrap 5, HTML5 Canvas
- **Image Processing:** Pillow
- **Authentication:** Django built-in auth

## 📊 Database Models

| Model | Description |
|-------|-------------|
| User | Custom user model with roles |
| Product | Designer products with images |
| CartItem | Shopping cart items |
| Order | Customer orders |
| OrderItem | Individual items in orders |
| Review | Product reviews and ratings |
| SiteStatistics | Daily site statistics |

## 🎨 Design Studio Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + Z` | Undo |
| `Ctrl + Shift + Z` | Redo |
| `Ctrl + S` | Save |
| `B` | Brush |
| `P` | Pencil |
| `E` | Eraser |
| `L` | Line |
| `R` | Rectangle |
| `C` | Circle |
| `T` | Text |
| `F` | Fill |
| `I` | Eyedropper |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License.

## 👨‍💻 Author

**scifises** - [GitHub](https://github.com/scifises)

## 🙏 Acknowledgments

- Django community
- Bootstrap team
- Unsplash for demo images

---

**Made with ❤️ for campus creativity**
