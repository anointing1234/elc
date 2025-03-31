from django.urls import path,include,re_path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.views.static import serve 


urlpatterns = [ 
    path('authenticate/',views.authenticate_view,name='authenticate'),
    path('login_view/',views.login_view,name='login_view'),
    path('register/',views.register,name='register'),
    path('logout_view/',views.logout_view,name='logout_view'),
    path('contact_form/',views.contact_form, name='contact_form'),
    path('forgot_password/',views.forgot_password,name='forgot_password'),
    path('send-reset-code/',views.send_reset_code_view, name='sendmail_view'),
    path('reset_password/',views.reset_password_view, name='reset_password'),
    re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



 

