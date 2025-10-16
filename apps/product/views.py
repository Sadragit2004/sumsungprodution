from django.shortcuts import render
from django.db.models import Count
from .models import Category,Brand,Feature,FeatureValue
from django.db.models import Q,Count,Min,Max
from django.core.paginator import Paginator
from .filters import ProductFilter
from django.db.models import Sum


def category_group_view(request):
    # همه دسته‌بندی‌ها همراه با شمارش محصولات
    categories = (
        Category.objects.annotate(product_count=Count("products"))
        .filter(isActive=True)
        .order_by("-product_count")  # بیشترین محصول اول
    )

    return render(request, "product_app/group.html", {"categories": categories})


from django.db.models import Count, Case, When, F, Avg, FloatField
from .models import Product, Comment, LikeOrUnlike

def latest_products_view(request):
    """
    Fetches the 20 latest products with their calculated ratings and available colors.
    """
    # Use Prefetch to optimize database queries for related data
    products = Product.objects.filter(isActive=True).order_by('-createAt')[:20]

    product_list = []
    for product in products:

        likes_count = LikeOrUnlike.objects.filter(product=product, like=True).count()
        unlikes_count = LikeOrUnlike.objects.filter(product=product, unlike=True).count()
        total_votes = likes_count + unlikes_count

        comments = Comment.objects.filter(product=product, isActive=True)
        comments_count = comments.count()


        if total_votes > 0:
            rating = 4 + (likes_count - unlikes_count) / (total_votes * 10)
            rating = max(3.5, min(rating, 5.0)) # Clamp between 3.5 and 5.0
        else:
            rating = 4.0
        colors = product.features_value.filter(feature__title='رنگ').values_list('value', flat=True)

        product_data = {
            'product': product,
            'image_url': product.image.url if product.image else '',
            'short_title': product.title,
            'brand': product.brand.title,
            'price': product.price,
            'colors': colors,
            'rating': round(rating, 1),
            'comments_count': comments_count,
        }
        product_list.append(product_data)

    context = {
        'products': product_list,
    }
    return render(request, 'product_app/recently_product.html', context)






def top_brands_view(request):
    """
    Fetches top brands sorted by the number of active products.
    """
    brands = Brand.objects.filter(isActive=True).annotate(
        product_count=Count('products')
    ).order_by('-product_count')[:10]  # Get the top 10 brands

    context = {
        'brands': brands,
    }
    return render(request, 'product_app/brands.html', context)



from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView
from django.db.models import Prefetch, Count, Avg
from django.http import JsonResponse
from .models import Product, ProductGallery, Comment, LikeOrUnlike
from apps.user.models import CustomUser
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch

