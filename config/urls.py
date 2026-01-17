"""
URL configuration for EduAI project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # API Routes
    path('api/auth/', include('apps.users.urls')),
    path('api/courses/', include('apps.courses.urls')),
    path('api/assessments/', include('apps.assessments.urls')),
    path('api/gamification/', include('apps.gamification.urls')),
    path('api/certificates/', include('apps.certificates.urls')),
    path('api/recommendations/', include('apps.recommendations.urls')),
    path('api/roadmaps/', include('apps.roadmaps.urls')),

    # Health check
    path('api/health/', include('apps.users.health_urls')),

    # Allauth (for social auth callbacks)
    path('accounts/', include('allauth.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
