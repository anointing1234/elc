from django.shortcuts import render
import requests
import logging
import json
import os
import time
from urllib.parse import urljoin
from requests.exceptions import RequestException
from django.contrib.auth import logout
from bs4 import BeautifulSoup
import random
from accounts.models import Product,ShoppingCart,WrittenReview,Order,BankDetails
from accounts.form import ReviewForm
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404,redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required



def home_view(request):
    # Tags
    featured_products = Product.objects.filter(product_tag=Product.FEATURED)
    bestsellers       = Product.objects.filter(product_tag=Product.BESTSELLERS)
    popular_categories= Product.objects.filter(product_tag=Product.POPULAR)
    new_arrivals      = Product.objects.filter(product_tag=Product.NEW_ARRIVALS)
    top_rated         = Product.objects.filter(product_tag=Product.TOP_RATED)
    on_sale           = Product.objects.filter(product_tag=Product.SALE)

    # All products
    all_products = Product.objects.all()

    # Categories
    ultrabooks       = Product.objects.filter(product_category=Product.ULTRABOOK)
    gaming_laptops   = Product.objects.filter(product_category=Product.GAMING)
    business_laptops = Product.objects.filter(product_category=Product.BUSINESS)
    convertibles     = Product.objects.filter(product_category=Product.CONVERTIBLE)
    chromebooks      = Product.objects.filter(product_category=Product.CHROMEBOOK)
    budget_laptops   = Product.objects.filter(product_category=Product.BUDGET)

    context = {
        # Tags
        'featured_products':   featured_products,
        'bestsellers':         bestsellers,
        'popular_categories':  popular_categories,
        'new_arrivals':        new_arrivals,
        'top_rated':           top_rated,
        'on_sale':             on_sale,

        # All
        'all_products':        all_products,

        # Categories
        'ultrabooks':          ultrabooks,
        'gaming_laptops':      gaming_laptops,
        'business_laptops':    business_laptops,
        'convertibles':        convertibles,
        'chromebooks':         chromebooks,
        'budget_laptops':      budget_laptops,
    }

    return render(request, 'home/index.html', context)



def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.filter(product_category=product.product_category)
    reviews = WrittenReview.objects.filter(product=product)

    if request.method == "POST":
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user  # Associate the review with the logged-in user
            review.save()
            return redirect('product_detail', product_id=product_id)  # Redirect to the same page to show the new review
    else:
        form = ReviewForm()  # Create a new form instance for GET requests

    stars_html = form.stars_widget()  # Get the stars HTML for rendering

    return render(request, 'home/product_details.html', {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'form': form,
        'stars_html': stars_html,  # Pass stars HTML to the template
    })






def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
       return JsonResponse({"error": "Login is required to add items to the cart."}, status=401)

    if request.method == "POST":
        try:
            product = Product.objects.get(id=product_id)  # Fetch the product
            user = request.user  # Get the logged-in user
            
            # Check if the product is already in the cart
            cart_item, created = ShoppingCart.objects.get_or_create(
                user=user, product=product,shipping_fee=product.shipping_fee,
                defaults={'quantity': 1}
            )
            if not created:
                # If the item exists, increase the quantity
                cart_item.quantity += 1
                cart_item.save()
            
            return JsonResponse({"message": "Product added to cart successfully!"}, status=200)
        
        except Product.DoesNotExist:
            return JsonResponse({"error": "Product not found."}, status=404)
    return JsonResponse({"error": "Invalid request method."}, status=400)


@login_required(login_url='authenticate')
def get_cart_count(request):
    if request.user.is_authenticated:
        cart_count = ShoppingCart.objects.filter(user=request.user).count()  # Get the number of items in the cart
        return JsonResponse({"cart_count": cart_count})
    else:
        return JsonResponse({"cart_count": 0})




