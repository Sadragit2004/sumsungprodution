from django.db import models
from django.utils import timezone
from ckeditor_uploader.fields import RichTextUploadingField
from django.utils.html import strip_tags
from django.urls import reverse
import jdatetime
from apps.user.models import CustomUser
import utils

# ========================
# Base Model
# ========================
class Base(models.Model):
    title = models.CharField(max_length=150, verbose_name="عنوان")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="نامک (Slug)")
    createAt = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ساخته شده")
    updateAt = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    isActive = models.BooleanField(default=True, verbose_name="فعال / غیرفعال")

    class Meta:
        abstract = True

    def __str__(self):
        return self.title


# ========================
# برند
# ========================
class Brand(Base):
    description = RichTextUploadingField(
        verbose_name="توضیحات برند", config_name="special", blank=True, null=True
    )
    fileupload = utils.FileUpload('images', 'brandFile')
    image = models.ImageField(upload_to=fileupload.upload_to, verbose_name="لوگو", blank=True, null=True)

    class Meta:
        verbose_name = "برند"
        verbose_name_plural = "برندها"

    def get_absolute_url(self):
        return reverse("shop:brand_detail", kwargs={"slug": self.slug})


# ========================
# دسته‌بندی محصول
# ========================
class Category(Base):
    parent = models.ForeignKey(
        "self", verbose_name="والد", related_name="children",
        on_delete=models.CASCADE, null=True, blank=True
    )
    description = RichTextUploadingField(
        verbose_name="توضیحات دسته‌بندی", config_name="special", blank=True, null=True
    )
    fileupload = utils.FileUpload('images', 'categoryFile')
    image = models.ImageField(upload_to=fileupload.upload_to, verbose_name="تصویر", blank=True, null=True)

    class Meta:
        verbose_name = "دسته‌بندی محصول"
        verbose_name_plural = "دسته‌بندی‌ها"

    def short_description(self):
        if self.description:
            clean_text = strip_tags(self.description)
            return clean_text[:150]
        return ""

    def get_absolute_url(self):
        return reverse("product:shop", kwargs={"slug": self.slug})


# ========================
# ویژگی محصول
# ========================
class Feature(Base):
    categories = models.ManyToManyField(Category, verbose_name="دسته‌بندی", related_name="features")

    class Meta:
        verbose_name = "ویژگی"
        verbose_name_plural = "ویژگی‌ها"


# ========================
# محصول
# ========================
class Product(Base):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, verbose_name="برند", related_name="products")
    categories = models.ManyToManyField(Category, verbose_name="دسته‌بندی‌ها", related_name="products")
    description = RichTextUploadingField(
        verbose_name="توضیحات محصول", config_name="special", blank=True, null=True
    )
    price = models.PositiveIntegerField(default=0, verbose_name="قیمت")
    features = models.ManyToManyField(Feature, through="ProductFeature", verbose_name="ویژگی‌ها")

    fileupload = utils.FileUpload('images', 'productFile')
    image = models.ImageField(upload_to=fileupload.upload_to, verbose_name="تصویر اصلی", blank=True, null=True)
    downloadLink = models.URLField(blank=True, null=True, verbose_name="لینک دانلود خارجی (اختیاری)")

    fileDrive = utils.FileUpload('fileUpload','drive')
    drive = models.FileField(verbose_name='درایور',upload_to=fileDrive.upload_to,blank=True,null=True)
    isDrive = models.BooleanField(default=False,verbose_name='ایا درایو هست ',blank=True,null=True)

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"

    def short_description(self):

        if self.description:
            clean_text = strip_tags(self.description)
            return clean_text[:150]
        return ""


    def get_absolute_url(self):
        return reverse("product:product_detail", kwargs={"slug": self.slug})

    def get_discount_percentage(self):
        discounts = [
            dbd.discountBasket.discount
            for dbd in self.productOfDiscount.all()
            if dbd.discountBasket.isActive
            and dbd.discountBasket.startDate <= timezone.now()
            and timezone.now() <= dbd.discountBasket.endDate
        ]
        return max(discounts) if discounts else 0

    def get_price_by_discount(self):
        discount = self.get_discount_percentage()
        return int(self.price - (self.price * discount / 100))




    @property
    def avg_rating(self):
        """محاسبه میانگین امتیاز محصول"""
        comments = self.comments.filter(isActive=True)
        if comments.exists():
            total_rating = sum(comment.rating for comment in comments)
            return round(total_rating / comments.count(), 1)
        return 0

    def get_absolute_url(self):
        return reverse("product:product_detail", kwargs={"slug": self.slug})

# ========================
# مقدار ویژگی
# ========================
class FeatureValue(models.Model):
    feature = models.ForeignKey(
        Feature, on_delete=models.CASCADE, verbose_name="ویژگی",
        null=True, blank=True, related_name="feature_values"
    )
    value = models.CharField(max_length=100, verbose_name="مقدار")

    class Meta:
        verbose_name = "مقدار ویژگی"
        verbose_name_plural = "مقادیر ویژگی‌ها"

    def __str__(self):
        return f"{self.feature} → {self.value}"


# ========================
# ارتباط محصول با ویژگی
# ========================
class ProductFeature(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="محصول", related_name="features_value")
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, verbose_name="ویژگی")
    value = models.CharField(max_length=40, verbose_name="مقدار")
    filterValue = models.ForeignKey(
        FeatureValue, null=True, blank=True,
        on_delete=models.CASCADE, verbose_name="مقدار برای فیلترینگ"
    )

    class Meta:
        verbose_name = "ویژگی محصول"
        verbose_name_plural = "ویژگی‌های محصول"

    def __str__(self):
        return f"{self.product} | {self.feature} = {self.value}"


