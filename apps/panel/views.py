from django.shortcuts import render,get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from apps.product.models import Product,Category,LikeOrUnlike,Comment
from apps.order.models import Order,OrderDetail
import jdatetime
from django.db.models import Count, Q, Prefetch


@login_required
def dashboard(request):
    user = request.user

    # محاسبه آمار سفارشات کاربر
    total_orders = user.orders.count()
    delivered_orders = user.orders.filter(status='delivered').count()
    canceled_orders = user.orders.filter(status='canceled').count()
    returned_orders = user.orders.filter(status='returned').count()

    # آخرین سفارش‌ها
    latest_orders = user.orders.all().order_by('-registerDate')[:5]

    # فرمت کردن تاریخ به شمسی برای آخرین سفارش‌ها
    for order in latest_orders:
        order.jalali_date = jdatetime.datetime.fromgregorian(datetime=order.registerDate).strftime("%Y/%m/%d")
        order.final_price = order.get_order_total_price()

    # محصولات پیشنهادی بر اساس خریدهای قبلی
    recommended_products = get_recommended_products_with_ratings(user)

    context = {
        'total_orders': total_orders,
        'delivered_orders': delivered_orders,
        'canceled_orders': canceled_orders,
        'returned_orders': returned_orders,
        'latest_orders': latest_orders,
        'recommended_products': recommended_products,
        'media_url': '/media/'
    }

    return render(request, 'panel_app/partials/dashboard.html', context)

def get_recommended_products_with_ratings(user, limit=10):
    """
    دریافت محصولات پیشنهادی با محاسبه رتبه‌بندی و رنگ‌ها
    """
    try:
        # دریافت محصولاتی که کاربر قبلاً خریده
        purchased_products = OrderDetail.objects.filter(
            order__customer=user,
            order__status='delivered'
        ).values_list('product', flat=True).distinct()

        if purchased_products:
            # دریافت دسته‌بندی‌های محصولات خریداری شده
            purchased_categories = Product.objects.filter(
                id__in=purchased_products
            ).values_list('categories', flat=True).distinct()

            # دریافت برندهای محصولات خریداری شده
            purchased_brands = Product.objects.filter(
                id__in=purchased_products
            ).values_list('brand', flat=True).distinct()

            # پیشنهاد محصولات از همان دسته‌بندی‌ها و برندها
            recommended = Product.objects.filter(
                Q(categories__in=purchased_categories) | Q(brand__in=purchased_brands),
                isActive=True
            ).exclude(
                id__in=purchased_products
            ).distinct()[:limit]

            # اگر تعداد کافی نبود، محصولات پرفروش را اضافه کن
            if recommended.count() < limit:
                remaining = limit - recommended.count()
                popular_products = get_popular_products().exclude(
                    id__in=purchased_products
                ).exclude(
                    id__in=recommended.values_list('id', flat=True)
                )[:remaining]
                recommended = list(recommended) + list(popular_products)

        else:
            # اگر کاربر هیچ خریدی نداشته، محصولات پرفروش را نشان بده
            recommended = get_popular_products()[:limit]

        # محاسبه رتبه‌بندی و ویژگی‌ها برای هر محصول
        product_list = []
        for product in recommended:
            product_data = calculate_product_ratings_and_features(product)
            product_list.append(product_data)

        return product_list

    except Exception as e:
        # در صورت بروز خطا، محصولات پرفروش را برگردان
        popular_products = get_popular_products()[:limit]
        return [calculate_product_ratings_and_features(product) for product in popular_products]

