from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import F
from django.urls import reverse
from ckeditor_uploader.fields import RichTextUploadingField

# نویسنده: می‌تونیم از User دیجانگو استفاده کنیم یا یک مدل Author مجزا
class Author(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='author_profile')
    display_name = models.CharField(max_length=150)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='authors/avatars/', blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.display_name or str(self.user)


# دسته‌بندی ساده بدون والد
class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


# تگ ساده (اختیاری اما مفید برای related posts)
class Tag(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# مدل متا تگ‌ها
class MetaTags(models.Model):
    """
    مدل برای مدیریت متا تگ‌ها (به جز keywords)
    """
    # فیلدهای عمومی برای شناسایی
    name = models.CharField(max_length=200, verbose_name="نام متا تگ", help_text="یک نام توصیفی برای این مجموعه متا تگ")

    # فیلدهای اصلی متا تگ‌ها
    title = models.CharField(max_length=60, blank=True, verbose_name="متا تایتل",
                           help_text="حداکثر ۶۰ کاراکتر - برای SEO")
    description = models.TextField(max_length=160, blank=True, verbose_name="متا دیسکریپشن",
                                 help_text="حداکثر ۱۶۰ کاراکتر - برای SEO")
    author = models.CharField(max_length=100, blank=True, verbose_name="نویسنده")
    copyright = models.CharField(max_length=100, blank=True, verbose_name="کپی رایت")
    robots = models.CharField(max_length=100, blank=True, default="index, follow",
                            verbose_name="ربات‌ها", help_text="مثال: noindex, nofollow")

    # Open Graph Meta Tags
    og_title = models.CharField(max_length=90, blank=True, verbose_name="OG Title",
                              help_text="حداکثر ۹۰ کاراکتر - برای شبکه‌های اجتماعی")
    og_description = models.TextField(max_length=200, blank=True, verbose_name="OG Description",
                                    help_text="حداکثر ۲۰۰ کاراکتر - برای شبکه‌های اجتماعی")
    og_image = models.ImageField(upload_to='meta/og_images/', blank=True, null=True,
                               verbose_name="OG Image", help_text="تصویر برای نمایش در شبکه‌های اجتماعی")
    og_type = models.CharField(max_length=50, blank=True, default="website",
                             verbose_name="OG Type", help_text="مثال: article, website, product")
    og_url = models.URLField(blank=True, verbose_name="OG URL")

    # Twitter Card Meta Tags
    twitter_card = models.CharField(max_length=50, blank=True, default="summary_large_image",
                                  verbose_name="Twitter Card Type",
                                  help_text="summary, summary_large_image, app, player")
    twitter_site = models.CharField(max_length=100, blank=True, verbose_name="Twitter Site",
                                  help_text="مانند: @username")
    twitter_creator = models.CharField(max_length=100, blank=True, verbose_name="Twitter Creator",
                                     help_text="مانند: @username")
    twitter_title = models.CharField(max_length=70, blank=True, verbose_name="Twitter Title",
                                   help_text="حداکثر ۷۰ کاراکتر")
    twitter_description = models.TextField(max_length=200, blank=True, verbose_name="Twitter Description",
                                         help_text="حداکثر ۲۰۰ کاراکتر")
    twitter_image = models.ImageField(upload_to='meta/twitter_images/', blank=True, null=True,
                                    verbose_name="Twitter Image")

    # سایر متا تگ‌ها
    canonical_url = models.URLField(blank=True, verbose_name="Canonical URL")
    content_type = models.CharField(max_length=50, blank=True, default="text/html; charset=utf-8",
                                  verbose_name="Content Type")
    viewport = models.CharField(max_length=100, blank=True, default="width=device-width, initial-scale=1.0",
                              verbose_name="Viewport")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Meta Tags"
        verbose_name_plural = "Meta Tags"
        ordering = ['-updated_at']

    def __str__(self):
        return self.name

    def get_meta_tags_dict(self):
        """
        بازگرداندن تمام متا تگ‌ها به صورت دیکشنری برای استفاده آسان در تمپلیت
        """
        return {
            'title': self.title,
            'description': self.description,
            'author': self.author,
            'copyright': self.copyright,
            'robots': self.robots,
            'og_title': self.og_title or self.title,
            'og_description': self.og_description or self.description,
            'og_image': self.og_image.url if self.og_image else '',
            'og_type': self.og_type,
            'og_url': self.og_url,
            'twitter_card': self.twitter_card,
            'twitter_site': self.twitter_site,
            'twitter_creator': self.twitter_creator,
            'twitter_title': self.twitter_title or self.title,
            'twitter_description': self.twitter_description or self.description,
            'twitter_image': self.twitter_image.url if self.twitter_image else (self.og_image.url if self.og_image else ''),
            'canonical_url': self.canonical_url,
            'content_type': self.content_type,
            'viewport': self.viewport,
        }


class BlogPost(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, related_name='posts')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='posts')
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')

    excerpt = models.TextField(blank=True)   # اطلاعات تکمیلی کوتاه
    content = models.TextField()             # محتوای بلاگ (Markdown/HTML ذخیره میشه)
    cover_image = models.ImageField(upload_to='blog/covers/', blank=True, null=True)

    description = RichTextUploadingField(
        verbose_name="توضیحات ", config_name="special", blank=True, null=True
    )
    is_featured = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    views = models.PositiveBigIntegerField(default=0)  # شمارنده بازدید

    # متا تگ‌ها - ارتباط با مدل MetaTags
    meta_tags = models.OneToOneField(MetaTags, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='blog_post', verbose_name="متا تگ‌ها")

    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.CharField(max_length=300, blank=True)
    reading_time = models.PositiveSmallIntegerField(blank=True, null=True,
                                                   help_text="Approx minutes. Optional.")

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    publish_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-publish_at', '-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status', 'publish_at']),
        ]

    def __str__(self):
        return self.title

    @property
    def is_published(self):
        if self.status != 'published':
            return False
        if self.publish_at and self.publish_at > timezone.now():
            return False
        return True

    def increment_views(self):
        # افزایش امن با F() تا race condition کم شود
        BlogPost.objects.filter(pk=self.pk).update(views=F('views') + 1)
        # هم‌زمان شئ جاری را آپدیت می‌کنیم تا بعد از فراخوانی view مقدار درست در instance باشد
        self.refresh_from_db(fields=['views'])

    def get_meta_tags(self):
        """
        بازگرداندن متا تگ‌های مربوط به پست
        اگر متا تگ اختصاصی وجود نداشته باشد، از مقادیر پیش‌فرض پست استفاده می‌کند
        """
        if self.meta_tags:
            return self.meta_tags.get_meta_tags_dict()
        else:
            # مقادیر پیش‌فرض از پست
            return {
                'title': self.seo_title or self.title,
                'description': self.seo_description or self.excerpt[:160] if self.excerpt else '',
                'author': self.author.display_name if self.author else '',
                'robots': 'index, follow',
                'og_title': self.seo_title or self.title,
                'og_description': self.seo_description or self.excerpt[:200] if self.excerpt else '',
                'og_image': self.cover_image.url if self.cover_image else '',
                'og_type': 'article',
                'og_url': self.get_absolute_url() if hasattr(self, 'get_absolute_url') else '',
                'twitter_card': 'summary_large_image',
                'canonical_url': self.get_absolute_url() if hasattr(self, 'get_absolute_url') else '',
                'viewport': 'width=device-width, initial-scale=1.0',
            }

    def get_absolute_url(self):
        """
        برای ساخت URL کامل پست (در صورت نیاز)
        """
        from django.urls import reverse
        return reverse('blog:detail', kwargs={'slug': self.slug})