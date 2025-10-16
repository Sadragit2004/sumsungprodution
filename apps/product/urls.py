from django.urls import path
from . import views
from . import drive_view

app_name = "product"

urlpatterns = [
    path("categories/group/", views.category_group_view, name="category_group"),
    path('product/recently',views.latest_products_view,name='recently'),
    path('product/brands',views.top_brands_view,name='brands'),
 # جزئیات محصول
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),

    # ثبت نظر برای محصول
    path('<slug:product_slug>/comment/', views.add_comment, name='add_comment'),

    # لایک/دیسلایک نظر
    path('comment/<int:comment_id>/like/', views.like_unlike_comment, name='like_unlike_comment'),

    # دریافت نظرات با صفحه‌بندی (AJAX)
    path('<slug:product_slug>/comments/', views.get_comments_ajax, name='get_comments_ajax'),
    path('f/ajax_admin/',views.get_filter_value_for_feature,name='filter_value_for_feature '),


    #-------------- shop -----------------------
    path('category/<slug:slug>/',views.show_by_filter,name='shop'),
    path('category/group/filter/',views.get_products_filter,name='category_filter_group'),
    path('category/brand/filter/',views.top_brands_view_category,name='category_filter_brand'),
    path('category/feature/filter/<slug:slug>/',views.get_feature_filter,name='category_filter_feature'),
    path('f/best-selling',views.best_selling_products_view,name='best_selling_products_view'),
    path('brand/<slug:slug>/',views.show_brand_products,name='brand'),
    path('f/categories-menu/', views.get_categories_menu, name='categories_menu'),
   path('f/wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('f/drives/', drive_view.AllDrivesView.as_view(), name='all_drives'),

    # جدیدترین درایوها
    path('drives/newest/', drive_view.NewestDrivesView.as_view(), name='newest_drives'),

    # پرفروش‌ترین درایوها
    path('drives/best-selling/', drive_view.BestSellingDrivesView.as_view(), name='best_selling_drives'),
    path('driver/<slug:slug>/',drive_view.DriveDetailView.as_view(),name='driveDetail')

]