def calculate_product_ratings_and_features(product):
    """
    محاسبه رتبه‌بندی و ویژگی‌های محصول
    """
    # محاسبه لایک و دیسلایک
    likes_count = LikeOrUnlike.objects.filter(product=product, like=True).count()
    unlikes_count = LikeOrUnlike.objects.filter(product=product, unlike=True).count()
    total_votes = likes_count + unlikes_count

    # محاسبه تعداد نظرات
    comments_count = Comment.objects.filter(product=product, isActive=True).count()

    # محاسبه رتبه‌بندی
    if total_votes > 0:
        rating = 4 + (likes_count - unlikes_count) / (total_votes * 10)
        rating = max(3.5, min(rating, 5.0))  # محدود کردن بین 3.5 و 5.0
    else:
        rating = 4.0

    # دریافت رنگ‌های محصول
    colors = product.features_value.filter(feature__title='رنگ').values_list('value', flat=True)

    # اگر رنگ پیدا نشد، از رنگ‌های پیش‌فرض استفاده کن
    if not colors:
        colors = ['مشکی', 'سفید', 'نقره‌ای']

    return {
        'product': product,
        'image_url': product.image.url if product.image else '',
        'short_title': product.title[:50] + '...' if len(product.title) > 50 else product.title,
        'brand': product.brand.title if product.brand else 'بدون برند',
        'price': product.price,
        'final_price': product.get_price_by_discount(),
        'discount_percentage': product.get_discount_percentage(),
        'colors': list(colors)[:3],  # حداکثر 3 رنگ نشان بده
        'rating': round(rating, 1),
        'comments_count': comments_count,
        'likes_count': likes_count,
    }

def get_popular_products():
    """
    دریافت محصولات پرفروش
    """
    return Product.objects.filter(
        isActive=True
    ).annotate(
        order_count=Count('orderItems')
    ).order_by('-order_count', '-createAt')


import jdatetime
from django.utils import timezone
from datetime import datetime

@login_required
def orders_view(request):
    user = request.user

    # دریافت پارامترهای فیلتر
    status_filter = request.GET.get('status', 'all')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search_query = request.GET.get('search', '')

    # فیلتر کردن سفارشات
    orders = user.orders.all().order_by('-registerDate')

    # فیلتر بر اساس وضعیت
    if status_filter != 'all':
        orders = orders.filter(status=status_filter)

    # فیلتر بر اساس تاریخ
    if date_from:
        try:
            # تبدیل تاریخ شمسی به میلادی
            jalali_date_from = jdatetime.datetime.strptime(date_from, '%Y/%m/%d')
            gregorian_date_from = jalali_date_from.togregorian()
            # اضافه کردن زمان به شروع روز
            gregorian_date_from = timezone.make_aware(
                datetime.combine(gregorian_date_from, datetime.min.time())
            )
            orders = orders.filter(registerDate__gte=gregorian_date_from)
        except ValueError:
            # در صورت خطا در فرمت تاریخ، فیلتر اعمال نشود
            pass

    if date_to:
        try:
            # تبدیل تاریخ شمسی به میلادی
            jalali_date_to = jdatetime.datetime.strptime(date_to, '%Y/%m/%d')
            gregorian_date_to = jalali_date_to.togregorian()
            # اضافه کردن زمان به پایان روز
            gregorian_date_to = timezone.make_aware(
                datetime.combine(gregorian_date_to, datetime.max.time())
            )
            orders = orders.filter(registerDate__lte=gregorian_date_to)
        except ValueError:
            # در صورت خطا در فرمت تاریخ، فیلتر اعمال نشود
            pass

    # جستجو در شماره سفارش
    if search_query:
        orders = orders.filter(orderCode__icontains=search_query)

    # فرمت کردن تاریخ به شمسی برای نمایش
    for order in orders:
        order.jalali_date = jdatetime.datetime.fromgregorian(
            datetime=order.registerDate
        ).strftime("%Y/%m/%d")
        order.final_price = order.get_order_total_price()
        order.items_count = order.details.count()

    # آمار سفارشات برای فیلترها
    orders_stats = {
        'all': user.orders.count(),
        'pending': user.orders.filter(status='pending').count(),
        'processing': user.orders.filter(status='processing').count(),
        'shipped': user.orders.filter(status='shipped').count(),
        'delivered': user.orders.filter(status='delivered').count(),
        'canceled': user.orders.filter(status='canceled').count(),
    }

    context = {
        'orders': orders,
        'orders_stats': orders_stats,
        'current_status': status_filter,
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
    }

    return render(request, 'panel_app/partials/orders.html', context)


