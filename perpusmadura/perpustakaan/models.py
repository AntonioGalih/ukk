from django.db import models
from django.contrib.auth.models import AbstractUser
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin/Pustakawan'),
        ('anggota', 'Anggota/Mahasiswa'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='anggota')

class Kategori(models.Model):
    nama = models.CharField(max_length=100)

    def __str__(self):
        return self.nama

class Buku(models.Model):
    judul = models.CharField(max_length=200)
    pengarang = models.CharField(max_length=100)
    penerbit = models.CharField(max_length=100, blank=True, null=True)
    tahun_terbit = models.IntegerField(blank=True, null=True)
    kategori = models.ForeignKey(Kategori, on_delete=models.SET_NULL, null=True, blank=True)
    stok = models.IntegerField(default=0)
    qr_code = models.ImageField(upload_to='qr_codes', blank=True)

    def __str__(self):
        return self.judul

    def save(self, *args, **kwargs):
        if not self.qr_code:
            import re
            # Menghindari error illegal character di Windows (seperti ':' atau '?')
            safe_judul = re.sub(r'[^A-Za-z0-9]', '_', self.judul[:15])
            
            qrcode_img = qrcode.make(f"BUKU-{self.judul}-{self.pengarang}")
            fname = f'qr_code-{safe_judul}.png'
            buffer = BytesIO()
            qrcode_img.save(buffer, format='PNG')
            self.qr_code.save(fname, File(buffer), save=False)
        super().save(*args, **kwargs)


class PengaturanSistem(models.Model):
    """Model Singleton untuk pengaturan sistem perpustakaan"""
    denda_per_hari = models.IntegerField(
        default=2000,
        help_text="Nominal denda per hari keterlambatan (Rupiah)"
    )
    denda_hilang_buku = models.IntegerField(
        default=100000,
        help_text="Nominal denda jika buku hilang (Rupiah)"
    )
    batas_hari_pinjam = models.IntegerField(
        default=7,
        help_text="Batas maksimal hari peminjaman buku"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pengaturan Sistem"
        verbose_name_plural = "Pengaturan Sistem"

    def __str__(self):
        return f"Pengaturan Sistem (Denda: Rp {self.denda_per_hari}/hari, Hilang: Rp {self.denda_hilang_buku}, Batas: {self.batas_hari_pinjam} hari)"

    @classmethod
    def get_pengaturan(cls):
        """Selalu kembalikan satu instance pengaturan (singleton pattern)"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1  # Pastikan selalu pk=1 (singleton)
        super().save(*args, **kwargs)


class Peminjaman(models.Model):
    STATUS_CHOICES = (
        ('dipinjam', 'Dipinjam'),
        ('kembali', 'Dikembalikan'),
        ('terlambat', 'Terlambat'),
        ('hilang', 'Hilang'),
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    buku = models.ForeignKey(Buku, on_delete=models.CASCADE)
    tanggal_pinjam = models.DateField(auto_now_add=True)
    tanggal_harus_kembali = models.DateField()
    tanggal_kembali = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='dipinjam')
    denda = models.IntegerField(default=0)
    diperpanjang = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.buku.judul}"

    def hitung_denda(self):
        """Hitung denda keterlambatan berdasarkan PengaturanSistem"""
        import datetime
        pengaturan = PengaturanSistem.get_pengaturan()
        if self.status == 'hilang':
            return pengaturan.denda_hilang_buku
        if self.tanggal_kembali and self.tanggal_harus_kembali:
            terlambat = (self.tanggal_kembali - self.tanggal_harus_kembali).days
        else:
            today = datetime.date.today()
            terlambat = (today - self.tanggal_harus_kembali).days
        if terlambat > 0:
            return terlambat * pengaturan.denda_per_hari
        return 0