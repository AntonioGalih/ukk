from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('tentang-kami/', views.tentang_kami_view, name='tentang_kami'),
    path('pusat-bantuan/', views.pusat_bantuan_view, name='pusat_bantuan'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('buku/<int:id>/', views.book_detail, name='book_detail'),
    path('buku/<int:id>/pinjam/', views.borrow_book, name='borrow_book'),
    path('peminjaman/<int:id>/ajukan-kembali/', views.request_return, name='request_return'),
    path('buku/<int:id>/qr/download/', views.download_book_qr, name='download_book_qr'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Manajemen Buku
    path('dashboard/buku/', views.book_manage, name='book_manage'),
    path('dashboard/buku/edit/<int:id>/', views.edit_buku, name='edit_buku'),
    path('dashboard/buku/hapus/<int:id>/', views.hapus_buku, name='hapus_buku'),

    # Manajemen User
    path('dashboard/users/', views.user_manage, name='user_manage'),
    path('dashboard/users/hapus/<int:id>/', views.hapus_user, name='hapus_user'),
    path('dashboard/users/toggle/<int:id>/', views.toggle_user_aktif, name='toggle_user_aktif'),

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
    path('dashboard/kembali/<int:id>/', views.return_book, name='return_book'),

    # Persetujuan
    path('dashboard/persetujuan/', views.persetujuan_view, name='persetujuan'),
    path('dashboard/persetujuan/<int:id>/<str:action>/', views.persetujuan_action, name='persetujuan_action'),

    # Peminjaman
    path('dashboard/peminjaman-saya/', views.peminjaman_saya_view, name='peminjaman_saya'),
    path('dashboard/riwayat-peminjaman/', views.riwayat_peminjaman_view, name='riwayat_peminjaman'),
]