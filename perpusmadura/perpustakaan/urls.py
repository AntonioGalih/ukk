from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/buku/', views.book_manage, name='book_manage'),
    path('dashboard/users/', views.user_manage, name='user_manage'),
    path('dashboard/pengaturan/', views.settings_view, name='settings'),
    path('scan-qr/', views.scan_qr_view, name='scan_qr'),
    path('perpanjang/<int:id>/', views.extend_borrowing, name='extend_borrowing'),
]