class ProductDetailView(DetailView):
    model = Product
    template_name = 'product_app/product_detail.html'
    context_object_name = 'product'

    def get_object(self, queryset=None):
        slug = self.kwargs.get('slug')
        return get_object_or_404(
            Product.objects.select_related('brand')
                           .prefetch_related(
                               'categories',
                               'gallery',
                               Prefetch(
                                   'comments',
                                   queryset=Comment.objects.filter(isActive=True)
                                   .select_related('user')
                                   .prefetch_related('replies')
                               )
                           )
                           .filter(isActive=True),
            slug=slug
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object

        # محاسبه امتیاز متوسط محصول
        comments = product.comments.filter(isActive=True)
        if comments.exists():
            avg_rating = comments.aggregate(avg=Avg('rating'))['avg']
            context['average_rating'] = round(avg_rating, 1)
        else:
            context['average_rating'] = 0

        # تعداد نظرات
        context['comments_count'] = comments.count()

        # تعداد پیشنهادها
        context['suggest_count'] = comments.filter(is_suggest=True).count()

        # گالری محصول
        context['gallery'] = product.gallery.all()

        # محصولات مرتبط (همان دسته‌بندی)
        related_products = Product.objects.filter(
            categories__in=product.categories.all(),
            isActive=True
        ).exclude(id=product.id).distinct()[:8]
        context['related_products'] = related_products

        # ویژگی‌های محصول
        features = product.features_value.select_related('feature', 'filterValue').all()
        context['features'] = features

        # ========================
        # اضافه کردن متاتگ
        # ========================
        if hasattr(product, 'meta_tag'):
            context['meta'] = product.meta_tag.get_meta_context(self.request)
        else:
            # اگر متاتگ نداشت، مقادیر پیش‌فرض
            default_image = self.request.build_absolute_uri("/media/default/og-image.jpg")
            context['meta'] = {
                "title": f"{product.title} | سامسونگ مرکزی آذربایجان",
                "description": product.short_description(),
                "robots": "index, follow",
                "og_type": "website",
                "og_site_name": "سامسونگ مرکزی آذربایجان",
                "og_title": f"{product.title} | سامسونگ مرکزی آذربایجان",
                "og_description": product.short_description(),
                "og_image": default_image,
                "og_url": self.request.build_absolute_uri(),
                "twitter_card": "summary_large_image",
                "twitter_title": f"{product.title} | سامسونگ مرکزی آذربایجان",
                "twitter_description": product.short_description(),
                "twitter_image": default_image,
            }

        return context


# ویو برای ثبت نظر
def add_comment(request, product_slug):
    if request.method == 'POST' and request.user.is_authenticated:
        product = get_object_or_404(Product, slug=product_slug, isActive=True)
        text = request.POST.get('text')
        is_suggest = request.POST.get('is_suggest') == 'on'
        parent_id = request.POST.get('parent_id')

        if text:
            comment = Comment(
                user=request.user,
                product=product,
                text=text,
                is_suggest=is_suggest
            )

            if parent_id:
                parent_comment = get_object_or_404(Comment, id=parent_id)
                comment.parent = parent_comment

            comment.save()

            return JsonResponse({
                'success': True,
                'message': 'نظر شما با موفقیت ثبت شد و پس از تایید نمایش داده می‌شود.'
            })

    return JsonResponse({
        'success': False,
        'message': 'خطا در ثبت نظر'
    }, status=400)

# ویو برای لایک/دیسلایک
def like_unlike_comment(request, comment_id):
    if request.method == 'POST' and request.user.is_authenticated:
        comment = get_object_or_404(Comment, id=comment_id)
        action = request.POST.get('action')  # 'like' or 'unlike'

        # بررسی آیا کاربر قبلا روی این نظر واکنش داشته یا نه
        like_unlike, created = LikeOrUnlike.objects.get_or_create(
            user=request.user,
            comment=comment,
            product=comment.product
        )

        if action == 'like':
            if like_unlike.like:
                # اگر قبلا لایک کرده، لایک را برمی‌دارد
                like_unlike.like = False
            else:
                like_unlike.like = True
                like_unlike.unlike = False
        elif action == 'unlike':
            if like_unlike.unlike:
                # اگر قبلا دیسلایک کرده، دیسلایک را برمی‌دارد
                like_unlike.unlike = False
            else:
                like_unlike.unlike = True
                like_unlike.like = False

        like_unlike.save()

        # تعداد لایک‌ها و دیسلایک‌های فعلی
        likes_count = comment.likes.filter(like=True).count()
        unlikes_count = comment.likes.filter(unlike=True).count()

        return JsonResponse({
            'success': True,
            'likes_count': likes_count,
            'unlikes_count': unlikes_count,
            'user_liked': like_unlike.like,
            'user_unliked': like_unlike.unlike
        })

    return JsonResponse({
        'success': False,
        'message': 'خطا در ثبت واکنش'
    }, status=400)

# ویو برای دریافت نظرات با صفحه‌بندی
def get_comments_ajax(request, product_slug):
    if request.method == 'GET':
        product = get_object_or_404(Product, slug=product_slug, isActive=True)
        page = int(request.GET.get('page', 1))
        comments_per_page = 5

        # نظرات والد (بدون parent)
        comments = product.comments.filter(
            isActive=True,
            parent__isnull=True
        ).select_related('user').prefetch_related('replies')

        # محاسبه صفحه‌بندی
        total_comments = comments.count()
        start_index = (page - 1) * comments_per_page
        end_index = start_index + comments_per_page

        comments_page = comments[start_index:end_index]

        # ساختار داده‌ای برای پاسخ
        comments_data = []
        for comment in comments_page:
            comment_data = {
                'id': comment.id,
                'user_name': comment.user.get_full_name() or comment.user.username,
                'text': comment.text,
                'is_suggest': comment.is_suggest,
                'created_at': comment.get_jalali_date(),
                'replies': []
            }

            # پاسخ‌های این نظر
            for reply in comment.replies.filter(isActive=True):
                reply_data = {
                    'id': reply.id,
                    'user_name': reply.user.get_full_name() or reply.user.name,
                    'text': reply.text,
                    'created_at': reply.get_jalali_date(),
                }
                comment_data['replies'].append(reply_data)

            comments_data.append(comment_data)

        return JsonResponse({
            'comments': comments_data,
            'has_next': end_index < total_comments,
            'current_page': page,
            'total_pages': (total_comments + comments_per_page - 1) // comments_per_page
        })

# -------------------------- shop ------------------------------


def best_selling_products_view(request):
    """
    نمایش پرفروش‌ترین محصولات بر اساس تعداد فروش
    """
    # محاسبه تعداد فروش هر محصول
    best_selling_products = Product.objects.filter(
        orderItems__order__isFinally=True
    ).annotate(
        total_sold=Sum('orderItems__qty')
    ).filter(
        total_sold__gt=0
    ).order_by('-total_sold')[:20]

    product_list = []
    for product in best_selling_products:
        likes_count = LikeOrUnlike.objects.filter(product=product, like=True).count()
        unlikes_count = LikeOrUnlike.objects.filter(product=product, unlike=True).count()
        total_votes = likes_count + unlikes_count

        comments = Comment.objects.filter(product=product, isActive=True)
        comments_count = comments.count()

        if total_votes > 0:
            rating = 4 + (likes_count - unlikes_count) / (total_votes * 10)
            rating = max(3.5, min(rating, 5.0))  # Clamp between 3.5 and 5.0
        else:
            rating = 4.0

        colors = product.features_value.filter(feature__title='رنگ').values_list('value', flat=True)

        product_data = {
            'product': product,
            'image_url': product.image.url if product.image else '',
            'short_title': product.title,
            'brand': product.brand.title,
            'price': product.price,
            'colors': colors,
            'rating': round(rating, 1),
            'comments_count': comments_count,
            'total_sold': product.total_sold,  # تعداد فروش
        }
        product_list.append(product_data)

    context = {
        'products': product_list,
    }
    return render(request, 'product_app/best_selling_products.html', context)



def get_products_filter(request, *args, **kwargs):
    """فیلتر دسته‌بندی محصولات"""
    products_group = Category.objects.annotate(
        product_count=Count('products', filter=Q(products__isActive=True))
    ).filter(
        isActive=True,
        product_count__gt=0
    ).order_by('-product_count')

    return render(request, 'product_app/partials/group_filter_pc.html', {
        'groups': products_group
    })

def show_brand_products(request, *args, **kwargs):
    """نمایش محصولات مربوط به یک برند خاص با فیلتر، مرتب‌سازی و پیجینیشن"""
    slug = kwargs['slug']
    brand = get_object_or_404(Brand, slug=slug, isActive=True)

    # دریافت شماره صفحه از درخواست
    page_number = request.GET.get('page', 1)

    # کوئری پایه
    products = Product.objects.filter(
        isActive=True,
        brand=brand
    ).select_related('brand').prefetch_related(
        'features_value',
        'features_value__filterValue'
    )

    # محدوده قیمت
    result_price = products.aggregate(
        max_price=Max('price'),
        min_price=Min('price')
    )

    # اعمال فیلترها
    filter_obj = ProductFilter(request.GET, queryset=products)
    products = filter_obj.qs

    # فیلتر ویژگی‌ها
    feature_filter = request.GET.getlist('feature')
    if feature_filter:
        products = products.filter(
            features_value__filterValue__id__in=feature_filter
        ).distinct()

    # مرتب‌سازی
    sort = request.GET.get('sort')
    if sort == '1':
        products = products.order_by('-createAt')
    elif sort == '2':
        products = products.order_by('-price')
    elif sort == '3':
        products = products.order_by('price')
    elif sort == '4':
        products = products.annotate(
            total_sold=Sum('orders_details_product__qty')
        ).order_by('-total_sold')
    else:
        products = products.order_by('-createAt')

    # پیجینیشن
    paginator = Paginator(products, 8)
    page_obj = paginator.get_page(page_number)

    # پاسخ AJAX برای Load More
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        products_data = []
        for product in page_obj:
            product_data = {
                'id': product.id,
                'title': product.title,
                'brand': product.brand.title,
                'image_url': product.image.url if product.image else '',
                'price': product.price,
                'avg_rating': product.avg_rating,
                'comments_count': product.comments.count(),
                'url': product.get_absolute_url(),
                'colors': []
            }

            for feature in product.features_value.all():
                if feature.feature.title == "رنگ" and feature.filterValue:
                    product_data['colors'].append({'value': feature.filterValue.value})

            products_data.append(product_data)

        return JsonResponse({
            'products': products_data,
            'has_next': page_obj.has_next(),
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None
        })

    # متاتگ برند
    meta_context = {}
    if hasattr(brand, 'meta_tag'):
        meta_context = brand.meta_tag.get_meta_context(request)

    # پاسخ HTML
    context = {
        'products': page_obj,
        'result_price': result_price,
        'brand': brand,
        'filter': filter_obj,
        **meta_context,  # اضافه شدن متاتگ‌ها به context
    }

    return render(request, 'product_app/brand_products.html', context)



def top_brands_view_category(request):
    """
    Fetches top brands sorted by the number of active products.
    """
    brands = Brand.objects.filter(isActive=True).annotate(
        product_count=Count('products')
    ).order_by('-product_count')[:10]  # Get the top 10 brands

    context = {
        'brands': brands,
    }
    return render(request, 'product_app/partials/brand_filter_pc.html', context)



def get_feature_filter(request, *args, **kwargs):
    """فیلتر ویژگی‌ها"""
    slug = kwargs['slug']
    group_product = get_object_or_404(Category, slug=slug)

    # بارگذاری مرتبط برای بهینه‌سازی
    feature_list = group_product.features.prefetch_related('feature_values')
    feature_dict = {}

    for feature in feature_list:
        feature_dict[feature] = feature.feature_values.all()

    return render(request, 'product_app/partials/feature_list_filer.html', {
        'feature_dict': feature_dict
    })

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Max, Min, Sum
from .models import Product, Category, MetaTag
from .filters import ProductFilter
def show_by_filter(request, *args, **kwargs):
    """نمایش محصولات با فیلترهای اعمال‌شده"""
    slug = kwargs['slug']
    group = get_object_or_404(Category, slug=slug)

    # شماره صفحه از درخواست
    page_number = request.GET.get('page', 1)

    # کوئری پایه محصولات فعال در این دسته
    products = Product.objects.filter(
        isActive=True,
        categories=group
    ).select_related('brand').prefetch_related(
        'features_value',
        'features_value__filterValue'
    ).distinct()

    # محدوده قیمت کل محصولات برای نمایش در اسلایدر
    result_price = products.aggregate(
        max_price=Max('price'),
        min_price=Min('price')
    )

    # اعمال فیلترهای django-filter
    filter_obj = ProductFilter(request.GET, queryset=products)
    products = filter_obj.qs

    # ✅ فیلتر محدوده قیمت
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')

    if price_min and price_max:
        try:
            price_min = int(price_min)
            price_max = int(price_max)
            products = products.filter(price__gte=price_min, price__lte=price_max)
        except ValueError:
            pass
    elif price_min:
        try:
            price_min = int(price_min)
            products = products.filter(price__gte=price_min)
        except ValueError:
            pass
    elif price_max:
        try:
            price_max = int(price_max)
            products = products.filter(price__lte=price_max)
        except ValueError:
            pass

    # ✅ اصلاح شده: فیلتر ویژگی‌ها با منطق OR
    feature_filter = request.GET.getlist('feature')
    if feature_filter:
        # استفاده از Q objects برای منطق OR
        from django.db.models import Q
        feature_query = Q()
        for f_id in feature_filter:
            feature_query |= Q(features_value__filterValue__id=f_id)
        products = products.filter(feature_query).distinct()

    # ✅ فیلتر برند
    brand_filter = request.GET.getlist('brand')
    if brand_filter:
        products = products.filter(brand__id__in=brand_filter)

    # مرتب‌سازی
    sort = request.GET.get('sort')
    if sort == '1':
        products = products.order_by('-createAt')  # جدیدترین
    elif sort == '2':
        products = products.order_by('-price')      # گران‌ترین
    elif sort == '3':
        products = products.order_by('price')       # ارزان‌ترین
    elif sort == '4':
        products = products.annotate(
            total_sold=Sum('orders_details_product__qty')
        ).order_by('-total_sold')                   # پرفروش‌ترین
    else:
        products = products.order_by('-createAt')

    # صفحه‌بندی
    paginator = Paginator(products, 4)
    page_obj = paginator.get_page(page_number)

    # ✅ بهبود: ساخت feature_dict برای نمایش در فیلترها
    from django.db.models import Count
    feature_dict = {}
    features_in_category = Feature.objects.filter(categories=group)

    for feature in features_in_category:
        # فقط مقادیری که در محصولات فعلی وجود دارند
        values = FeatureValue.objects.filter(
            feature=feature,
            productfeature__product__in=products
        ).annotate(
            product_count=Count('productfeature__product')
        ).filter(product_count__gt=0).distinct()

        if values.exists():
            feature_dict[feature] = values

    # پاسخ برای AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        products_data = []
        for product in page_obj:
            product_data = {
                'id': product.id,
                'title': product.title,
                'brand': product.brand.title,
                'image_url': product.image.url if product.image else '',
                'price': product.price,
                'avg_rating': product.avg_rating,
                'comments_count': product.comments.count(),
                'url': product.get_absolute_url(),
                'colors': []
            }
            for feature in product.features_value.all():
                if feature.feature.title == "رنگ":
                    product_data['colors'].append({'value': feature.filterValue.value})
            products_data.append(product_data)

        return JsonResponse({
            'products': products_data,
            'has_next': page_obj.has_next(),
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None
        })

    # متاتگ‌ها
    try:
        meta_tag = group.meta_tag
        meta_context = meta_tag.get_meta_context(request)
    except MetaTag.DoesNotExist:
        meta_context = {
            "title": group.title,
            "description": f"محصولات دسته‌بندی {group.title}",
            "robots": "index, follow",
            "og_type": "website",
            "og_site_name": "سامسونگ مرکزی آذربایجان",
            "og_title": group.title,
            "og_description": f"محصولات دسته‌بندی {group.title}",
            "og_image": request.build_absolute_uri("/media/default/og-image.jpg"),
            "og_url": request.build_absolute_uri(),
            "twitter_card": "summary_large_image",
            "twitter_title": group.title,
            "twitter_description": f"محصولات دسته‌بندی {group.title}",
            "twitter_image": request.build_absolute_uri("/media/default/og-image.jpg"),
        }

    # داده‌ها برای قالب
    context = {
        'products': page_obj,
        'result_price': result_price,
        'slug': slug,
        'group': group,
        'filter': filter_obj,
        'feature_dict': feature_dict,  # ✅ اضافه شده
        'price_min': price_min or result_price["min_price"],
        'price_max': price_max or result_price["max_price"],
        **meta_context
    }

    return render(request, 'product_app/shop.html', context)




def get_categories_menu(request):
    """
    دریافت دسته‌بندی‌های اصلی برای منوی ساده
    """
    try:
        # دریافت فقط دسته‌بندی‌های اصلی (سطح اول)
        main_categories = Category.objects.filter(
            parent__isnull=True,
            isActive=True
        ).annotate(
            product_count=Count('products')
        ).order_by('-product_count', 'title')[:8]

        categories_data = []

        for category in main_categories:
            categories_data.append({
                'id': category.id,
                'title': category.title,
                'slug': category.slug,
                'product_count': category.product_count,
            })

        return JsonResponse({
            'success': True,
            'categories': categories_data
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })




from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import Wishlist, Product

@login_required
@require_POST
def add_to_wishlist(request, product_id):
    """افزودن محصول به علاقه‌مندی‌ها"""
    try:
        product = Product.objects.get(id=product_id, isActive=True)

        # بررسی وجود محصول در علاقه‌مندی‌ها
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )

        if created:
            return JsonResponse({
                'success': True,
                'message': 'محصول به علاقه‌مندی‌ها اضافه شد',
                'action': 'added'
            })
        else:
            return JsonResponse({
                'success': True,
                'message': 'این محصول قبلاً در علاقه‌مندی‌ها وجود دارد',
                'action': 'already_exists'
            })

    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'محصول یافت نشد'
        })


