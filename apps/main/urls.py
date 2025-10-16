
from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('',views.main,name='index'),
    path('slider_list_view/',views.slider_list_view,name='slider_list_view'),
    path('slider_main_view/',views.slider_main_view,name='slider_main_view'),
    path('call/',views.call,name='call'),
    path('about/',views.about,name='about')
]
