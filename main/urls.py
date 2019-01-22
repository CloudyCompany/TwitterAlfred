from django.urls import path
from main import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('logout/', auth_views.logout, name='logout'),
    path('getStream/', views.get_twitter_stream),
    path('stream/', views.twitter_stream, name="stream"),
    path('recommendations/', views.recommend),
    path('get_profile_preview/', views.get_profile_preview),
    path('update/', views.updateDB),
    path('stats/', views.get_stats),
]
