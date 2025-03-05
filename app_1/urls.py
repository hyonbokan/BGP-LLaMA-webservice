from django.urls import path, re_path
from django.urls import path
from app_1.views import status_views, base_views


urlpatterns = [
    path('get_csrf_token/', status_views.get_csrf_token, name='get_csrf_token'),
    path('status_updates/', status_views.status_updates, name='status_updates'),
    path('download', base_views.download_file_with_query, name='api-download-file-query'),
    re_path(r'.*', base_views.catch_all),
]