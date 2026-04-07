from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import Buku, CustomUser, Peminjaman, Kategori
from .forms import UserLoginForm, BukuForm, BukuEditForm, UserForm, UserRegistrationForm
import datetime
import csv
import io

def home(request):
    buku_list = Buku.objects.all()[:8]
    return render(request, 'home.html', {'buku_list': buku_list})

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

@login_required(login_url='login')
def dashboard_view(request):
    if request.user.role == 'admin':
        users_count = CustomUser.objects.filter(role='anggota').count()
        buku_count = Buku.objects.count()
        peminjaman_aktif = Peminjaman.objects.filter(status='dipinjam').count()
        denda_total = sum([p.denda for p in Peminjaman.objects.all()])
        
        recent_peminjaman = Peminjaman.objects.all().order_by('-tanggal_pinjam')[:5]
        context = {
            'users_count': users_count,
            'buku_count': buku_count,
            'peminjaman_aktif': peminjaman_aktif,
            'denda_total': denda_total,
            'recent_peminjaman': recent_peminjaman
        }
        return render(request, 'dashboard_admin.html', context)
    else:
        peminjaman = Peminjaman.objects.filter(user=request.user)
        context = {'peminjaman_list': peminjaman}
        return render(request, 'dashboard_anggota.html', context)

@login_required(login_url='login')
def book_manage(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    query = request.GET.get('q', '')
    kategori_id = request.GET.get('kategori', '')
    
    buku_list = Buku.objects.all()
    if query:
        buku_list = buku_list.filter(judul__icontains=query) | buku_list.filter(pengarang__icontains=query)
    if kategori_id:
        buku_list = buku_list.filter(kategori_id=kategori_id)
    
    buku_list = buku_list.order_by('judul')
    kategori_list = Kategori.objects.all()
    
    form = BukuForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Buku berhasil ditambahkan dan QR Code telah digenerate!")
        return redirect('book_manage')
        
    return render(request, 'book_manage.html', {
        'buku_list': buku_list,
        'form': form,
        'kategori_list': kategori_list,
        'query': query,
        'selected_kategori': kategori_id,
    })

@login_required(login_url='login')
def edit_buku(request, id):
    if request.user.role != 'admin':
        return redirect('dashboard')
    buku = get_object_or_404(Buku, id=id)
    form = BukuEditForm(request.POST or None, instance=buku)
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
    tahun = request.GET.get('tahun', '')

    buku_list = Buku.objects.all()
    if query:
        buku_list = buku_list.filter(judul__icontains=query) | buku_list.filter(pengarang__icontains=query)
    if kategori_id:
        buku_list = buku_list.filter(kategori_id=kategori_id)
    if stok_filter == 'tersedia':
        buku_list = buku_list.filter(stok__gt=0)
    elif stok_filter == 'habis':
        buku_list = buku_list.filter(stok=0)
    if tahun:
        buku_list = buku_list.filter(tahun_terbit=tahun)

    kategori_list = Kategori.objects.all()
    return render(request, 'katalog_buku.html', {
        'buku_list': buku_list,
        'kategori_list': kategori_list,
        'query': query,
        'selected_kategori': kategori_id,
        'stok_filter': stok_filter,
        'tahun': tahun,
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
            peminjaman.tanggal_harus_kembali += datetime.timedelta(days=7)
            peminjaman.diperpanjang = True
            peminjaman.save()
            messages.success(request, "Peminjaman berhasil diperpanjang 7 hari.")
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