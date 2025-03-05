# app_1/routing.py
from django.urls import re_path
from app_1.consumers.consumers import LLMConsumer, CodeExecutionConsumer

websocket_urlpatterns = [
    re_path(r"ws/llm/$", LLMConsumer.as_asgi()),
    re_path(r"ws/execute_code/$", CodeExecutionConsumer.as_asgi()),
]
