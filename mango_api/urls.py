from django.contrib import admin
from django.urls import path
from mango_api import views

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', admin.site.urls),
    path('login/', views.LoginUser.as_view(), name='login'),
    path('logout/', views.LogoutUser.as_view(), name='logout'),
    path('fetch_two_days/', views.FetchTwoDays.as_view(), name='fetch_two_days'),
    path('fetch_week/', views.FetchWeek.as_view(), name='fetch_week'),
]
