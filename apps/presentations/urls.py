from django.urls import path
from . import views

app_name = 'presentations'

urlpatterns = [
    path('', views.home, name='home'),
    path('home/content/', views.home_content, name='home_content'),
    path('upload/', views.upload_presentation, name='upload'),
    path('upload/htmx/', views.upload_presentation_htmx, name='upload_htmx'),
    path('presentation/<int:pk>/status/', views.check_presentation_status, name='check_status'),
    path('presentation/<int:pk>/badge/', views.check_presentation_badge, name='check_badge'),
    path('presentation/<int:pk>/', views.presentation_detail, name='presentation_detail'),
    path('presentation/<int:pk>/delete/', views.delete_presentation, name='delete_presentation'),
    path('presentation/<int:pk>/delete/htmx/', views.delete_presentation_htmx, name='delete_presentation_htmx'),
    path('presentar/<int:pk>/', views.presentation_mode, name='presentation_mode'),
    path('presentar/<int:pk>/slide/<int:slide_number>/', views.presentation_slide, name='presentation_slide'),
    path('list/', views.presentation_list, name='list'),
    path('list/content/', views.presentation_list_content, name='list_content'),
    path('config/', views.camera_config, name='camera_config'),
]