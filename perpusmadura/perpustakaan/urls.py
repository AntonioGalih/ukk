from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Manajemen Buku
    path('dashboard/buku/', views.book_manage, name='book_manage'),
    path('dashboard/buku/edit/<int:id>/', views.edit_buku, name='edit_buku'),
    path('dashboard/buku/hapus/<int:id>/', views.hapus_buku, name='hapus_buku'),

    # Manajemen User
    path('dashboard/users/', views.user_manage, name='user_manage'),
    path('dashboard/users/hapus/<int:id>/', views.hapus_user, name='hapus_user'),
    path('dashboard/users/toggle/<int:id>/', views.toggle_user_aktif, name='toggle_user_aktif'),

    # Manajemen Peminjaman
    path('dashboard/peminjaman/', views.peminjaman_manage, name='peminjaman_manage'),
    path('dashboard/peminjaman/kembalikan/<int:id>/', views.kembalikan_buku, name='kembalikan_buku'),

    # Laporan
    path('dashboard/laporan/', views.laporan_view, name='laporan'),
    path('dashboard/laporan/export/', views.export_csv, name='export_csv'),
    path('dashboard/laporan/import/', views.import_csv, name='import_csv'),

    # Katalog & QR
    path('katalog/', views.katalog_view, name='katalog'),
    path('scan-qr/', views.scan_qr_view, name='scan_qr'),

    # Pengaturan & Misc
    path('dashboard/pengaturan/', views.settings_view, name='settings'),
    path('perpanjang/<int:id>/', views.extend_borrowing, name='extend_borrowing'),
]