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
    featured_products = Product.objects.filter(product_tag=Product.FEATURED)
    bestsellers = Product.objects.filter(product_tag='Bestsellers')
    New_arrivals = Product.objects.filter(product_tag='New Arrivals')
    Top_rated = Product.objects.filter(product_tag='Top Rated')
    On_sale = Product.objects.filter(product_tag='Sale')
    all_products = Product.objects.all()
    
    Amplifies = Product.objects.filter(product_category='Amplifiers')
    Digital = Product.objects.filter(product_category='Digital')
    Loudspeakers = Product.objects.filter(product_category='Loudspeakers')
    Turnatables = Product.objects.filter(product_category='Turntables')

 

    return render(request,'home/index.html',
    {
    'featured_products': featured_products,
    'bestsellers': bestsellers,
    'New_arrivals':New_arrivals,
    'Top_rated':Top_rated,
    'on_sale': On_sale,
    'all_products': all_products,
    'Amplifies': Amplifies,
    'Digital': Digital,
    'Loudspeakers':Loudspeakers,
    'Turnatables':Turnatables,
    })
    

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






def Loudspeakers_view(request):
    # Query the products based on category
    Loudspeakers_products = Product.objects.filter(product_category="Loudspeakers")

    # Initialize the paginator with the list of products and the number per page (e.g., 3)
    paginator = Paginator(Loudspeakers_products, 3)

    # Get the current page number from the GET request (defaults to 1 if not specified)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Pass the paginated products and the total count to the template
    return render(request, 'home/Loudspeakers.html', {
        'Loudspeakers_products': page_obj,  # Use the paginated page_obj here
        'Loudspeakers_count': Loudspeakers_products.count(),  # The total count remains the same
    })


def Mixer_Console_view(request):
     # Query the products based on category
    Mixer_Console_products = Product.objects.filter(product_category="Mixer Console")

    # Initialize the paginator with the list of products and the number per page (e.g., 3)
    paginator = Paginator(Mixer_Console_products, 3)

    # Get the current page number from the GET request (defaults to 1 if not specified)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Pass the paginated products and the total count to the template
    return render(request, 'home/Mixer_Console.html', {
        'Mixer_Console_products': page_obj,  # Use the paginated page_obj here
        'Mixer_Console_count': Mixer_Console_products.count(),  # The total count remains the same
    })



def Digital_view(request):
     # Query the products based on category
    Digital_products = Product.objects.filter(product_category="Digital")

    # Initialize the paginator with the list of products and the number per page (e.g., 3)
    paginator = Paginator(Digital_products, 3)

    # Get the current page number from the GET request (defaults to 1 if not specified)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Pass the paginated products and the total count to the template
    return render(request, 'home/Digital.html', {
        'Digital_products': page_obj,  # Use the paginated page_obj here
        'Digital_count': Digital_products.count(),  # The total count remains the same
    })









def Turntables_view(request):
     # Query the products based on category
    Turntables_products = Product.objects.filter(product_category="Turntables")

    # Initialize the paginator with the list of products and the number per page (e.g., 3)
    paginator = Paginator(Turntables_products, 3)

    # Get the current page number from the GET request (defaults to 1 if not specified)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Pass the paginated products and the total count to the template
    return render(request, 'home/Turntables.html', {
        'Turntables_products': page_obj,  # Use the paginated page_obj here
        'Turntables_count': Turntables_products.count(),  # The total count remains the same
    })


def Amplifiers_view(request):
     # Query the products based on category
    Amplifiers_products = Product.objects.filter(product_category="Amplifiers")

    # Initialize the paginator with the list of products and the number per page (e.g., 3)
    paginator = Paginator(Amplifiers_products, 3)

    # Get the current page number from the GET request (defaults to 1 if not specified)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Pass the paginated products and the total count to the template
    return render(request, 'home/Amplifiers.html', {
        'Amplifiers_products': page_obj,  # Use the paginated page_obj here
        'Amplifiers_count': Amplifiers_products.count(),  # The total count remains the same
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





      













