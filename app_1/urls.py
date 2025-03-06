from django.urls import path, re_path
from app_1.views.asgi_views import (
    get_csrf_token,
    status_updates,
    download_file,
    catch_all,
)

urlpatterns = [
    path('get_csrf_token/', get_csrf_token, name='get_csrf_token'),
    path('status_updates/', status_updates, name='status_updates'),
    path('download', download_file, name='api-download-file'),
    re_path(r'.*', catch_all),
]