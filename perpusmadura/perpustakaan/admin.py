from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import CustomUser, Kategori, Buku, Peminjaman, PengaturanSistem

@admin.register(CustomUser)
class CustomUserAdmin(ImportExportModelAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active')
    search_fields = ('username', 'email')

@admin.register(Kategori)
class KategoriAdmin(ImportExportModelAdmin):
    list_display = ('id', 'nama')
    search_fields = ('nama',)

@admin.register(Buku)
class BukuAdmin(ImportExportModelAdmin):
    list_display = ('judul', 'pengarang', 'kategori', 'stok', 'tahun_terbit')
    list_filter = ('kategori',)
    search_fields = ('judul', 'pengarang')

@admin.register(Peminjaman)
class PeminjamanAdmin(ImportExportModelAdmin):
    list_display = ('user', 'buku', 'tanggal_pinjam', 'tanggal_harus_kembali', 'tanggal_kembali', 'status', 'denda', 'diperpanjang')
    list_filter = ('status', 'diperpanjang')
    search_fields = ('user__username', 'buku__judul')
    date_hierarchy = 'tanggal_pinjam'

@admin.register(PengaturanSistem)
class PengaturanSistemAdmin(admin.ModelAdmin):
    list_display = ('denda_per_hari', 'denda_hilang_buku', 'batas_hari_pinjam', 'updated_at')

    def has_add_permission(self, request):
        # Hanya boleh ada 1 record
        return not PengaturanSistem.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
