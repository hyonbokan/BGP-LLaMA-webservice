from django.contrib import admin
from django.urls import path, include, re_path
from app_1.views import *
from .views import views
from django.urls import path
from app_1.views import gpt_views, bgp_views, code_execution_views, status_views

# urlpatterns = [
#     path('bgp_llama', views.bgp_llama, name='bgp-llama'),
#     path('gpt_4o_mini', views.gpt_4o_mini, name='gpt-4o-mini'),
#     path('execute_code', views.execute_code, name='execute_code'),
#     path('download', views.download_file_with_query, name='api-download-file-query'),
#     # path('finetuning', views.finetune_model, name='finetune_model'), 
#     path('get_csrf_token', views.get_csrf_token, name='get_csrf_token'),
#     re_path(r'.*', views.catch_all),
# ]

urlpatterns = [
    path('bgp_llama/', bgp_views.bgp_llama, name='bgp-llama'),
    path('gpt_4o_mini/', gpt_views.gpt_4o_mini, name='gpt_4o_mini'),
    path('execute_code/', code_execution_views.execute_code, name='execute_code'),
    path('download/', views.download_file_with_query, name='api-download-file-query'),
    path('get_csrf_token/', status_views.get_csrf_token, name='get_csrf_token'),
    path('status_updates/', status_views.status_updates, name='status_updates'),
    re_path(r'.*', views.catch_all),
]