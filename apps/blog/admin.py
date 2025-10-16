from django.contrib import admin
from .models import Author, Category, Tag, MetaTags, BlogPost

# پنل ادمین Author
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'user', 'website']
    search_fields = ['display_name', 'user__username']

# پنل ادمین Category
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ['name']}

# پنل ادمین Tag
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ['name']}

# پنل ادمین MetaTags
class MetaTagsAdmin(admin.ModelAdmin):
    list_display = ['name', 'title', 'og_type']
    search_fields = ['name', 'title']

# پنل ادمین BlogPost
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'is_featured', 'publish_at']
    list_filter = ['status', 'category', 'is_featured', 'publish_at']
    search_fields = ['title', 'excerpt', 'author__display_name']
    prepopulated_fields = {'slug': ['title']}

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'slug', 'author', 'category', 'tags')
        }),
        ('محتوای پست', {
            'fields': ('excerpt', 'content', 'cover_image', 'description')
        }),
        ('تنظیمات', {
            'fields': ('status', 'is_featured', 'publish_at', 'reading_time')
        }),
        ('SEO', {
            'fields': ('seo_title', 'seo_description', 'meta_tags')
        }),
    )

# ثبت همه مدل‌ها
admin.site.register(Author, AuthorAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(MetaTags, MetaTagsAdmin)
admin.site.register(BlogPost, BlogPostAdmin)