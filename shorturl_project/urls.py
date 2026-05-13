"""
URL configuration for shorturl_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path
from core import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.index,name='index'),
    path('api/shorten/',views.shorten_api,name='shorten_api'),
    path('api/stats/',views.stats_api,name='stats_api'),
    path('<str:short_code>/',views.redirect_view,name='redirect'),
    path('',views.index,name='index'),
]
