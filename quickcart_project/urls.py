from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Unified App Routing with Namespace Aliases
    path('', include('app.urls')),
    path('', include(('app.urls', 'store'), namespace='store')),
    path('', include(('app.urls', 'cart'), namespace='cart')),
    path('', include(('app.urls', 'accounts'), namespace='accounts')),
    path('', include(('app.urls', 'customer'), namespace='customer')),
    path('', include(('app.urls', 'support'), namespace='support')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
