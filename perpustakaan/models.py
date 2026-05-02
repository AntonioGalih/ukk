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
    cover = models.ImageField(upload_to='covers', blank=True, null=True)
    qr_code = models.ImageField(upload_to='qr_codes', blank=True)

    def __str__(self):
        return self.judul

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)

        if self.qr_code:
            return

        if creating and self.pk is None:
            return

        qrcode_payload = f"/buku/{self.pk}/"
        qrcode_img = qrcode.make(qrcode_payload)
        qrcode_img = qrcode_img.convert('RGB')
        canvas = Image.new('RGB', qrcode_img.size, 'white')
        canvas.paste(qrcode_img, (0, 0))
        fname = f'qr_code-buku-{self.pk}.png'
        buffer = BytesIO()
        canvas.save(buffer, 'PNG')
        buffer.seek(0)
        self.qr_code.save(fname, File(buffer), save=False)
        canvas.close()

        super().save(update_fields=['qr_code'])

class Peminjaman(models.Model):
    STATUS_CHOICES = (
        ('ajuan_pinjam', 'Ajuan Pinjam'),
        ('dipinjam', 'Dipinjam'),
        ('ajuan_kembali', 'Ajuan Kembali'),
        ('kembali', 'Dikembalikan'),
        ('terlambat', 'Terlambat'),
        ('hilang', 'Hilang'),
        ('ditolak_pinjam', 'Ditolak (Pinjam)'),
        ('ditolak_kembali', 'Ditolak (Kembali)'),
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    buku = models.ForeignKey(Buku, on_delete=models.CASCADE)
    tanggal_pinjam = models.DateField(auto_now_add=True)
    tanggal_harus_kembali = models.DateField()
    tanggal_kembali = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ajuan_pinjam')
    denda = models.IntegerField(default=0)
    diperpanjang = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.buku.judul}"