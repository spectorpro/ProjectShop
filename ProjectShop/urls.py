from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from mailing.views import dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('mailing.urls')),

    # Авторизация
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Дашборд
    path('dashboard/', dashboard, name='dashboard'),
]
