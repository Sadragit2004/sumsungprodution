from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from apps.product.models import Product, Category
from .models import SearchHistory, PopularSearch

@require_GET
@csrf_exempt
def search_suggestions(request):
    """پیشنهادات جستجو برای بخش هدر"""
    query = request.GET.get('q', '').strip()

    # پاسخ پیش‌فرض
    response_data = {
        'products': [],
        'categories': [],
        'popular_searches': [],
        'total_products': 0,
        'total_categories': 0
    }

    if not query or len(query) < 2:
        return JsonResponse(response_data)

    try:
        # ذخیره تاریخچه جستجو
        if request.user.is_authenticated:
            SearchHistory.objects.create(user=request.user, query=query)
        else:
            session_key = request.session.session_key
            if session_key:
                SearchHistory.objects.create(session_key=session_key, query=query)

        # به‌روزرسانی جستجوهای پرتکرار
        popular_search, created = PopularSearch.objects.get_or_create(
            query__iexact=query,
            defaults={'query': query, 'count': 1}
        )
        if not created:
            popular_search.count += 1
            popular_search.last_searched = timezone.now()
            popular_search.save()

        # جستجوی محصولات - استفاده از icontains برای جستجوی جزئی
        products = Product.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__title__icontains=query),
            isActive=True
        ).select_related('brand').prefetch_related('categories')[:8]

        # جستجوی دسته‌بندی‌ها
        categories = Category.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query),
            isActive=True
        )[:6]

        # جستجوهای پرتکرار مرتبط
        popular_searches = PopularSearch.objects.filter(
            query__icontains=query
        ).exclude(query__iexact=query).order_by('-count')[:5]

        # آماده‌سازی داده محصولات
        product_suggestions = []
        for product in products:
            try:
                product_data = {
                    'id': product.id,
                    'title': product.title,
                    'slug': product.slug,
                    'price': product.price,
                    'final_price': product.get_price_by_discount(),
                    'image_url': product.image.url if product.image else '',
                    'brand': product.brand.title if product.brand else '',
                    'url': product.get_absolute_url(),
                    'has_discount': product.get_discount_percentage() > 0,
                    'discount_percentage': product.get_discount_percentage(),
                    'avg_rating': getattr(product, 'avg_rating', 0)
                }
                product_suggestions.append(product_data)
            except Exception as e:
                print(f"Error processing product {product.id}: {e}")
                continue

        # آماده‌سازی داده دسته‌بندی‌ها
        category_suggestions = []
        for category in categories:
            try:
                category_data = {
                    'id': category.id,
                    'title': category.title,
                    'slug': category.slug,
                    'image_url': category.image.url if category.image else '',
                    'url': category.get_absolute_url(),
                    'product_count': category.products.filter(isActive=True).count()
                }
                category_suggestions.append(category_data)
            except Exception as e:
                print(f"Error processing category {category.id}: {e}")
                continue

        # آماده‌سازی جستجوهای پرتکرار
        popular_suggestions = [{'query': ps.query, 'count': ps.count} for ps in popular_searches]

        response_data.update({
            'products': product_suggestions,
            'categories': category_suggestions,
            'popular_searches': popular_suggestions,
            'total_products': products.count(),
            'total_categories': categories.count()
        })

    except Exception as e:
        print(f"Search error: {e}")
        # در صورت خطا، پاسخ خالی برگردانید

    return JsonResponse(response_data)



def search_results(request):
    """صفحه نتایج جستجوی کامل"""
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '')
    sort_by = request.GET.get('sort', 'relevance')

    products = Product.objects.filter(isActive=True)
    categories = Category.objects.filter(isActive=True)

    if query:
        products = products.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__title__icontains=query) |
            Q(features_value__value__icontains=query)
        ).distinct()

    if category_slug:
        products = products.filter(categories__slug=category_slug)

    # مرتب‌سازی
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-createAt')
    elif sort_by == 'popular':
        products = products.order_by('-createAt')  # می‌توانید منطق محبوبیت را اضافه کنید
    else:  # relevance
        products = products.order_by('-createAt')

    context = {
        'query': query,
        'products': products,
        'categories': categories,
        'selected_category': category_slug,
        'sort_by': sort_by,
        'results_count': products.count()
    }

    return render(request, 'search_app/search.html', context)