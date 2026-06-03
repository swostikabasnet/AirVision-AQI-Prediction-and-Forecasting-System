"""
URL configuration for airvision project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # AUTH + ACCOUNT APP
    path('', include('accounts.urls')),
    path('accounts/', include('accounts.urls')),

    # Urls for main app views
    path('', views.landing_page, name='landing_page'), # Landing page
    path('user/', views.user_dashboard, name='user_dashboard'),
    path('myadmin/', views.admin_dashboard, name='admin_dashboard'), # Custom URL for admin dashboard to avoid conflict with Django's default admin
    path('forecast/<str:city>/', views.forecast_view, name='forecast'), # Dynamic URL for weather forecast based on city name
    path('search/', views.search_view, name='search'),
    path('aqi/<str:city>/', views.aqi_view, name='aqi'),
    path('users/delete/<int:id>/', views.delete_user, name='delete_user'),#delete users by admin
    path('myadmin/prediction/delete/<int:id>/', views.delete_prediction, name='delete_prediction'),
    path('prediction/view/<int:id>/', views.prediction_detail, name='prediction_detail'), # Detailed report view for individual predictions
    path('prediction_detail/<int:id>/', views.prediction_detail, name='prediction_detail_alias'),
    path('manual_aqi_delete/<int:id>/', views.delete_aqi_record, name='delete_aqi_record'),
    path('predict/', views.get_prediction, name='get_prediction'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
