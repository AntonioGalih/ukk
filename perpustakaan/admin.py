from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from django.conf import settings
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

    @admin.action(description='Tandai sebagai hilang (set denda)')
    def mark_as_lost(self, request, queryset):
        denda_hilang = getattr(settings, 'DENDA_BUKU_HILANG', 50000)
        queryset.update(status='hilang', denda=denda_hilang)

    actions = ['mark_as_lost']
