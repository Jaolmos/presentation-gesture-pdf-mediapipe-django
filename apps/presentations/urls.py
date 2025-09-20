from django.urls import path
from . import views

app_name = 'presentations'

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_presentation, name='upload'),
    path('presentation/<int:pk>/', views.presentation_detail, name='presentation_detail'),
    path('list/', views.presentation_list, name='list'),
]