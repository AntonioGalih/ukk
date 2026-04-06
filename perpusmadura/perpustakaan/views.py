from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Buku, CustomUser, Peminjaman, Kategori
from .forms import UserLoginForm, BukuForm, UserForm, UserRegistrationForm
import datetime

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
        # Dashboard Admin
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
        # Dashboard Anggota
        peminjaman = Peminjaman.objects.filter(user=request.user)
        context = {'peminjaman_list': peminjaman}
        return render(request, 'dashboard_anggota.html', context)

@login_required(login_url='login')
def book_manage(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
        
    buku_list = Buku.objects.all()
    form = BukuForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Buku berhasil ditambahkan")
        return redirect('book_manage')
        
    return render(request, 'book_manage.html', {'buku_list': buku_list, 'form': form})

@login_required(login_url='login')
def user_manage(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
        
    users = CustomUser.objects.filter(role='anggota')
    form = UserForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "User berhasil ditambahkan")
        return redirect('user_manage')
        
    return render(request, 'user_manage.html', {'users': users, 'form': form})

@login_required(login_url='login')
def extend_borrowing(request, id):
    peminjaman = get_object_or_404(Peminjaman, id=id)
    # Check if user is the owner
    if peminjaman.user == request.user and peminjaman.status == 'dipinjam' and not peminjaman.diperpanjang:
        today = datetime.date.today()
        # Perpanjang hanya bisa di hari terakhir peminjaman
        if peminjaman.tanggal_harus_kembali == today:
            peminjaman.tanggal_harus_kembali += datetime.timedelta(days=7) # +7 Hari
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