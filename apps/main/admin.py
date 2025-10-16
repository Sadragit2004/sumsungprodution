from django.contrib import admin
from .models import SliderSite, SliderMain, Banner

@admin.register(SliderSite)
class SliderSiteAdmin(admin.ModelAdmin):
    list_display = (
        'textSlider',
        'altSlide',
        'isActive',
        'registerData',
        'endData',
        'link'
    )
    list_filter = ('isActive', 'registerData', 'endData')
    search_fields = ('textSlider', 'altSlide', 'link')
    actions = ['make_active', 'make_inactive']

    def make_active(self, request, queryset):
        queryset.update(isActive=True)
    make_active.short_description = "فعال کردن اسلایدرهای انتخاب شده"

    def make_inactive(self, request, queryset):
        queryset.update(isActive=False)
    make_inactive.short_description = "غیرفعال کردن اسلایدرهای انتخاب شده"


@admin.register(SliderMain)
class SliderMainAdmin(admin.ModelAdmin):
    list_display = (
        'textSlider',
        'altSlide',
        'isActive',
        'registerData',
        'endData',
        'link'
    )
    list_filter = ('isActive', 'registerData', 'endData')
    search_fields = ('textSlider', 'altSlide', 'link')
    actions = ['make_active', 'make_inactive']

    def make_active(self, request, queryset):
        queryset.update(isActive=True)
    make_active.short_description = "فعال کردن اسلایدرهای اصلی انتخاب شده"

    def make_inactive(self, request, queryset):
        queryset.update(isActive=False)
    make_inactive.short_description = "غیرفعال کردن اسلایدرهای اصلی انتخاب شده"


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = (
        'nameBanner',
        'textBanner',
        'altSlide',
        'isActive',
        'registerData',
        'endData'
    )
    list_filter = ('isActive', 'registerData', 'endData')
    search_fields = ('nameBanner', 'textBanner', 'altSlide')
    actions = ['make_active', 'make_inactive']

    def make_active(self, request, queryset):
        queryset.update(isActive=True)
    make_active.short_description = "فعال کردن بنرهای انتخاب شده"

    def make_inactive(self, request, queryset):
        queryset.update(isActive=False)
    make_inactive.short_description = "غیرفعال کردن بنرهای انتخاب شده"