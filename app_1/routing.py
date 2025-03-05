# app_1/routing.py
from django.urls import re_path
from app_1.consumers.llm_consumer import LLMConsumer
from app_1.consumers.gpt_consumer import GPTConsumer
from app_1.consumers.code_execution import CodeExecutionConsumer

websocket_urlpatterns = [
    re_path(r"ws/llm/$", LLMConsumer.as_asgi()),
    re_path(r"ws/gpt/$", GPTConsumer.as_asgi()),
    re_path(r"ws/execute_code/$", CodeExecutionConsumer.as_asgi()),
]
