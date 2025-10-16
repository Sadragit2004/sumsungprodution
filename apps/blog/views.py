from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, DetailView
from django.utils import timezone
from django.db.models import Q
from .models import BlogPost, Category, Tag
from django.views.generic import ListView
from django.utils import timezone
from django.db.models import Q
from django.http import Http404

class BlogListView(ListView):
    model = BlogPost
    paginate_by = 6  # منطبق با تعداد کارت‌ها در صفحه
    context_object_name = 'posts'
    template_name = 'blog_app/blog_list.html'

    def get_queryset(self):
        qs = BlogPost.objects.filter(
            status='published'
        ).filter(
            Q(publish_at__lte=timezone.now()) | Q(publish_at__isnull=True)
        ).select_related('author', 'category').prefetch_related('tags').order_by('-publish_at', '-created_at')

        # فیلتر براساس دسته‌بندی
        category_slug = self.request.GET.get('category')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)

        # فیلتر براساس تگ
        tag_slug = self.request.GET.get('tag')
        if tag_slug:
            qs = qs.filter(tags__slug=tag_slug)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['popular_posts'] = BlogPost.objects.filter(
            status='published'
        ).filter(
            Q(publish_at__lte=timezone.now()) | Q(publish_at__isnull=True)
        ).order_by('-views')[:5]

        # برای هایلایت کردن دسته‌بندی فعال
        context['active_category'] = self.request.GET.get('category', '')
        return context

def post_detail_view(request, slug):
    post = get_object_or_404(
        BlogPost.objects.select_related('author', 'category', 'meta_tags').prefetch_related('tags'),
        slug=slug,
        status='published'
    )

    # بررسی زمان انتشار
    if post.publish_at and post.publish_at > timezone.now():
        raise Http404("Post not published yet")

    # افزایش بازدید
    post.increment_views()

    # مقالات مرتبط
    related_qs = BlogPost.objects.filter(status='published').exclude(pk=post.pk)
    related_by_tags = None
    tags = post.tags.all()

    if tags.exists():
        related_by_tags = related_qs.filter(tags__in=tags).distinct().select_related('author', 'category')[:3]  # فقط 3 مقاله

    if related_by_tags and related_by_tags.exists():
        related = related_by_tags
    else:
        if post.category:
            related = related_qs.filter(category=post.category)[:3]
        else:
            related = related_qs.order_by('-views')[:3]

    # گرفتن متا تگ‌ها
    meta_tags = post.get_meta_tags()

    # اگر OG URL پر نشده، URL کامل پست را قرار می‌دهیم
    if not meta_tags.get('og_url'):
        meta_tags['og_url'] = request.build_absolute_uri(post.get_absolute_url())

    # اگر canonical_url پر نشده، URL کامل پست را قرار می‌دهیم
    if not meta_tags.get('canonical_url'):
        meta_tags['canonical_url'] = request.build_absolute_uri(post.get_absolute_url())

    # اگر OG Image پر نشده اما پست کاور تصویر دارد، از آن استفاده می‌کنیم
    if not meta_tags.get('og_image') and post.cover_image:
        meta_tags['og_image'] = request.build_absolute_uri(post.cover_image.url)

    # اگر Twitter Image پر نشده اما OG Image دارد، از آن استفاده می‌کنیم
    if not meta_tags.get('twitter_image') and meta_tags.get('og_image'):
        meta_tags['twitter_image'] = meta_tags['og_image']

    context = {
        'post': post,
        'related_posts': related,
        'categories': Category.objects.all(),
        'meta_tags': meta_tags,  # اضافه کردن متا تگ‌ها به context
    }
    return render(request, 'blog_app/detail.html', context)



def blog_main(request):
    """صفحه اصلی — ارسال ۵ مقاله پربازدید"""
    top_blogs = BlogPost.objects.order_by('-views')[:5]

    context = {
        'top_blogs': top_blogs,
    }
    return render(request, 'blog_app/mainBlog.html', context)