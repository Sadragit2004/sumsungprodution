from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.db import models

from django.contrib import messages
import jdatetime
from .models import (
    Brand, Category, Product, ProductGallery, Feature, FeatureValue,
    ProductFeature, Comment, LikeOrUnlike, MetaTag, Wishlist
)

# ========================
# فیلترهای سفارشی
# ========================
class PriceLevelFilter(admin.SimpleListFilter):
    title = "بازه قیمتی"
    parameter_name = "price_level"

    def lookups(self, request, model_admin):
        return (
            ("low", "کمتر از 500K"),
            ("mid", "500K تا 2M"),
            ("high", "بیشتر از 2M"),
        )

    def queryset(self, request, queryset):
        if self.value() == "low":
            return queryset.filter(price__lt=500_000)
        if self.value() == "mid":
            return queryset.filter(price__gte=500_000, price__lte=2_000_000)
        if self.value() == "high":
            return queryset.filter(price__gt=2_000_000)
        return queryset

class DriveFilter(admin.SimpleListFilter):
    title = "نوع محصول"
    parameter_name = "is_drive"

    def lookups(self, request, model_admin):
        return (
            ("drives", "درایورها"),
            ("products", "محصولات عادی"),
        )

    def queryset(self, request, queryset):
        if self.value() == "drives":
            return queryset.filter(isDrive=True)
        if self.value() == "products":
            return queryset.filter(isDrive=False)
        return queryset

# ========================
# اینلاین‌ها
# ========================
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1
    fields = ("preview", "image", "alt")
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:8px" />', obj.image.url)
        return "—"
    preview.short_description = "پیش‌نمایش"

class ProductFeatureInline(admin.TabularInline):
    model = ProductFeature
    extra = 1
   
    fields = ("feature", "value", "filterValue")


    class Media:

        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/jquery/3.5.1/jquery.min.js',
            'assets/js/admin_script11.js',)

# ========================
# Brand Admin
# ========================
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("title", "isActive", "products_count", "drives_count", "createAt")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ("isActive", ("createAt", admin.DateFieldListFilter))

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _products_count=Count("products", distinct=True),
            _drives_count=Count("products", filter=models.Q(products__isDrive=True), distinct=True)
        )

    def products_count(self, obj):
        return obj._products_count
    products_count.short_description = "تعداد محصولات"
    products_count.admin_order_field = "_products_count"

    def drives_count(self, obj):
        return obj._drives_count
    drives_count.short_description = "تعداد درایورها"
    drives_count.admin_order_field = "_drives_count"

# ========================
# Category Admin
# ========================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "parent", "isActive", "products_count", "drives_count")
    search_fields = ("title", "slug", "description")
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ("isActive", "parent")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _products_count=Count("products", distinct=True),
            _drives_count=Count("products", filter=models.Q(products__isDrive=True), distinct=True)
        )

    def products_count(self, obj):
        return obj._products_count
    products_count.short_description = "تعداد محصولات"
    products_count.admin_order_field = "_products_count"

    def drives_count(self, obj):
        return obj._drives_count
    drives_count.short_description = "تعداد درایورها"
    drives_count.admin_order_field = "_drives_count"

# ========================
# Feature Admin
# ========================
@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ("title", "isActive", "categories_count", "values_count")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("categories",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _categories_count=Count("categories", distinct=True),
            _values_count=Count("feature_values", distinct=True),
        )

    def categories_count(self, obj):
        return obj._categories_count
    categories_count.short_description = "تعداد دسته‌بندی‌ها"

    def values_count(self, obj):
        return obj._values_count
    values_count.short_description = "تعداد مقادیر"

# ========================
# FeatureValue Admin
# ========================
@admin.register(FeatureValue)
class FeatureValueAdmin(admin.ModelAdmin):
    list_display = ("value", "feature")
    search_fields = ("value", "feature__title")
    list_filter = ("feature",)
    autocomplete_fields = ("feature",)

