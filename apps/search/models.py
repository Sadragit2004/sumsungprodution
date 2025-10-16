from django.db import models
from django.utils import timezone
from apps.product.models import Product, Category

# ========================
# تاریخچه جستجو
# ========================
class SearchHistory(models.Model):
    user = models.ForeignKey('user.CustomUser', on_delete=models.CASCADE, verbose_name="کاربر", null=True, blank=True)
    query = models.CharField(max_length=200, verbose_name="عبارت جستجو")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاریخ جستجو")
    session_key = models.CharField(max_length=100, blank=True, null=True, verbose_name="کلید نشست")

    class Meta:
        verbose_name = "تاریخچه جستجو"
        verbose_name_plural = "تاریخچه جستجوها"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.query} - {self.user if self.user else 'مهمان'}"

# ========================
# جستجوهای پرتکرار
# ========================
class PopularSearch(models.Model):
    query = models.CharField(max_length=200, unique=True, verbose_name="عبارت جستجو")
    count = models.PositiveIntegerField(default=1, verbose_name="تعداد جستجو")
    last_searched = models.DateTimeField(default=timezone.now, verbose_name="آخرین جستجو")

    class Meta:
        verbose_name = "جستجوی پرتکرار"
        verbose_name_plural = "جستجوهای پرتکرار"
        ordering = ['-count', '-last_searched']

    def __str__(self):
        return f"{self.query} ({self.count})"