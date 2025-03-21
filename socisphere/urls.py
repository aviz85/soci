"""
URL configuration for socisphere project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.template import Template, Context
from django.template.loader import get_template
from django.http import HttpResponse
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Create the schema view for Swagger documentation
schema_view = get_schema_view(
    openapi.Info(
        title="SociSphere API",
        default_version='v1',
        description="API documentation for SociSphere social network",
        terms_of_service="https://www.socisphere.com/terms/",
        contact=openapi.Contact(email="contact@socisphere.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Frontend view functions
def home_view(request):
    try:
        template = get_template('index.html')
        context = {'request': request, 'STATIC_URL': settings.STATIC_URL}
        html = template.render(context)
        return HttpResponse(html)
    except Exception as e:
        return HttpResponse(f"Error rendering template: {str(e)}")

def explore_view(request):
    return render(request, 'explore.html')

def login_view(request):
    return render(request, 'auth/login.html')

def register_view(request):
    return render(request, 'auth/register.html')

def profile_view(request):
    return render(request, 'profile/index.html')

def messages_view(request):
    return render(request, 'interactions/messages.html')

def communities_view(request):
    return render(request, 'communities/index.html')

def notifications_view(request):
    return render(request, 'notifications.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # API endpoints
    path('api/users/', include('apps.users.urls')),
    path('api/content/', include('apps.content.urls')),
    path('api/communities/', include('apps.communities.urls')),
    path('api/interactions/', include('apps.interactions.urls')),
    
    # API Documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Frontend views
    path('', home_view, name='home'),
    path('explore/', explore_view, name='explore'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('profile/', profile_view, name='profile'),
    path('messages/', messages_view, name='messages'),
    path('communities/', communities_view, name='communities'),
    path('notifications/', notifications_view, name='notifications'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
