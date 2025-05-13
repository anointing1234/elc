import json
import locale
import random
import string
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO
from PIL import Image

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.html import format_html
from django.utils.safestring import mark_safe


# Set locale for formatting prices and dates
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, 'C')  # Fallback to default locale


class AccountManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not username:
            raise ValueError("User must have a username")
        if not email:
            raise ValueError("User must have an email address")

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)  # Hash the password
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username=None, password=None, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not username:
            username = f"admin_{email.split('@')[0]}"  # Generate a default username

        return self.create_user(email=email, username=username, password=password, **extra_fields)


class Account(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name="email", max_length=100, unique=True)
    username = models.CharField(max_length=100)
    date_joined = models.DateTimeField(verbose_name="date joined", auto_now_add=True)
    last_login = models.DateTimeField(verbose_name="last login", auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
   
    USERNAME_FIELD = 'email'
    
    objects = AccountManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True



class Product(models.Model):
    # === Laptop categories ===
    ULTRABOOK   = 'ultrabook'
    GAMING      = 'gaming'
    BUSINESS    = 'business'
    CONVERTIBLE = 'convertible'
    CHROMEBOOK  = 'chromebook'
    BUDGET      = 'budget'

    PRODUCT_CATEGORY_CHOICES = [
        (ULTRABOOK,   'Ultrabooks'),
        (GAMING,      'Gaming Laptops'),
        (BUSINESS,    'Business Laptops'),
        (CONVERTIBLE, '2-in-1 Convertibles'),
        (CHROMEBOOK,  'Chromebooks'),
        (BUDGET,      'Budget Laptops'),
    ]

    # === (Optional) Product types ===
    AUDIO_EQUIPMENT = 'Audio Equipment'
    ACCESSORIES     = 'Accessories'
    COMPONENTS      = 'Components'

    PRODUCT_TYPE_CHOICES = [
        (AUDIO_EQUIPMENT, 'Audio Equipment'),
        (ACCESSORIES,     'Accessories'),
        (COMPONENTS,      'Components'),
    ]

    # === (Optional) Tags for marketing ===
    FEATURED     = 'Featured Products'
    BESTSELLERS  = 'Bestsellers'
    POPULAR      = 'Popular Categories'
    NEW_ARRIVALS = 'New Arrivals'
    SALE         = 'Sale'
    TOP_RATED    = 'Top Rated'

    PRODUCT_TAG_CHOICES = [
        (FEATURED,     'Featured Products'),
        (BESTSELLERS,  'Bestsellers'),
        (POPULAR,      'Popular Categories'),
        (NEW_ARRIVALS, 'New Arrivals'),
        (SALE,         'Sale'),
        (TOP_RATED,    'Top Rated'),
    ]

    # === Fields ===
    name              = models.CharField(max_length=255)
    product_category  = models.CharField(
        max_length=20,
        choices=PRODUCT_CATEGORY_CHOICES
    )
    product_type      = models.CharField(
        max_length=50,
        choices=PRODUCT_TYPE_CHOICES,
        blank=True, null=True
    )
    product_tag       = models.CharField(
        max_length=50,
        choices=PRODUCT_TAG_CHOICES,
        blank=True, null=True
    )
    price             = models.DecimalField(max_digits=10, decimal_places=2)
    reviews_in_stars  = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=0.0,
        help_text="Average star rating (e.g. 4.5)"
    )
    quantity          = models.PositiveIntegerField(
        default=0,
        help_text="Units in stock"
    )
    description       = models.TextField()
    image             = models.ImageField(
        upload_to='products/',
        blank=True, null=True
    )
    shipping_fee      = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0
    )

    # === Admin: show a thumbnail ===
    def image_tag(self):
        if self.image:
            return mark_safe(
                f'<img src="{self.image.url}" '
                'width="50" height="50" style="border-radius:5px;" />'
            )
        return "(No Image)"
    image_tag.short_description = "Image Preview"

    # === Override save() to convert to WebP before storing ===
    def save(self, *args, **kwargs):
        if self.image:
            # open & ensure RGB
            img = Image.open(self.image)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # save to WebP in memory
            webp_buf = BytesIO()
            img.save(webp_buf, format="WebP", quality=90)
            webp_buf.seek(0)

            # replace the file with our WebP
            self.image = InMemoryUploadedFile(
                webp_buf,
                field_name='image',
                name=f"{self.image.name.rsplit('.',1)[0]}.webp",
                content_type='image/webp',
                size=webp_buf.tell(),
                charset=None,
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



class WrittenReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='written_reviews')
    name = models.CharField(max_length=100)  # Reviewer name
    stars = models.PositiveIntegerField(default=0)  # Rating out of 5
    content = models.TextField()  # Review text
    image = models.ImageField(upload_to='reviews/', blank=True, null=True)  # Optional image
    date = models.DateTimeField(auto_now_add=True)

    def image_tag(self):
        """Returns an HTML image tag for the product image in Django Admin."""
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="50" height="50" style="border-radius:5px;" />')
        return "(No Image)"

        image_tag.short_description = "Image Preview"  # Sets column name in Admin


    def save(self, *args, **kwargs):
        # Convert review image to WebP format before saving
        if self.image:
            img = Image.open(self.image)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            webp_image = BytesIO()
            img.save(webp_image, format="WebP", quality=90)
            webp_image.seek(0)
            
            self.image = InMemoryUploadedFile(
                webp_image,
                'ImageField',
                f"{self.image.name.split('.')[0]}.webp",
                'image/webp',
                webp_image.tell(),
                None
            )
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Review by {self.name} - {self.stars} stars"


