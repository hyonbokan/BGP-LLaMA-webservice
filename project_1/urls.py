from django.contrib import admin
from django.urls import path, include, re_path
from . import views
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/',include('django.contrib.auth.urls')),
    path('api/', include('app_1.urls')),
    re_path(r'^.*$', views.index_react, name='index_react'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Catch-all pattern to serve React frontend's index.html
urlpatterns += [
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html')),
]