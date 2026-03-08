"""
URL configuration for kiblock project.
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', core_views.login_view, name='login'),
    path('logout/', core_views.logout_view, name='logout'),
    path('blocks/', core_views.block_list, name='block_list'),
    path('blocks/search/', core_views.search_blocks, name='search_blocks'),
    path('blocks/upload-project/', core_views.upload_project, name='upload_project'),
    path('blocks/copy/<int:block_id>/', core_views.copy_block, name='copy_block'),
    path('blocks/add-to-cart/<int:block_id>/', core_views.add_to_cart, name='add_to_cart'),
    path('cart/', core_views.cart_view, name='cart'),
    path('cart/increase/<int:item_id>/', core_views.increase_cart_item, name='increase_cart_item'),
    path('cart/decrease/<int:item_id>/', core_views.decrease_cart_item, name='decrease_cart_item'),
    path('cart/remove/<int:item_id>/', core_views.remove_cart_item, name='remove_cart_item'),
    path('history/', core_views.copied_history_view, name='copied_history'),
    path('history/add-to-cart/<int:block_id>/', core_views.add_to_cart, name='history_add_to_cart'),
    path('', lambda request: redirect('login'), name='home'),
]

# Serve media files directly from Django (also in production)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'core' / 'static')