@login_required(login_url='authenticate')
def cart_view(request):
    # Fetch cart items for the logged-in user
    cart_items = ShoppingCart.objects.filter(user=request.user)
    
    # Initialize total variables
    subtotal = 0
    total = 0
    shipping_total = 0
    
    # Loop through each item to calculate subtotal and shipping fee
    for item in cart_items:
        # Calculate the subtotal (product price * quantity)
        item_subtotal = item.product.price * item.quantity
        subtotal += item_subtotal
        
        # Calculate the shipping fee for the item (example logic)
        shipping_fee = item.product.shipping_fee * item.quantity  # You can adjust this logic based on the product
        
        # Add shipping fee to the total
        shipping_total += shipping_fee
        
        # Add the item total (subtotal + shipping) to the total
        total += item_subtotal + shipping_fee

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_total': shipping_total,
        'total': total,
    }
    return render(request, 'home/cart.html', context)


def get_cart_total(user):
    cart_items = ShoppingCart.objects.filter(user=user)
    total = sum(item.total_price() for item in cart_items)
    return total



def calculate_shipping_fee(cart_total):
    # Example: Flat $10 shipping if cart total is below $100, free otherwise
    return  cart_total 


@login_required(login_url='authenticate')
# Function to increase item quantity
def increase_quantity(request, item_id):
    cart_item = ShoppingCart.objects.get(id=item_id, user=request.user)
    cart_item.quantity += 1
    cart_item.save()

    # Calculate updated totals
    cart_total = get_cart_total(request.user)
    shipping_fee = calculate_shipping_fee(cart_total)
    total_amount = cart_total + shipping_fee

    return JsonResponse({
        'new_quantity': cart_item.quantity,
        'new_total': cart_item.total_price(),
        'new_cart_total': cart_total,
        'new_shipping_total': shipping_fee,
        'new_total_amount': total_amount,
    })

# Function to decrease item quantity
def decrease_quantity(request, item_id):
    cart_item = ShoppingCart.objects.get(id=item_id, user=request.user)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()

    # Calculate updated totals
    cart_total = get_cart_total(request.user)
    shipping_fee = calculate_shipping_fee(cart_total)
    total_amount = cart_total + shipping_fee

    return JsonResponse({
        'new_quantity': cart_item.quantity,
        'new_total': cart_item.total_price(),
        'new_cart_total': cart_total,
        'new_shipping_total': shipping_fee,
        'new_total_amount': total_amount,
    })

@login_required(login_url='authenticate')
# Function to remove item from cart
def remove_from_cart(request, item_id):
    cart_item = ShoppingCart.objects.get(id=item_id, user=request.user)
    cart_item.delete()

    # Calculate updated totals
    cart_total = get_cart_total(request.user)
    shipping_fee = calculate_shipping_fee(cart_total)
    total_amount = cart_total + shipping_fee

    return JsonResponse({
        'message': 'Item removed successfully',
        'new_cart_total': cart_total,
        'new_shipping_total': shipping_fee,
        'new_total_amount': total_amount,
    })


def category_products(request, category_slug):
    # Validate that it's a valid category slug
    valid_categories = dict(Product.PRODUCT_CATEGORY_CHOICES)
    if category_slug not in valid_categories:
        return render(request, 'home/invalid_category.html', {'invalid_category': category_slug})

    # Filter products by category
    products = Product.objects.filter(product_category=category_slug)

    # Paginate results
    paginator = Paginator(products, 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'home/category.html', {
        'products': page_obj,
        'category_key': category_slug,
        'category_label': valid_categories[category_slug],  # For readable name like "Ultrabooks"
        'product_count': products.count(),
    })

def authenticate_view(request):
    return render(request,'auth/authenticate.html')


@login_required(login_url='authenticate')
def checkout_view(request):
    cart_items = ShoppingCart.objects.filter(user=request.user)
    # Calculate cart total and shipping fee
    cart_total = sum(item.total_price() for item in cart_items)
    shipping_fee = sum(item.shipping_fee for item in cart_items)  
    total_with_shipping = cart_total + shipping_fee
    
    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'shipping_fee': shipping_fee,
        'total_with_shipping': total_with_shipping,
    }
    return render(request,'home/checkout.html',context)    