class ShoppingCart(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def total_price(self):
        """Calculate total price for this cart item."""
        return self.product.price * self.quantity + self.shipping_fee
    total_price.short_description = 'Total Price'

    def image_tag(self):
        """HTML tag to display product image in admin interface."""
        if self.product.image:
            return format_html('<img src="{}" style="max-width: 100px; max-height: 100px;" />', self.product.image.url)
        return 'No Image'
    image_tag.short_description = 'Image Preview'

    def __str__(self):
        return f"{self.quantity} x {self.product.name} for {self.user.username}"


class BankDetails(models.Model):
    bank_name = models.CharField(max_length=255, default="Default Bank")
    branch_name = models.CharField(max_length=255, default="Default Branch")
    account_number = models.CharField(max_length=20, default="0000000000")
    account_holder = models.CharField(max_length=255, default="Default Account Holder")
    swift_code = models.CharField(max_length=11, default="SWIFT000")

    def __str__(self):
        return f"{self.bank_name} - {self.branch_name}"   


class Order(models.Model):
    ORDER_STATUSES = [
        ('under_review', 'Under Review'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    order_id = models.CharField(max_length=20, unique=True, editable=False, blank=True)
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postcode = models.CharField(max_length=20)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=ORDER_STATUSES, default='under_review')
    product_details = models.TextField()  # JSON field for product details
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    order_image = models.ImageField(upload_to='order_images/', null=True, blank=True)
    bank_details = models.ForeignKey('BankDetails', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivery_date_start = models.DateField(null=True, blank=True)
    delivery_date_end = models.DateField(null=True, blank=True)

    def calculate_total_price(self):
        """Calculate the total price including products and shipping."""
        products = json.loads(self.product_details).get("products", [])
        products_total = sum(int(item["quantity"]) * float(item["price"]) for item in products)
        return products_total + self.shipping_fee

    def image_tag(self):
        """HTML tag for displaying the order image in admin."""
        if self.order_image:
            return format_html('<img src="{}" style="max-width: 100px; max-height: 100px;" />', self.order_image.url)
        return 'No Image'
    image_tag.short_description = 'Image Preview'

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = str(uuid.uuid4())[:8].upper()
        if not self.delivery_date_start or not self.delivery_date_end:
            today = datetime.now().date()
            self.delivery_date_start = today + timedelta(days=14)
            self.delivery_date_end = self.delivery_date_start + timedelta(days=7)
        super().save(*args, **kwargs)

    def formatted_delivery_date(self):
        """Return a formatted delivery date range."""
        if self.created_at:
            start_date = self.created_at + timedelta(days=14)
            end_date = start_date + timedelta(days=7)
            return f"Between {start_date.strftime('%d %B')} and {end_date.strftime('%d %B')}"
        return "Delivery date unavailable"

    @staticmethod
    def format_price(price):
        """Format price with commas and two decimal places."""
        try:
            return "${:,.2f}".format(float(price))
        except (ValueError, TypeError):
            return "N/A"

    def format_product_details(self):
        """Format product details for easy rendering."""
        try:
            product_details = json.loads(self.product_details)
            formatted_details = []
        
            if 'products' in product_details and isinstance(product_details['products'], list):
                for item in product_details['products']:
                    name = item.get('name', 'N/A')
                    quantity = item.get('quantity', 'N/A')
                    price = item.get('price', 'N/A')
                    formatted_price = self.format_price(price)
                    formatted_details.append({
                        'name': name,
                        'quantity': quantity,
                        'price': formatted_price,
                    })
            return formatted_details if formatted_details else []
        except json.JSONDecodeError:
            print("Error: Invalid JSON format in product_details.")
            return []
        except Exception as e:
            print(f"Error formatting product details: {e}")
            return [] 


class PasswordResetCode(models.Model):
    email = models.EmailField(unique=True)
    reset_code = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
