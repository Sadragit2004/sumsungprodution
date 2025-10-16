"""web URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
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
from django.urls import path,include
from django.conf.urls.static import static
import web.settings as sett

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('apps.main.urls',namespace='main')),
    path('ckeditor',include('ckeditor_uploader.urls')),
    path('accounts/',include('apps.user.urls',namespace='user')),
    path('product/',include('apps.product.urls',namespace='product')),
    path('order/',include('apps.order.urls',namespace='order')),
    path('discount/',include('apps.discount.urls',namespace='discount')),
    path('peyment/',include('apps.peyment.urls',namespace='peyment')),
    path('search/',include('apps.search.urls',namespace='search')),
    path('blog/',include('apps.blog.urls',namespace='blog')),
    path('panel/',include('apps.panel.urls',namespace='panel'))


]+static(sett.MEDIA_URL,document_root = sett.MEDIA_ROOT)
