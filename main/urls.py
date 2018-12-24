from django.contrib import admin
from django.urls import path
from main import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('login/', auth_views.login, name='login'),
    path('logout/', auth_views.logout, name='logout'),
]