def get_bank_details(request):
    try:
        bank_details = BankDetails.objects.first()  # Fetch the first bank details record
        if not bank_details:
            return JsonResponse({"error": "Bank details not found"}, status=404)

        return JsonResponse({
            "bank_name": bank_details.bank_name,
            "branch_name": bank_details.branch_name,
            "account_number": bank_details.account_number,
            "account_holder": bank_details.account_holder,
            "swift_code": bank_details.swift_code,
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)  

@login_required(login_url='authenticate')
def create_order(request):
    if request.method == "POST":
        try:
            # Parse the request body
            data = json.loads(request.body)

            billing_details = data.get("billingDetails")
            cart_details = data.get("cartDetails")

            # Validate data
            if not billing_details or not cart_details:
                return JsonResponse({"success": False, "error": "Invalid request data."}, status=400)

            # Create a list to hold order IDs for the response
            order_ids = []

            # Iterate over each product in the cart
            for product in cart_details["products"]:
                # Calculate total price for the individual product order
                total_price = float(product["quantity"]) * float(product["price"])

                # Calculate shipping fee (this is a placeholder; adjust as needed)
                shipping_fee = cart_details.get("shipping_fee", 0.0)  # Ensure this is set correctly

                # Create a new order instance for each product
                order = Order(
                    user=request.user,
                    street_address=billing_details["street_address"],
                    city=billing_details["city"],
                    state=billing_details["state"],
                    postcode=billing_details["postcode"],
                    email=billing_details["email"],
                    phone=billing_details["phone"],
                    product_details=json.dumps({"products": [product]}),  # Store only the current product
                    total_price=total_price,
                    shipping_fee=shipping_fee,
                )

                # Assign an image to the order from the product
                product_id = product["id"]
                try:
                    product_instance = Product.objects.get(id=product_id)
                    if product_instance.image:
                        order.order_image = product_instance.image  # Assign product's image to order_image
                except Product.DoesNotExist:
                    pass  # Handle the case where the product does not exist

                # Save the order instance
                order.save()
                order_ids.append(order.id)  # Store the order ID for the response

            # Clear the shopping cart for the user
            ShoppingCart.objects.filter(user=request.user).delete()

            return JsonResponse({"success": True, "order_ids": order_ids})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON format."}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)




def order_success(request):
    return render(request, 'home/order.html')



@login_required(login_url='authenticate')
def myorders(request):
    """
    Fetch and display all orders for the currently logged-in user.
    """
    # Fetch orders for the logged-in user
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    # Parse product details for each order
    for order in orders:
        try:
            order.product_details_parsed = json.loads(order.product_details).get('products', [])
        except json.JSONDecodeError:
            order.product_details_parsed = []  # Default to empty list if JSON is invalid

    return render(request, 'home/my_orders.html', {
        'orders': orders,
    })



def about_us_view(request):
    return render(request,'home/about.html')



def contact_view(request):
    return render(request,'home/contact.html')




def product_search(request):
    query = request.GET.get('search', '').strip()  # Trim whitespace
    print(f"Search query: '{query}'")  # Debugging line

    if query:
        # Check if the query length is less than 3
        if len(query) < 3:
            # If less than 3 characters, we can still search for products that contain the query
            products = Product.objects.filter(name__icontains=query)
        else:
            # If 3 or more characters, perform a more comprehensive search
            products = Product.objects.filter(name__icontains=query)

        print(f"Found products: {products}")  # Debugging line
    else:
        products = Product.objects.none()

    paginator = Paginator(products, 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'home/search_results.html', {
        'Search_products': page_obj,
        'Search_count': products.count(),
        'search_query': query,
    })




def terms_view(request):
    return render(request,'home/terms_conditions.html')

def refund_view(request):
    return render(request,'home/refund_policy.html')


      













