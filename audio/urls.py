from django.urls import path,include,re_path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.views.static import serve 


urlpatterns = [ 
    path('',views.home_view,name='home'),
    path('home/',views.home_view,name='home'),
    path('product_detail/<int:product_id>/', views.product_detail, name='product_detail'),
    path('add_to_cart/<int:product_id>/',views.add_to_cart, name='add_to_cart'),
    path('get_cart_count/',views.get_cart_count, name='get_cart_count'),
    path('cart/',views.cart_view,name='cart'),
    path('increase/<int:item_id>/', views.increase_quantity, name='increase'),
    path('decrease/<int:item_id>/', views.decrease_quantity, name='decrease'),
    path("create_order/",views.create_order, name="create_order"),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove'),
    path('shop/category/<slug:category_slug>/', views.category_products, name='category_products'),
    path('authenticate/',views.authenticate_view,name='authenticate'),
    path('checkout_view/',views.checkout_view,name='checkout_view'),
    path("order_success/", views.order_success, name="order_success"),
    path("myorders/",views.myorders,name="myorders"),
    path("get_bank_details/",views.get_bank_details, name="get_bank_details"),
    path('about_us/',views.about_us_view,name='about_us'),
    path('contact/',views.contact_view,name='contact'),
    path('search/',views.product_search, name='product_search'),
    path('terms_condition/',views.terms_view,name='terms_condition'), 
    path('refund_policy/',views.refund_view,name='refund_policy'),
    re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



 

