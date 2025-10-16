from django.urls import path
from . import views


app_name = 'panel'

urlpatterns = [

    path('',views.dashboard,name='dashboard'),
     path('order/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('orders/',views.orders_view,name='orders'),
    path('order/<uuid:order_code>/',views.order_detail,name='orderdetail'),
     path('edit-profile/', views.edit_profile, name='edit_profile'),
     path('purchased_drives/',views.PurchasedDrivesView.as_view(),name='purchased_drives')

]