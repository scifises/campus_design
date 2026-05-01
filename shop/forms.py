from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Product, Review


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 'placeholder': 'email@example.com'
        })
    )
    role = forms.ChoiceField(
        choices=[('buyer', 'Buyer'), ('seller', 'Seller')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='buyer'
    )
    student_id = forms.CharField(
        max_length=20, required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'e.g. S2208001'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role', 'student_id')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Min 8 characters'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Confirm your password'
        })


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'Username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 'placeholder': 'Password'
        })
    )


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('title', 'description', 'image', 'price', 'category')
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g., Cyberpunk UM 2026'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Describe your design...'
            }),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': '0.00',
                'step': '0.01', 'min': '0'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }


class CheckoutForm(forms.Form):
    full_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'Your full name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 'placeholder': 'email@example.com'
        })
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 3, 'placeholder': 'Shipping address'
        })
    )
    phone = forms.CharField(
        max_length=20, required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': '+60 12-345 6789'
        })
    )


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ('rating', 'comment')
        widgets = {
            'rating': forms.Select(
                choices=[(i, f'{i} ⭐') for i in range(1, 6)],
                attrs={'class': 'form-select'}
            ),
            'comment': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Share your thoughts...'
            }),
        }
