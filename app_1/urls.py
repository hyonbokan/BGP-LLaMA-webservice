from django.contrib import admin
from django.urls import path, include, re_path
from app_1.views import *
from . import views

urlpatterns = [
    path('bgp_llama', views.bgp_llama, name='bgp-llama'),
    path('download', views.download_file_with_query, name='api-download-file-query'),
    # path('finetuning', views.finetune_model, name='finetune_model'), 
    path('get_csrf_token', views.get_csrf_token, name='get_csrf_token'),
    re_path(r'.*', views.catch_all),
]