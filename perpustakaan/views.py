from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404
from django.conf import settings
from django.http import HttpResponse
from django.db.models import Count, Sum
from django.core.paginator import Paginator
from .models import Buku, CustomUser, Peminjaman, Kategori
from .forms import UserLoginForm, BukuForm, BukuEditForm, UserForm, UserRegistrationForm
from io import BytesIO
from django.core.files import File
import datetime
import csv
import io
import json
import qrcode

def home(request):
    qs = Buku.objects.all().order_by('-id')
    paginator = Paginator(qs, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'home.html', {'buku_list': page_obj, 'page_obj': page_obj})

def tentang_kami_view(request):
    return render(request, 'tentang_kami.html')

def pusat_bantuan_view(request):
    return render(request, 'pusat_bantuan.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = UserLoginForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                if not user.is_active:
                    messages.error(request, "Akun Anda telah dinonaktifkan. Hubungi admin untuk informasi lebih lanjut.")
                else:
                    login(request, user)
                    return redirect('dashboard')
            else:
                messages.error(request, "Username atau Password salah")
    
    return render(request, 'login.html', {'form': form})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = UserRegistrationForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    return render(request, 'register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

def generate_qr(buku):
    qr_data = f"Buku: {buku.judul} | ID: {buku.id}"
    qr = qrcode.make(qr_data)

    buffer = BytesIO()
    qr.save(buffer, format='PNG')

    filename = f"qr_{buku.id}.png"
    buku.qr_code.save(filename, File(buffer), save=False)

@login_required(login_url='login')
def dashboard_view(request):
    # Pastikan user yang sudah login tapi dinonaktifkan langsung dikeluarkan
    if not request.user.is_active:
        logout(request)
        messages.error(request, "Akun Anda telah dinonaktifkan. Hubungi admin untuk informasi lebih lanjut.")
        return redirect('login')

    if request.user.role == 'admin':
        users_count = CustomUser.objects.filter(role='anggota').count()
        buku_count = Buku.objects.count()
        total_stok = Buku.objects.aggregate(total=Sum('stok'))['total'] or 0
        peminjaman_aktif = Peminjaman.objects.filter(status='dipinjam').count()
        peminjaman_terlambat = Peminjaman.objects.filter(status='terlambat').count()
        denda_total = sum([p.denda for p in Peminjaman.objects.all()])
        
        recent_peminjaman = Peminjaman.objects.select_related('user', 'buku').order_by('-tanggal_pinjam')[:10]

        # --- Data Chart: Peminjaman 3 Hari Terakhir ---
        today = datetime.date.today()
        chart_labels = []
        chart_pinjam = []
        chart_kembali = []
        HARI_ID = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
        for i in range(2, -1, -1):
            hari = today - datetime.timedelta(days=i)
            chart_labels.append(HARI_ID[hari.weekday()])
            chart_pinjam.append(
                Peminjaman.objects.filter(tanggal_pinjam=hari).count()
            )
            chart_kembali.append(
                Peminjaman.objects.filter(tanggal_kembali=hari).count()
            )

        # --- Data Chart: Distribusi Kategori Buku ---
        kategori_data = (
            Buku.objects.filter(kategori__isnull=False)
            .values('kategori__nama')
            .annotate(jumlah=Count('id'))
            .order_by('-jumlah')
        )
        buku_tanpa_kategori = Buku.objects.filter(kategori__isnull=True).count()

        kategori_labels = [item['kategori__nama'] for item in kategori_data]
        kategori_values = [item['jumlah'] for item in kategori_data]
        if buku_tanpa_kategori > 0:
            kategori_labels.append('Lainnya')
            kategori_values.append(buku_tanpa_kategori)

        context = {
            'users_count': users_count,
            'buku_count': buku_count,
            'total_stok': total_stok,
            'peminjaman_aktif': peminjaman_aktif,
            'peminjaman_terlambat': peminjaman_terlambat,
            'denda_total': denda_total,
            'recent_peminjaman': recent_peminjaman,
            'chart_labels': chart_labels,
            'chart_pinjam': chart_pinjam,
            'chart_kembali': chart_kembali,
            'kategori_labels': kategori_labels,
            'kategori_values': kategori_values,
        }
        return render(request, 'dashboard_admin.html', context)
    else:
        peminjaman = Peminjaman.objects.filter(user=request.user)
        today = datetime.date.today()
        denda_per_hari = getattr(settings, 'DENDA_TERLAMBAT_PER_HARI', 2000)
        denda_hilang = getattr(settings, 'DENDA_BUKU_HILANG', 50000)
        
        denda_total = 0
        peminjaman_aktif_list = []

        for p in peminjaman:
            if p.status == 'hilang':
                if p.denda != denda_hilang:
                    p.denda = denda_hilang
                    p.save(update_fields=['denda'])
                denda_total += p.denda
                continue

            if p.status in ['dipinjam', 'terlambat', 'ajuan_kembali']:
                peminjaman_aktif_list.append(p)
                if p.tanggal_kembali is None and p.tanggal_harus_kembali and today > p.tanggal_harus_kembali:
                    hari_telat = (today - p.tanggal_harus_kembali).days
                    new_denda = max(0, hari_telat * denda_per_hari)
                    if p.status != 'ajuan_kembali' and (p.status != 'terlambat' or p.denda != new_denda):
                        p.status = 'terlambat'
                        p.denda = new_denda
                        p.save(update_fields=['status', 'denda'])
                    if p.status == 'ajuan_kembali' and p.denda != new_denda:
                        p.denda = new_denda
                        p.save(update_fields=['denda'])
            elif p.status == 'ajuan_pinjam':
                peminjaman_aktif_list.append(p)
            denda_total += p.denda

        # --- Data Chart: Jejak Bacaan (6 Bulan Terakhir) ---
        import calendar

        bacaan_labels = []
        bacaan_values = []
        for i in range(5, -1, -1):
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            # Label = "Bulan" ex: "Jan", "Feb"
            bacaan_labels.append(calendar.month_abbr[m])
            count = peminjaman.filter(
                tanggal_pinjam__year=y,
                tanggal_pinjam__month=m
            ).count()
            bacaan_values.append(count)

        # --- Data Chart: Kategori Favorit ---
        user_kategori_data = (
            peminjaman.filter(buku__kategori__isnull=False)
            .values('buku__kategori__nama')
            .annotate(jumlah=Count('id'))
            .order_by('-jumlah')
        )
        buku_tanpa_kategori = peminjaman.filter(buku__kategori__isnull=True).count()

        user_kategori_labels = [item['buku__kategori__nama'] for item in user_kategori_data]
        user_kategori_values = [item['jumlah'] for item in user_kategori_data]
        if buku_tanpa_kategori > 0:
            user_kategori_labels.append('Lainnya')
            user_kategori_values.append(buku_tanpa_kategori)

        total_stok = Buku.objects.aggregate(total=Sum('stok'))['total'] or 0
        
        context = {
            'peminjaman_list': peminjaman_aktif_list,
            'denda_total': denda_total,
            'bacaan_labels': bacaan_labels,
            'bacaan_values': bacaan_values,
            'user_kategori_labels': user_kategori_labels,
            'user_kategori_values': user_kategori_values,
            'total_stok': total_stok,
        }
        return render(request, 'dashboard_anggota.html', context)

@login_required(login_url='login')
def book_manage(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    query = request.GET.get('q', '')
    kategori_id = request.GET.get('kategori', '')
    tahun_filter = request.GET.get('tahun_terbit', '')
    penerbit_filter = request.GET.get('penerbit', '')
    
    buku_list = Buku.objects.all()
    form = BukuForm(request.POST or None, request.FILES or None)

    if query:
        buku_list = buku_list.filter(judul__icontains=query) | buku_list.filter(pengarang__icontains=query)
    if kategori_id:
        buku_list = buku_list.filter(kategori_id=kategori_id)
    if tahun_filter:
        buku_list = buku_list.filter(tahun_terbit=tahun_filter)
    if penerbit_filter:
        buku_list = buku_list.filter(penerbit=penerbit_filter)

    buku_list = buku_list.order_by('-id')

    paginator = Paginator(buku_list, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    query_params.pop('page', None)
    querystring = query_params.urlencode()
    
    # Ambil list tahun dan penerbit unik untuk dropdown filter
    tahun_list = Buku.objects.exclude(tahun_terbit__isnull=True).values_list('tahun_terbit', flat=True).distinct().order_by('-tahun_terbit')
    penerbit_list = Buku.objects.exclude(penerbit__exact='').exclude(penerbit__isnull=True).values_list('penerbit', flat=True).distinct().order_by('penerbit')
    
    buku_list = buku_list.order_by('judul')
    kategori_list = Kategori.objects.all()

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Buku berhasil ditambahkan dan QR Code telah digenerate!")
        return redirect('book_manage')
        
    return render(request, 'book_manage.html', {
        'buku_list': page_obj,
        'page_obj': page_obj,
        'querystring': querystring,
        'form': form,
        'kategori_list': kategori_list,
        'tahun_list': tahun_list,
        'penerbit_list': penerbit_list,
        'query': query,
        'selected_kategori': kategori_id,
        'selected_tahun': tahun_filter,
        'selected_penerbit': penerbit_filter,
    })

@login_required(login_url='login')
def edit_buku(request, id):
    if request.user.role != 'admin':
        return redirect('dashboard')
    buku = get_object_or_404(Buku, id=id)
    form = BukuEditForm(request.POST or None, request.FILES or None, instance=buku)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f"Buku '{buku.judul}' berhasil diperbarui!")
        return redirect('book_manage')
    return render(request, 'edit_buku.html', {'form': form, 'buku': buku})

@login_required(login_url='login')
def hapus_buku(request, id):
    if request.user.role != 'admin':
        return redirect('dashboard')
    buku = get_object_or_404(Buku, id=id)
    if request.method == 'POST':
        judul = buku.judul
        buku.delete()
        messages.success(request, f"Buku '{judul}' berhasil dihapus!")
    return redirect('book_manage')

@login_required(login_url='login')
def user_manage(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
        
    users = CustomUser.objects.filter(role='anggota').order_by('username')
    form = UserForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "User berhasil ditambahkan")
        return redirect('user_manage')
        
    return render(request, 'user_manage.html', {'users': users, 'form': form})

@login_required(login_url='login')
def hapus_user(request, id):
    if request.user.role != 'admin':
        return redirect('dashboard')
    user = get_object_or_404(CustomUser, id=id)
    if request.method == 'POST':
        nama = user.username
        user.delete()
        messages.success(request, f"User '{nama}' berhasil dihapus!")
    return redirect('user_manage')

@login_required(login_url='login')
def toggle_user_aktif(request, id):
    if request.user.role != 'admin':
        return redirect('dashboard')
    user = get_object_or_404(CustomUser, id=id)
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        status = "diaktifkan" if user.is_active else "dinonaktifkan"
        messages.success(request, f"User '{user.username}' berhasil {status}!")
    return redirect('user_manage')

@login_required(login_url='login')
def katalog_view(request):
    query = request.GET.get('q', '')
    kategori_id = request.GET.get('kategori', '')
    stok_filter = request.GET.get('stok', '')
    tahun_filter = request.GET.get('tahun_terbit', '')
    penerbit_filter = request.GET.get('penerbit', '')

    buku_list = Buku.objects.all()
    if query:
        buku_list = buku_list.filter(judul__icontains=query) | buku_list.filter(pengarang__icontains=query)
    if kategori_id:
        buku_list = buku_list.filter(kategori_id=kategori_id)
    if stok_filter == 'tersedia':
        buku_list = buku_list.filter(stok__gt=0)
    elif stok_filter == 'habis':
        buku_list = buku_list.filter(stok=0)
    if tahun_filter:
        buku_list = buku_list.filter(tahun_terbit=tahun_filter)
    if penerbit_filter:
        buku_list = buku_list.filter(penerbit=penerbit_filter)

    buku_list = buku_list.order_by('-id')

    paginator = Paginator(buku_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    query_params.pop('page', None)
    querystring = query_params.urlencode()

    tahun_list = Buku.objects.exclude(tahun_terbit__isnull=True).values_list('tahun_terbit', flat=True).distinct().order_by('-tahun_terbit')
    penerbit_list = Buku.objects.exclude(penerbit__exact='').exclude(penerbit__isnull=True).values_list('penerbit', flat=True).distinct().order_by('penerbit')

    kategori_list = Kategori.objects.all()
    return render(request, 'katalog_buku.html', {
        'buku_list': page_obj,
        'page_obj': page_obj,
        'querystring': querystring,
        'kategori_list': kategori_list,
        'tahun_list': tahun_list,
        'penerbit_list': penerbit_list,
        'query': query,
        'selected_kategori': kategori_id,
        'stok_filter': stok_filter,
        'selected_tahun': tahun_filter,
        'selected_penerbit': penerbit_filter,
    })

@login_required(login_url='login')
def laporan_view(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    total_buku = Buku.objects.count()
    total_user = CustomUser.objects.filter(role='anggota').count()
    total_peminjaman = Peminjaman.objects.count()
    peminjaman_aktif = Peminjaman.objects.filter(status='dipinjam').count()
    total_denda = sum([p.denda for p in Peminjaman.objects.all()])
    
    context = {
        'total_buku': total_buku,
        'total_user': total_user,
        'total_peminjaman': total_peminjaman,
        'peminjaman_aktif': peminjaman_aktif,
        'total_denda': total_denda,
    }
    return render(request, 'laporan.html', context)

@login_required(login_url='login')
def export_csv(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    tipe = request.GET.get('tipe', 'buku')
    response = HttpResponse(content_type='text/csv')
    
    if tipe == 'buku':
        response['Content-Disposition'] = 'attachment; filename="data_buku.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Judul', 'Pengarang', 'Penerbit', 'Tahun Terbit', 'Kategori', 'Stok'])
        for b in Buku.objects.all():
            writer.writerow([b.id, b.judul, b.pengarang, b.penerbit or '', b.tahun_terbit or '', b.kategori.nama if b.kategori else '', b.stok])
    
    elif tipe == 'peminjaman':
        response['Content-Disposition'] = 'attachment; filename="data_peminjaman.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'User', 'Buku', 'Tgl Pinjam', 'Tgl Harus Kembali', 'Tgl Kembali', 'Status', 'Denda'])
        for p in Peminjaman.objects.all():
            writer.writerow([p.id, p.user.username, p.buku.judul, p.tanggal_pinjam, p.tanggal_harus_kembali, p.tanggal_kembali or '', p.status, p.denda])
    
    elif tipe == 'user':
        response['Content-Disposition'] = 'attachment; filename="data_user.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Username', 'Email', 'Role', 'Status Aktif', 'Tanggal Gabung'])
        for u in CustomUser.objects.filter(role='anggota'):
            writer.writerow([u.id, u.username, u.email, u.role, 'Aktif' if u.is_active else 'Nonaktif', u.date_joined.strftime('%d/%m/%Y')])
    
    return response

@login_required(login_url='login')
def import_csv(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            messages.error(request, "File harus berformat .csv")
            return redirect('laporan')
        
        try:
            decoded = csv_file.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(decoded))
            count = 0
            for row in reader:
                judul = row.get('Judul', '').strip()
                pengarang = row.get('Pengarang', '').strip()
                if judul and pengarang:
                    Buku.objects.create(
                        judul=judul,
                        pengarang=pengarang,
                        penerbit=row.get('Penerbit', '').strip(),
                        tahun_terbit=int(row.get('Tahun Terbit', 0) or 0) or None,
                        stok=int(row.get('Stok', 0) or 0),
                    )
                    count += 1
            messages.success(request, f"Berhasil mengimpor {count} buku!")
        except Exception as e:
            messages.error(request, f"Gagal mengimpor: {str(e)}")
    
    return redirect('laporan')

@login_required(login_url='login')
def extend_borrowing(request, id):
    peminjaman = get_object_or_404(Peminjaman, id=id)
    if peminjaman.user == request.user and peminjaman.status == 'dipinjam' and not peminjaman.diperpanjang:
        today = datetime.date.today()
        if peminjaman.tanggal_harus_kembali == today:
            peminjaman.tanggal_harus_kembali += datetime.timedelta(days=3)
            peminjaman.diperpanjang = True
            peminjaman.save()
            messages.success(request, "Peminjaman berhasil diperpanjang 3 hari.")
        else:
            messages.error(request, "Perpanjangan hanya bisa dilakukan tepat di hari terakhir pengembalian.")
    else:
        messages.error(request, "Tidak dapat memperpanjang buku ini.")
        
    return redirect('dashboard')

@login_required(login_url='login')
def settings_view(request):
    return render(request, 'settings.html')

def scan_qr_view(request):
    return render(request, 'scan_qr.html')

def book_detail(request, id):
    buku = get_object_or_404(Buku, id=id)
    peminjaman_list = []
    if request.user.is_authenticated and request.user.role == 'admin':
        peminjaman_list = Peminjaman.objects.filter(buku=buku).select_related('user').order_by('-tanggal_pinjam')
        today = datetime.date.today()
        denda_per_hari = getattr(settings, 'DENDA_TERLAMBAT_PER_HARI', 2000)
        denda_hilang = getattr(settings, 'DENDA_BUKU_HILANG', 50000)
        for p in peminjaman_list:
            if p.status == 'hilang':
                if p.denda != denda_hilang:
                    p.denda = denda_hilang
                    p.save(update_fields=['denda'])
                continue
            if p.status in ['dipinjam', 'terlambat'] and p.tanggal_kembali is None and p.tanggal_harus_kembali and today > p.tanggal_harus_kembali:
                hari_telat = (today - p.tanggal_harus_kembali).days
                new_denda = max(0, hari_telat * denda_per_hari)
                if p.status != 'terlambat' or p.denda != new_denda:
                    p.status = 'terlambat'
                    p.denda = new_denda
                    p.save(update_fields=['status', 'denda'])
    return render(request, 'book_detail.html', {'buku': buku, 'peminjaman_list': peminjaman_list})

@login_required(login_url='login')
def borrow_book(request, id):
    if request.method != 'POST':
        return redirect('book_detail', id=id)

    if request.user.role != 'anggota':
        return redirect('book_detail', id=id)

    buku = get_object_or_404(Buku, id=id)
    if buku.stok <= 0:
        messages.error(request, 'Stok buku sedang habis.')
        return redirect('book_detail', id=id)

    today = datetime.date.today()
    tenggat = today + datetime.timedelta(days=3)
    Peminjaman.objects.create(
        user=request.user,
        buku=buku,
        tanggal_harus_kembali=tenggat,
        status='ajuan_pinjam',
        denda=0,
        diperpanjang=False,
    )
    messages.success(request, 'Pengajuan peminjaman berhasil dibuat. Tunggu persetujuan admin.')
    return redirect('katalog')

@login_required(login_url='login')
def request_return(request, id):
    if request.method != 'POST':
        return redirect('dashboard')

    if request.user.role != 'anggota':
        return redirect('dashboard')

    peminjaman = get_object_or_404(Peminjaman, id=id, user=request.user)
    if peminjaman.status not in ['dipinjam', 'terlambat']:
        messages.error(request, 'Pengembalian tidak dapat diajukan untuk status ini.')
        return redirect('dashboard')

    peminjaman.status = 'ajuan_kembali'
    peminjaman.save(update_fields=['status'])
    messages.success(request, 'Pengajuan pengembalian dikirim. Tunggu persetujuan admin.')
    return redirect('dashboard')

@login_required(login_url='login')
def persetujuan_view(request):
    if request.user.role != 'admin':
        return redirect('dashboard')

    qs = Peminjaman.objects.select_related('user', 'buku').filter(status__in=['ajuan_pinjam', 'ajuan_kembali']).order_by('-tanggal_pinjam')
    paginator = Paginator(qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    query_params.pop('page', None)
    querystring = query_params.urlencode()

    return render(request, 'persetujuan.html', {'page_obj': page_obj, 'peminjaman_list': page_obj, 'querystring': querystring})

@login_required(login_url='login')
def persetujuan_action(request, id, action):
    if request.user.role != 'admin':
        return redirect('dashboard')

    if request.method != 'POST':
        return redirect('persetujuan')

    peminjaman = get_object_or_404(Peminjaman, id=id)
    today = datetime.date.today()

    if peminjaman.status == 'ajuan_pinjam':
        if action == 'approve':
            buku = peminjaman.buku
            if buku.stok <= 0:
                messages.error(request, 'Stok buku habis. Tidak dapat menyetujui peminjaman.')
                return redirect('persetujuan')
            peminjaman.status = 'dipinjam'
            peminjaman.tanggal_harus_kembali = today + datetime.timedelta(days=3)
            peminjaman.diperpanjang = False
            peminjaman.save(update_fields=['status', 'tanggal_harus_kembali', 'diperpanjang'])
            buku.stok = max(0, buku.stok - 1)
            buku.save(update_fields=['stok'])
            messages.success(request, f"Peminjaman '{buku.judul}' disetujui untuk {peminjaman.user.username}.")
        elif action == 'reject':
            peminjaman.status = 'ditolak_pinjam'
            peminjaman.save(update_fields=['status'])
            messages.success(request, 'Pengajuan peminjaman ditolak.')
        else:
            messages.error(request, 'Aksi tidak dikenal.')
        return redirect('persetujuan')

    if peminjaman.status == 'ajuan_kembali':
        if action == 'approve':
            peminjaman.status = 'kembali'
            peminjaman.tanggal_kembali = today
            peminjaman.save(update_fields=['status', 'tanggal_kembali'])
            buku = peminjaman.buku
            buku.stok += 1
            buku.save(update_fields=['stok'])
            messages.success(request, f"Pengembalian '{buku.judul}' disetujui untuk {peminjaman.user.username}.")
        elif action == 'reject':
            peminjaman.status = 'ditolak_kembali'
            peminjaman.save(update_fields=['status'])
            messages.success(request, 'Pengajuan pengembalian ditolak.')
        else:
            messages.error(request, 'Aksi tidak dikenal.')
        return redirect('persetujuan')

    messages.error(request, 'Data tidak dalam status menunggu persetujuan.')
    return redirect('persetujuan')

@login_required(login_url='login')
def peminjaman_saya_view(request):
    if request.user.role != 'anggota':
        return redirect('dashboard')

    qs = Peminjaman.objects.select_related('buku').filter(user=request.user).filter(status__in=['ajuan_pinjam', 'dipinjam', 'terlambat', 'ajuan_kembali']).order_by('-tanggal_pinjam')
    paginator = Paginator(qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    query_params.pop('page', None)
    querystring = query_params.urlencode()

    return render(request, 'peminjaman_saya.html', {'page_obj': page_obj, 'peminjaman_list': page_obj, 'querystring': querystring})

@login_required(login_url='login')
def riwayat_peminjaman_view(request):
    if request.user.role == 'admin':
        qs = Peminjaman.objects.select_related('user', 'buku').order_by('-tanggal_pinjam')
    else:
        qs = Peminjaman.objects.select_related('buku').filter(user=request.user).order_by('-tanggal_pinjam')

    paginator = Paginator(qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    query_params.pop('page', None)
    querystring = query_params.urlencode()

    return render(request, 'riwayat_peminjaman.html', {'page_obj': page_obj, 'peminjaman_list': page_obj, 'querystring': querystring})

@login_required(login_url='login')
def download_book_qr(request, id):
    if request.user.role != 'admin':
        raise Http404()

    buku = get_object_or_404(Buku, id=id)

    if not buku.qr_code or not buku.qr_code.name:
        raise Http404("QR belum tersedia")

    try:
        f = buku.qr_code.open('rb')
    except FileNotFoundError:
        raise Http404("File QR tidak ditemukan")

    filename = f"qr-buku-{buku.id}.png"
    return FileResponse(f, as_attachment=True, filename=filename)

@login_required(login_url='login')
def return_book(request, id):
    if request.user.role != 'admin':
        return redirect('dashboard')
        
    peminjaman = get_object_or_404(Peminjaman, id=id)
    if peminjaman.status == 'ajuan_kembali':
        peminjaman.status = 'kembali'
        peminjaman.tanggal_kembali = datetime.date.today()
        peminjaman.save(update_fields=['status', 'tanggal_kembali'])

        buku = peminjaman.buku
        buku.stok += 1
        buku.save(update_fields=['stok'])

        messages.success(request, f"Pengembalian '{buku.judul}' disetujui untuk {peminjaman.user.username}.")
    else:
        messages.error(request, "Pengembalian hanya bisa diproses setelah anggota mengajukan pengembalian.")
        
    return redirect('dashboard')