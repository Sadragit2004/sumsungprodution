from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView
from django.db.models import Avg, Prefetch
from django.db.models import Q
from .models import Product, Comment
from apps.order.models import OrderDetail

class DriveDetailView(DetailView):
    model = Product
    template_name = 'driver_app/driverDetail.html'
    context_object_name = 'drive'

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
                           .filter(isActive=True, isDrive=True),  # فقط درایوها
            slug=slug
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        drive = self.object

        # محاسبه امتیاز متوسط درایو
        comments = drive.comments.filter(isActive=True)
        if comments.exists():
            avg_rating = comments.aggregate(avg=Avg('rating'))['avg']
            context['average_rating'] = round(avg_rating, 1)
        else:
            context['average_rating'] = 0

        # تعداد نظرات
        context['comments_count'] = comments.count()

        # تعداد پیشنهادها
        context['suggest_count'] = comments.filter(is_suggest=True).count()

        # گالری درایو
        context['gallery'] = drive.gallery.all()

        # درایوهای مرتبط (همان برند)
        related_drives = Product.objects.filter(
            brand=drive.brand,
            isActive=True,
            isDrive=True
        ).exclude(id=drive.id).distinct()[:8]
        context['related_drives'] = related_drives

        # ویژگی‌های درایو
        features = drive.features_value.select_related('feature', 'filterValue').all()
        context['features'] = features

        # ========================
        # اضافه کردن متاتگ
        # ========================
        if hasattr(drive, 'meta_tag'):
            context['meta'] = drive.meta_tag.get_meta_context(self.request)
        else:
            # اگر متاتگ نداشت، مقادیر پیش‌فرض
            default_image = drive.image.url if drive.image else self.request.build_absolute_uri("/media/default/og-image.jpg")
            context['meta'] = {
                "title": f"{drive.title} | درایورها | سامسونگ مرکزی آذربایجان",
                "description": drive.short_description(),
                "robots": "index, follow",
                "og_type": "website",
                "og_site_name": "سامسونگ مرکزی آذربایجان",
                "og_title": f"{drive.title} | درایورها | سامسونگ مرکزی آذربایجان",
                "og_description": drive.short_description(),
                "og_image": self.request.build_absolute_uri(default_image),
                "og_url": self.request.build_absolute_uri(),
                "twitter_card": "summary_large_image",
                "twitter_title": f"{drive.title} | درایورها | سامسونگ مرکزی آذربایجان",
                "twitter_description": drive.short_description(),
                "twitter_image": self.request.build_absolute_uri(default_image),
            }

        # ========================
        # اطلاعات اضافی مخصوص درایوها
        # ========================
        context['is_drive'] = True
        context['drive_file'] = drive.drive if drive.isDrive else None
        context['download_link'] = drive.downloadLink

        # آمار فروش درایو
        drive_sales = OrderDetail.objects.filter(
            product=drive,
            order__isFinally=True
        ).count()
        context['drive_sales'] = drive_sales

        # جدیدترین درایوهای همان برند
        latest_brand_drives = Product.objects.filter(
            brand=drive.brand,
            isActive=True,
            isDrive=True
        ).exclude(id=drive.id).order_by('-createAt')[:4]
        context['latest_brand_drives'] = latest_brand_drives

        return context



from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q, Count, Sum
from .models import Product, Brand, Category
from apps.order.models import OrderDetail

# ========================
# ویو نمایش تمام درایوها
# ========================
class AllDrivesView(ListView):
    model = Product
    template_name = 'driver_app/driverlist.html'
    context_object_name = 'drives'

    def get_queryset(self):
        # فقط محصولاتی که درایو هستند و فعالند
        return Product.objects.filter(
            isDrive=True,
            isActive=True
        ).select_related('brand').prefetch_related('categories').order_by('brand__title', '-createAt')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # گروه‌بندی درایورها بر اساس برند
        drives_by_brand = {}
        for drive in context['drives']:
            brand_name = drive.brand.title if drive.brand else "بدون برند"
            if brand_name not in drives_by_brand:
                drives_by_brand[brand_name] = []
            drives_by_brand[brand_name].append(drive)

        context['drives_by_brand'] = drives_by_brand

        return context
# ========================
# ویو نمایش جدیدترین درایوها
# ========================
class NewestDrivesView(ListView):
    model = Product
    template_name = 'driver_app/recentyledriver.html'
    context_object_name = 'drives'
    paginate_by = 20

    def get_queryset(self):
        return Product.objects.filter(
            isDrive=True,
            isActive=True
        ).select_related('brand').prefetch_related('categories').order_by('-createAt')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'جدیدترین درایورها'
        return context

# ========================
# ویو نمایش پرفروش‌ترین درایوها
# ========================
class BestSellingDrivesView(ListView):
    model = Product
    template_name = 'driver_app/bestsaledriver.html'
    context_object_name = 'drives'
    paginate_by = 20

    def get_queryset(self):
        # محاسبه تعداد فروش هر درایو
        return Product.objects.filter(
            isDrive=True,
            isActive=True
        ).annotate(
            total_sold=Count('orderItems')
        ).select_related('brand').prefetch_related('categories').order_by('-total_sold', '-createAt')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'پرفروش‌ترین درایورها'
        return context

# ========================
# ویو نمایش درایوها بر اساس برند
# ========================