# ========================
# Product Admin - ادمین اصلی محصولات
# ========================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "thumb", "title", "brand", "price_fmt", "drive_badge",
        "file_status", "isActive", "createAt"
    )
    list_editable = ("isActive",)
    search_fields = ("title", "slug", "description", "brand__title")
    list_filter = (
        "isActive", DriveFilter, "brand", "categories", PriceLevelFilter,
        ("createAt", admin.DateFieldListFilter),
    )
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("categories",)
    readonly_fields = ("thumb_large", "createAt", "updateAt", "file_size_display")
    inlines = (ProductGalleryInline, ProductFeatureInline)
    ordering = ("-createAt",)

    fieldsets = (
        ("اطلاعات اصلی", {
            "fields": (
                "title", "slug", "brand", "categories",
                "description", "price", "isActive"
            )
        }),
        ("تصویر اصلی", {
            "fields": ("image", "thumb_large"),
            "classes": ("collapse",)
        }),
        ("تنظیمات درایور", {
            "fields": (
                "isDrive", "drive", "file_size_display", "downloadLink"
            ),
            "classes": ("collapse",),
            "description": "تنظیمات مخصوص محصولات درایوری"
        }),
        ("تاریخ‌ها", {
            "fields": ("createAt", "updateAt"),
            "classes": ("collapse",)
        }),
    )

    actions = ["make_drive", "remove_drive"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _gallery_count=Count("gallery", distinct=True),
        ).select_related("brand").prefetch_related("categories")

    def price_fmt(self, obj):
        return f"{obj.price:,} تومان" if obj.price else "—"
    price_fmt.short_description = "قیمت"

    def thumb(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:50px;width:50px;object-fit:cover;border-radius:8px" />', obj.image.url)
        return "—"
    thumb.short_description = "تصویر"

    def thumb_large(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:200px;border-radius:12px" />', obj.image.url)
        return "—"
    thumb_large.short_description = "پیش‌نمایش بزرگ"

    def drive_badge(self, obj):
        if obj.isDrive:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">درایور</span>'
            )
        return format_html(
            '<span style="background: #6c757d; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">محصول</span>'
        )
    drive_badge.short_description = "نوع"
    drive_badge.admin_order_field = "isDrive"

    def file_status(self, obj):
        if obj.isDrive:
            if obj.drive:
                size = obj.drive.size
                if size < 1024*1024:
                    size_text = f"{size/1024:.1f} KB"
                else:
                    size_text = f"{size/(1024*1024):.1f} MB"
                return format_html(
                    '<span style="color: #28a745;">✓ فایل ({})</span>', size_text
                )
            elif obj.downloadLink:
                return format_html(
                    '<span style="color: #007bff;">🔗 لینک خارجی</span>'
                )
            return format_html('<span style="color: #dc3545;">✗ بدون فایل</span>')
        return "—"
    file_status.short_description = "وضعیت فایل"

    def file_size_display(self, obj):
        if obj.drive:
            try:
                size = obj.drive.size
                if size < 1024*1024:
                    return f"{size/1024:.1f} KB"
                else:
                    return f"{size/(1024*1024):.1f} MB"
            except:
                return "نامشخص"
        return "—"
    file_size_display.short_description = "حجم فایل"

    @admin.action(description="تبدیل به درایور")
    def make_drive(self, request, queryset):
        updated = queryset.update(isDrive=True)
        self.message_user(
            request,
            f"{updated} محصول با موفقیت به درایور تبدیل شد.",
            messages.SUCCESS
        )

    @admin.action(description="خروج از حالت درایور")
    def remove_drive(self, request, queryset):
        updated = queryset.update(isDrive=False)
        self.message_user(
            request,
            f"{updated} محصول از حالت درایور خارج شد.",
            messages.SUCCESS
        )

# ========================
# Proxy Model برای درایورها - ادمین جداگانه
# ========================
class DriveProduct(Product):
    class Meta:
        proxy = True
        verbose_name = "درایور"
        verbose_name_plural = "درایورها"

@admin.register(DriveProduct)
class DriveProductAdmin(admin.ModelAdmin):
    list_display = (
        "thumb", "title", "brand", "price_fmt", "file_status",
        "file_size", "download_preview", "isActive", "createAt"
    )
    list_editable = ("isActive",)
    search_fields = ("title", "slug", "brand__title")
    list_filter = (
        "isActive", "brand", "categories",
        ("createAt", admin.DateFieldListFilter),
    )
    readonly_fields = ("thumb_large", "createAt", "updateAt", "file_size_display")

    fieldsets = (
        ("اطلاعات اصلی درایور", {
            "fields": (
                "title", "slug", "brand", "categories",
                "description", "price", "isActive"
            )
        }),
        ("فایل درایور", {
            "fields": (
                "drive", "file_size_display", "downloadLink"
            ),
            "description": "آپلود فایل درایور یا وارد کردن لینک دانلود خارجی"
        }),
        ("تصویر", {
            "fields": ("image", "thumb_large"),
            "classes": ("collapse",)
        }),
        ("تاریخ‌ها", {
            "fields": ("createAt", "updateAt"),
            "classes": ("collapse",)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(isDrive=True)

    def price_fmt(self, obj):
        return f"{obj.price:,} تومان" if obj.price else "—"
    price_fmt.short_description = "قیمت"

    def thumb(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:40px;width:40px;object-fit:cover;border-radius:6px" />', obj.image.url)
        return "—"
    thumb.short_description = ""

    def thumb_large(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:200px;border-radius:12px" />', obj.image.url)
        return "—"
    thumb_large.short_description = "پیش‌نمایش بزرگ"

    def file_status(self, obj):
        if obj.drive:
            return format_html('<span style="color: #28a745;">✓ فایل آپلود شده</span>')
        elif obj.downloadLink:
            return format_html('<span style="color: #007bff;">🔗 لینک خارجی</span>')
        return format_html('<span style="color: #dc3545;">✗ بدون فایل</span>')
    file_status.short_description = "وضعیت فایل"

    def file_size(self, obj):
        if obj.drive:
            try:
                size = obj.drive.size
                if size < 1024*1024:
                    return f"{size/1024:.1f} KB"
                else:
                    return f"{size/(1024*1024):.1f} MB"
            except:
                return "—"
        return "—"
    file_size.short_description = "حجم فایل"

    def download_preview(self, obj):
        if obj.downloadLink:
            return format_html(
                '<a href="{}" target="_blank" style="font-size: 12px; background: #007bff; color: white; padding: 2px 8px; border-radius: 4px; text-decoration: none;">مشاهده لینک</a>',
                obj.downloadLink
            )
        return "—"
    download_preview.short_description = "لینک دانلود"

    def file_size_display(self, obj):
        return self.file_size(obj)
    file_size_display.short_description = "حجم فایل"

    def save_model(self, request, obj, form, change):
        obj.isDrive = True
        super().save_model(request, obj, form, change)

# ========================
# ProductGallery Admin
# ========================
@admin.register(ProductGallery)
class ProductGalleryAdmin(admin.ModelAdmin):
    list_display = ("preview", "product", "alt", "product_type")
    search_fields = ("product__title", "alt")
    autocomplete_fields = ("product",)
    list_filter = ("product__isDrive",)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:50px;border-radius:8px" />', obj.image.url)
        return "—"
    preview.short_description = "پیش‌نمایش"

    def product_type(self, obj):
        if obj.product.isDrive:
            return "درایور"
        return "محصول"
    product_type.short_description = "نوع محصول"

# ========================
# ProductFeature Admin
# ========================
@admin.register(ProductFeature)
class ProductFeatureAdmin(admin.ModelAdmin):
    list_display = ("product", "feature", "value", "filterValue", "product_type")
    search_fields = ("product__title", "feature__title", "value")
    autocomplete_fields = ("product", "feature", "filterValue")
    list_filter = ("feature", "product__isDrive")

    def product_type(self, obj):
        if obj.product.isDrive:
            return "درایور"
        return "محصول"
    product_type.short_description = "نوع محصول"





# ========================
# Comment Admin
# ========================
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "text_short", "rating_stars", "product_type", "get_jalali_date", "isActive")
    list_editable = ("isActive",)
    search_fields = ("user__username", "product__title", "text")
    list_filter = ("isActive", "product__isDrive", "product", ("created_at", admin.DateFieldListFilter))
    autocomplete_fields = ("user", "product", "parent")

    def text_short(self, obj):
        return (obj.text[:40] + "...") if len(obj.text) > 40 else obj.text
    text_short.short_description = "متن"

    def rating_stars(self, obj):
        stars = "★" * obj.rating + "☆" * (5 - obj.rating)
        return format_html('<span style="color: gold; font-size: 16px;">{}</span>', stars)
    rating_stars.short_description = "امتیاز"

    def product_type(self, obj):
        if obj.product.isDrive:
            return "درایور"
        return "محصول"
    product_type.short_description = "نوع محصول"

    def get_jalali_date(self, obj):
        return jdatetime.datetime.fromgregorian(datetime=obj.created_at).strftime("%Y/%m/%d")
    get_jalali_date.short_description = "تاریخ ثبت"

# ========================
# LikeOrUnlike Admin
# ========================
@admin.register(LikeOrUnlike)
class LikeOrUnlikeAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "comment_short", "like", "unlike", "product_type", "jalali_date")
    list_filter = ("like", "unlike", "product__isDrive", ("created_at", admin.DateFieldListFilter))
    search_fields = ("user__username", "comment__text", "product__title")
    autocomplete_fields = ("user", "comment", "product")

    def comment_short(self, obj):
        if obj.comment and obj.comment.text:
            return (obj.comment.text[:30] + "...") if len(obj.comment.text) > 30 else obj.comment.text
        return "—"
    comment_short.short_description = "کامنت"

    def product_type(self, obj):
        if obj.product.isDrive:
            return "درایور"
        return "محصول"
    product_type.short_description = "نوع محصول"

    def jalali_date(self, obj):
        return jdatetime.datetime.fromgregorian(datetime=obj.created_at).strftime("%Y/%m/%d")
    jalali_date.short_description = "تاریخ ثبت"

# ========================
# MetaTag Admin
# ========================
@admin.register(MetaTag)
class MetaTagAdmin(admin.ModelAdmin):
    list_display = ("__str__", "title", "product", "category", "brand")
    list_filter = ("product__isDrive", "product", "category", "brand")
    search_fields = ("title", "product__title", "category__title", "brand__title")

    fieldsets = (
        ("ارتباط", {
            "fields": ("product", "category", "brand"),
            "description": "انتخاب محصول، دسته‌بندی یا برند (یکی باید انتخاب شود)."
        }),
        ("Meta اصلی", {
            "fields": ("title", "description"),
        }),
        ("Open Graph", {
            "fields": ("og_type", "og_site_name", "og_title", "og_description", "og_image_url", "og_url"),
        }),
        ("Twitter", {
            "fields": ("twitter_card", "twitter_title", "twitter_description", "twitter_image_url"),
        }),
    )

# ========================
# Wishlist Admin
# ========================
@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "product_type", "jalali_date")
    search_fields = ("user__username", "product__title")
    list_filter = ("product__isDrive", ("created_at", admin.DateFieldListFilter))
    autocomplete_fields = ("user", "product")

    def product_type(self, obj):
        if obj.product.isDrive:
            return "درایور"
        return "محصول"
    product_type.short_description = "نوع محصول"

    def jalali_date(self, obj):
        return jdatetime.datetime.fromgregorian(datetime=obj.created_at).strftime("%Y/%m/%d")
    jalali_date.short_description = "تاریخ افزودن"