from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

@login_required
@require_POST
def cancel_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id, customer=request.user)

        # فقط سفارش‌های در حال بررسی قابل لغو هستند
        if order.status == 'pending':
            order.status = 'canceled'
            order.save()
            return JsonResponse({'success': True, 'message': 'سفارش با موفقیت لغو شد'})
        else:
            return JsonResponse({'success': False, 'message': 'امکان لغو این سفارش وجود ندارد'})

    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'سفارش یافت نشد'})


@login_required
def order_detail(request, order_code):
    order = get_object_or_404(
        Order,
        orderCode=order_code,
        customer=request.user
    )

    context = {
        'order': order,
        'order_items': order.details.all().select_related('product', 'brand')
    }

    return render(request, 'panel_app/partials/orderdetail.html', context)



from django.contrib import messages


from datetime import datetime, date

@login_required
def edit_profile(request):
    user = request.user

    if request.method == 'POST':
        # دریافت داده‌های فرم
        name = request.POST.get('name')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        phone_number = request.POST.get('phone_number')

        # اعتبارسنجی داده‌ها
        errors = []

        if not name or not name.strip():
            errors.append('نام الزامی است')

        if not age or not age.strip():
            errors.append('سن الزامی است')
        if not gender:
            errors.append('جنسیت الزامی است')
        if not phone_number or not phone_number.strip():
            errors.append('شماره تماس الزامی است')

        # اعتبارسنجی سن
        if age and age.strip():
            if not age.isdigit():
                errors.append('سن باید عدد باشد')
            else:
                age_int = int(age)
                if age_int < 1 or age_int > 150:
                    errors.append('سن باید بین 1 تا 150 باشد')

        # اعتبارسنجی شماره تماس
        if phone_number and phone_number.strip():
            if not phone_number.isdigit():
                errors.append('شماره تماس باید عدد باشد')
            elif len(phone_number) != 11:
                errors.append('شماره تماس باید 11 رقمی باشد')

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                # محاسبه تاریخ تولد از سن
                current_year = date.today().year
                birth_year = current_year - int(age)
                birth_date = date(birth_year, 1, 1)  # اول فروردین آن سال

                # بروزرسانی اطلاعات کاربر
                user.name = name.strip()
                user.birth_date = birth_date
                user.gender = gender
                user.mobileNumber = phone_number.strip()

                # ذخیره اطلاعات اضافی در مدل UserSecurity
                if hasattr(user, 'security'):
                    user.security.isInfoFiled = True
                    user.security.save()

                user.save()

                messages.success(request, 'اطلاعات با موفقیت بروزرسانی شد')
                return redirect('panel:dashboard')  # یا نام URL پروفایل

            except Exception as e:
                messages.error(request, f'خطا در بروزرسانی اطلاعات: {str(e)}')

    # محاسبه سن از تاریخ تولد برای نمایش در فرم
    current_age = user.age if user.birth_date else ''

    context = {
        'user': user,
        'current_age': current_age,
        'genders': [
            ('True', 'مرد'),
            ('False', 'زن'),
        ]
    }

    return render(request, 'panel_app/partials/info.html', context)





from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

class PurchasedDrivesView(LoginRequiredMixin, ListView):
    model = OrderDetail
    template_name = 'panel_app/partials/purchased_drives.html'
    context_object_name = 'purchased_drives'

    def get_queryset(self):
        # سفارشات نهایی شده کاربر که شامل محصولات درایور هستند
        user_orders = Order.objects.filter(
            customer=self.request.user,
            isFinally=True
        )

        # جزئیات سفارش که محصولات درایور هستند
        purchased_drives = OrderDetail.objects.filter(
            order__in=user_orders,
            product__isDrive=True,
            product__isActive=True
        ).select_related('product', 'product__brand').distinct()

        return purchased_drives