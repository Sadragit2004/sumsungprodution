from django.shortcuts import render
import web.settings as sett
from django.utils import timezone
from .models import *

# Create your views here.




def media_admin(request):
    context = {
        'media_url':sett.MEDIA_URL
    }


    return context


def main(request):

    return render(request,'main_app/main.html')




def slider_list_view(request):
    """
    دریافت تمام اسلایدرهای سایت و نمایش اسلایدرهای فعال.
    """
    # دریافت تمام اسلایدرهای سایت
    sliders = SliderSite.objects.all()

    # بررسی تاریخ انقضا و غیرفعال کردن اسلایدرهای منقضی‌شده
    for slider in sliders:
        slider.deactivateIfExpired()

    # فقط اسلایدرهای فعال را نمایش می‌دهیم
    active_sliders = SliderSite.objects.filter(isActive=True)

    return render(request, 'main_app/slider_file.html', {'sliders': active_sliders})

def slider_list_view2(request):
    """
    دریافت 2 اسلایدر اول سایت و نمایش اسلایدرهای فعال.
    """
    # دریافت تمام اسلایدرها و مرتب‌سازی بر اساس تاریخ ثبت
    sliders = SliderSite.objects.all().order_by('registerData')[:2]

    # بررسی تاریخ انقضا و غیرفعال کردن اسلایدرهای منقضی‌شده
    for slider in sliders:
        slider.deactivateIfExpired()

    # فقط اسلایدرهای فعال را نمایش می‌دهیم
    active_sliders = SliderSite.objects.filter(isActive=True)[:2]

    return render(request, 'main_app/slider_file2.html', {'sliders': active_sliders})



def slider_main_view(request):
    """
    دریافت 2 اسلایدر اصلی (مرکز) و نمایش اسلایدرهای فعال.
    """
    sliders = SliderMain.objects.all().order_by('registerData')[:2]

    # بررسی تاریخ انقضا و غیرفعال کردن اسلایدرهای منقضی‌شده
    for slider in sliders:
        slider.deactivateIfExpired()

    # فقط اسلایدرهای فعال را نمایش می‌دهیم
    active_sliders = SliderMain.objects.filter(isActive=True)[:2]

    return render(request, 'main_app/slider_main.html', {'sliders': active_sliders})

def active_banners(request):
    """
    نمایش بنرهای فعال با تاریخ انقضای معتبر.
    """
    banners = Banner.objects.filter(isActive=True, endData__gt=timezone.now())
    return render(request, 'main_app/slider_banner.html', {'banners': banners})



def about(request):

    return render(request,'main_app/dsm/about.html')


def call(request):

    return render(request,'main_app/dsm/call.html')