@login_required
@require_POST
def remove_from_wishlist(request, product_id):
    """حذف محصول از علاقه‌مندی‌ها"""
    try:
        deleted_count = Wishlist.objects.filter(
            user=request.user,
            product_id=product_id
        ).delete()[0]

        if deleted_count > 0:
            return JsonResponse({
                'success': True,
                'message': 'محصول از علاقه‌مندی‌ها حذف شد',
                'action': 'removed'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'این محصول در علاقه‌مندی‌ها وجود ندارد'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'خطا در حذف محصول'
        })

@login_required
def wishlist_view(request):
    """صفحه علاقه‌مندی‌های کاربر"""
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')

    # محاسبه اطلاعات محصولات
    wishlist_products = []
    for item in wishlist_items:
        product = item.product
        wishlist_products.append({
            'id': product.id,
            'title': product.title,
            'image_url': product.image.url if product.image else '',
            'brand': product.brand.title,
            'price': product.price,
            'final_price': product.get_price_by_discount(),
            'discount_percentage': product.get_discount_percentage(),
            'rating': product.avg_rating,
            'comments_count': product.comments.count(),
            'url': product.get_absolute_url(),
            'added_date': item.created_at
        })

    context = {
        'wishlist_products': wishlist_products,
    }

    return render(request, 'product_app/wishlist.html', context)

def get_filter_value_for_feature(request):
    if request.method == 'GET':
        feature_id = request.GET['feature_id']
        feature_values = FeatureValue.objects.filter(feature_id=feature_id)

        # استفاده از فیلد value که در مدل وجود دارد
        res = {fv.value: fv.id for fv in feature_values}
        print(res,'this is res')
        return JsonResponse(data=res, safe=False)