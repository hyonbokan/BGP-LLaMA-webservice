from django.contrib import admin
from django.urls import path, include, re_path
from . import views

from django.conf.urls.static import static
from django.conf import settings

from . import user_login

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/',include('django.contrib.auth.urls')),
    path('404',views.PAGE_NOT_FOUND, name='404'),
    path('api/', include('app_1.urls')),
    re_path(r'^.*$', views.index_react, name='index_react'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)