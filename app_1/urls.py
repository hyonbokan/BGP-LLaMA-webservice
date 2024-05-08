from django.contrib import admin
from django.urls import path, include
from app_1.views import *
from . import views

urlpatterns = [
    path('bgp_llama', views.BGP_LLaMA, name='bgp_llama'),
    path('api/download/<path:file_path>/', views.download_file, name='api-download-file'),
    # path('api/test-download/', views.test_download_view),
]