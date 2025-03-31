from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin  # Use UnfoldModelAdmin
from .models import Account, Product, WrittenReview, ShoppingCart, BankDetails, Order, PasswordResetCode
from django.utils.html import format_html
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import json

@admin.register(Account)
class AccountAdmin(UnfoldModelAdmin):
    list_display = ('email', 'username', 'is_admin', 'is_active', 'date_joined', 'last_login')
    search_fields = ('email', 'username')
    list_filter = ('is_admin', 'is_active', 'is_staff')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login')


@admin.register(Product)
class ProductAdmin(UnfoldModelAdmin):
    list_display = ('name', 'product_category', 'product_type','product_tag', 'price', 'quantity', 'image_tag')
    search_fields = ('name', 'product_category', 'product_type')
    list_filter = ('product_category', 'product_type', 'product_tag')
    ordering = ('-price',)
    readonly_fields = ('image_tag',)


@admin.register(WrittenReview)
class WrittenReviewAdmin(UnfoldModelAdmin):
    list_display = ('product', 'name', 'stars', 'date', 'image_tag')
    search_fields = ('product__name', 'name')
    list_filter = ('stars', 'date')
    readonly_fields = ('image_tag',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(UnfoldModelAdmin):
    list_display = ('user', 'product', 'quantity', 'added_at', 'total_price', 'image_tag')
    search_fields = ('user__email', 'product__name')
    list_filter = ('added_at',)
    readonly_fields = ('total_price', 'image_tag',)


@admin.register(BankDetails)
class BankDetailsAdmin(UnfoldModelAdmin):
    list_display = ('bank_name', 'branch_name', 'account_number', 'account_holder', 'swift_code')
    search_fields = ('bank_name', 'branch_name', 'account_holder')


@admin.register(Order)
class OrderAdmin(UnfoldModelAdmin):
    # Fields to display in the list view
    list_display = (
        'id',
        'order_id',
        'user',
        'status',
        'total_price',
        'formatted_delivery_date',
        'image_tag',
        'created_at',
        'format_product_details',  # Add formatted product details to the list display
    )

    # Fields to make read-only in the detail view
    readonly_fields = ('order_id', 'formatted_delivery_date', 'image_tag', 'created_at', 'updated_at', 'format_product_details',)

    # Filters and search fields
    list_filter = ('status', 'created_at',)
    search_fields = ('order_id', 'email', 'user__username', 'user__email', 'phone',)

    # Fieldsets for organizing the admin detail view
    fieldsets = (
        ('Order Information', {
            'fields': (
                'order_id',
                'user',
                'email',
                'phone',
                'status',
                'product_details',
                'total_price',
                'shipping_fee',
            ),
        }),
        ('Delivery Information', {
            'fields': ('formatted_delivery_date',),
        }),
        ('Address Information', {
            'fields': ('street_address', 'city', 'state', 'postcode',),
        }),
        ('Order Image', {
            'fields': ('order_image', 'image_tag',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at',),
        }),
    )

    # Custom actions for confirming and declining orders
    actions = ['confirm_order', 'decline_order']

    def confirm_order(self, request, queryset):
        """Mark selected orders as completed and send confirmation email."""
        updated_count = queryset.filter(status='under_review').update(status='completed')
        
        # Send emails for each confirmed order
        for order in queryset.filter(status='completed'):
            self.send_confirmation_email(order)

        self.message_user(request, f"{updated_count} order(s) marked as 'Completed' and emails sent.")

    confirm_order.short_description = "Confirm selected orders"

    def decline_order(self, request, queryset):
        """Mark selected orders as cancelled."""
        updated_count = queryset.filter(status='under_review').update(status='cancelled')
        self.message_user(request, f"{updated_count} order(s) marked as 'Cancelled'.")

    decline_order.short_description = "Decline selected orders"

    def send_confirmation_email(self, order):
        """Send an order confirmation email to the user."""
        subject = f"Order Confirmation - {order.order_id}"

        # Prepare the email content
        formatted_product_details = order.format_product_details()  # Get the formatted product details
        formatted_delivery_date = order.formatted_delivery_date()  # Get the formatted delivery date range

        html_content = render_to_string('order_confirmation_email.html', {
            'order': order,
            'formatted_product_details': formatted_product_details,
            'formatted_delivery_date': formatted_delivery_date  # Pass formatted delivery date range
        })

        # Create the email message
        email = EmailMessage(
            subject,
            html_content,
            settings.DEFAULT_FROM_EMAIL,
            [order.email],  # Send to the order's user email
        )
        email.content_subtype = 'html'  # Mark the email as HTML

        # Send the email
        try:
            email.send(fail_silently=False)
            print(f"Confirmation email sent successfully to {order.email}")  # Print message in the console
        except Exception as e:
            print(f"Failed to send confirmation email to {order.email}: {e}")

    def format_product_details(self, obj):
        """Format the product details for display in the admin panel."""
        try:
            product_details = json.loads(obj.product_details)
            return format_html("<br>".join([f"{item['name']} (Qty: {item['quantity']})" for item in product_details['products']]))
        except (json.JSONDecodeError, KeyError):
            return "Invalid product details"

    format_product_details.short_description = "Product Details"



@admin.register(PasswordResetCode)
class PasswordResetCodeAdmin(UnfoldModelAdmin):
    list_display = ('email', 'reset_code', 'created_at')
    search_fields = ('email',)
    ordering = ('-created_at',)