# ========================
# گالری محصول
# ========================
class ProductGallery(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="محصول", related_name="gallery")
    fileupload = utils.FileUpload('images', 'galleryFile')
    alt = models.CharField(max_length=100, blank=True, null=True, verbose_name="متن جایگزین")
    image = models.ImageField(upload_to=fileupload.upload_to, verbose_name="تصویر")

    class Meta:
        verbose_name = "گالری محصول"
        verbose_name_plural = "گالری محصولات"

    def __str__(self):
        return f"تصویر {self.product.title}"

# نظر کاربران
# ========================
# نظر کاربران
class Comment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="comments", verbose_name="کاربر")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="comments", verbose_name="محصول")
    text = models.TextField(verbose_name="متن نظر")
    is_suggest = models.BooleanField(default=False, verbose_name="پیشنهاد وضعیت")

    # اضافه کردن فیلد rating
    rating = models.PositiveSmallIntegerField(
        default=5,
        verbose_name="امتیاز",
        choices=[(1, '۱ ستاره'), (2, '۲ ستاره'), (3, '۳ ستاره'), (4, '۴ ستاره'), (5, '۵ ستاره')]
    )

    parent = models.ForeignKey("self", on_delete=models.CASCADE, related_name="replies", null=True, blank=True, verbose_name="والد")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    isActive = models.BooleanField(default=False, verbose_name="فعال")

    def get_jalali_date(self):
        return jdatetime.datetime.fromgregorian(datetime=self.created_at).strftime("%Y/%m/%d")

    def __str__(self):
        return f"نظر {self.user} روی {self.product}"

    class Meta:
        verbose_name = "نظر"
        verbose_name_plural = "نظرات"


# ========================
# لایک / دیسلایک
# ========================
class LikeOrUnlike(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="likes", verbose_name="کاربر")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="likes", verbose_name="نظر")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="likes", verbose_name="محصول")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ ثبت")
    like = models.BooleanField(default=False)
    unlike = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} → {self.comment}"

    class Meta:
        verbose_name = "لایک"
        verbose_name_plural = "لایک‌ها"



# ========================
# متاتگ محصولات و دسته‌بندی‌ها (با URL به جای آپلود تصویر)
# ========================

class MetaTag(models.Model):
    # ارتباط با محصول یا دسته‌بندی
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name="meta_tag",
        verbose_name="محصول",
        null=True, blank=True
    )
    category = models.OneToOneField(
        Category,
        on_delete=models.CASCADE,
        related_name="meta_tag",
        verbose_name="دسته‌بندی",
        null=True, blank=True
    )
    brand = models.OneToOneField(
        Brand,
        on_delete=models.CASCADE,
        related_name="meta_tag",
        verbose_name="دسته‌بندی",
        null=True, blank=True
    )

    # فیلدهای متا
    title = models.CharField(
        max_length=200,
        verbose_name="عنوان <title>"
    )
    description = models.TextField(
        verbose_name="توضیحات (meta description)"
    )

    # Open Graph
    og_type = models.CharField(max_length=50, default="website", verbose_name="og:type")
    og_site_name = models.CharField(max_length=150, default="سامسونگ مرکزی آذربایجان", verbose_name="og:site_name")
    og_title = models.CharField(max_length=200, verbose_name="og:title", blank=True, null=True)
    og_description = models.TextField(verbose_name="og:description", blank=True, null=True)
    og_image_url = models.URLField(verbose_name="og:image URL", blank=True, null=True)
    og_url = models.URLField(verbose_name="og:url", blank=True, null=True)

    # Twitter
    twitter_card = models.CharField(max_length=50, default="summary_large_image", verbose_name="twitter:card")
    twitter_title = models.CharField(max_length=200, verbose_name="twitter:title", blank=True, null=True)
    twitter_description = models.TextField(verbose_name="twitter:description", blank=True, null=True)
    twitter_image_url = models.URLField(verbose_name="twitter:image URL", blank=True, null=True)

    class Meta:
        verbose_name = "متاتگ سئو"
        verbose_name_plural = "متاتگ‌ها"

    def __str__(self):
        if self.product:
            return f"متاتگ محصول: {self.product.title}"
        elif self.category:
            return f"متاتگ دسته‌بندی: {self.category.title}"
        return "متاتگ بدون ارتباط"

    def get_meta_context(self, request):
        """تولید context برای استفاده در قالب"""
        default_image = request.build_absolute_uri("/media/default/og-image.jpg")

        return {
            "title": self.title,
            "description": self.description,
            "robots": "index, follow",
            "og_type": self.og_type,
            "og_site_name": self.og_site_name,
            "og_title": self.og_title or self.title,
            "og_description": self.og_description or self.description,
            "og_image": self.og_image_url or default_image,
            "og_url": self.og_url or request.build_absolute_uri(),
            "twitter_card": self.twitter_card,
            "twitter_title": self.twitter_title or self.title,
            "twitter_description": self.twitter_description or self.description,
            "twitter_image": self.twitter_image_url or default_image,
        }


class Wishlist(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="wishlists", verbose_name="کاربر")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlists", verbose_name="محصول")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ افزودن")

    class Meta:
        verbose_name = "علاقه‌مندی"
        verbose_name_plural = "علاقه‌مندی‌ها"
        unique_together = ['user', 'product']

    def __str__(self):
        return f"{self.user} - {self.product}"