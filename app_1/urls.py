from django.contrib import admin
from django.urls import path, include
from app_1.views import *
from . import views

urlpatterns = [
    path('query_detail/<slug:slug>',views.QUERY_DETAIL,name='query_detail'),
    path('bgp_llama',views.BGP_LLaMA,name='bgp_llama'),
    path('dataset', views.DATASET, name='dataset'),
    # path('', )
]

