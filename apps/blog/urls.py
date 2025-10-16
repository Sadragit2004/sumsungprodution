from django.urls import path
from .views import blog_main,BlogListView, post_detail_view

app_name = 'blog'

urlpatterns = [
    path('', BlogListView.as_view(), name='list'),
    path('<slug:slug>', post_detail_view, name='detail'),
    path('f/blogmain/',blog_main , name='blogmain'),
]
