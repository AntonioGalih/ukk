from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perpustakaan', '0002_buku_cover_alter_peminjaman_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='peminjaman',
            name='status',
            field=models.CharField(choices=[('ajuan_pinjam', 'Ajuan Pinjam'), ('dipinjam', 'Dipinjam'), ('ajuan_kembali', 'Ajuan Kembali'), ('kembali', 'Dikembalikan'), ('terlambat', 'Terlambat'), ('hilang', 'Hilang'), ('ditolak_pinjam', 'Ditolak (Pinjam)'), ('ditolak_kembali', 'Ditolak (Kembali)')], default='ajuan_pinjam', max_length=20),
        ),
    ]
