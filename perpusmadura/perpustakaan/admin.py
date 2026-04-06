from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import CustomUser, Kategori, Buku, Peminjaman

@admin.register(CustomUser)
class CustomUserAdmin(ImportExportModelAdmin):
    list_display = ('username', 'email', 'role', 'is_staff')

@admin.register(Kategori)
class KategoriAdmin(ImportExportModelAdmin):
    list_display = ('id', 'nama')

@admin.register(Buku)
class BukuAdmin(ImportExportModelAdmin):
    list_display = ('judul', 'pengarang', 'stok', 'kategori')

@admin.register(Peminjaman)
class PeminjamanAdmin(ImportExportModelAdmin):
    list_display = ('user', 'buku', 'tanggal_pinjam', 'tanggal_harus_kembali', 'status', 'denda')
