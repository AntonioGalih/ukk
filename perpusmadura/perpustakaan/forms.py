from django import forms
from django.contrib.auth import authenticate
from .models import Buku, Kategori, CustomUser, Peminjaman, PengaturanSistem

CSS_INPUT = 'w-full px-3 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent text-gray-800 bg-white transition'
CSS_SELECT = 'w-full px-3 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent text-gray-800 bg-white transition cursor-pointer'

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': CSS_INPUT,
        'placeholder': 'Buat Password Rahasia'
    }))
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': CSS_INPUT,
        'placeholder': 'Masukkan Username'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': CSS_INPUT,
        'placeholder': 'email@anda.com'
    }))

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = 'anggota'
        if commit:
            user.save()
        return user

class UserLoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': CSS_INPUT,
        'placeholder': 'Masukkan Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': CSS_INPUT,
        'placeholder': 'Masukkan Password'
    }))

class BukuForm(forms.ModelForm):
    class Meta:
        model = Buku
        fields = ['judul', 'pengarang', 'penerbit', 'tahun_terbit', 'kategori', 'stok']
        widgets = {
            'judul': forms.TextInput(attrs={'class': CSS_INPUT, 'placeholder': 'Judul buku...'}),
            'pengarang': forms.TextInput(attrs={'class': CSS_INPUT, 'placeholder': 'Nama pengarang...'}),
            'penerbit': forms.TextInput(attrs={'class': CSS_INPUT, 'placeholder': 'Nama penerbit...'}),
            'tahun_terbit': forms.NumberInput(attrs={'class': CSS_INPUT, 'placeholder': '2024'}),
            'kategori': forms.Select(attrs={'class': CSS_SELECT}),
            'stok': forms.NumberInput(attrs={'class': CSS_INPUT, 'placeholder': '0', 'min': '0'}),
        }
        labels = {
            'judul': 'Judul Buku',
            'pengarang': 'Pengarang',
            'penerbit': 'Penerbit',
            'tahun_terbit': 'Tahun Terbit',
            'kategori': 'Kategori',
            'stok': 'Jumlah Stok',
        }

class BukuEditForm(forms.ModelForm):
    class Meta:
        model = Buku
        fields = ['judul', 'pengarang', 'penerbit', 'tahun_terbit', 'kategori', 'stok']
        widgets = {
            'judul': forms.TextInput(attrs={'class': CSS_INPUT}),
            'pengarang': forms.TextInput(attrs={'class': CSS_INPUT}),
            'penerbit': forms.TextInput(attrs={'class': CSS_INPUT}),
            'tahun_terbit': forms.NumberInput(attrs={'class': CSS_INPUT}),
            'kategori': forms.Select(attrs={'class': CSS_SELECT}),
            'stok': forms.NumberInput(attrs={'class': CSS_INPUT, 'min': '0'}),
        }
        labels = {
            'judul': 'Judul Buku',
            'pengarang': 'Pengarang',
            'penerbit': 'Penerbit',
            'tahun_terbit': 'Tahun Terbit',
            'kategori': 'Kategori',
            'stok': 'Jumlah Stok',
        }

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': CSS_INPUT, 'placeholder': '••••••••'}))
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': CSS_INPUT, 'placeholder': 'Username unik'}),
            'email': forms.EmailInput(attrs={'class': CSS_INPUT, 'placeholder': 'email@contoh.com'}),
            'role': forms.Select(attrs={'class': CSS_SELECT}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class PeminjamanAdminForm(forms.ModelForm):
    """Form untuk admin menambah peminjaman baru"""
    class Meta:
        model = Peminjaman
        fields = ['user', 'buku', 'tanggal_harus_kembali']
        widgets = {
            'user': forms.Select(attrs={'class': CSS_SELECT}),
            'buku': forms.Select(attrs={'class': CSS_SELECT}),
            'tanggal_harus_kembali': forms.DateInput(attrs={'class': CSS_INPUT, 'type': 'date'}),
        }
        labels = {
            'user': 'Anggota',
            'buku': 'Buku',
            'tanggal_harus_kembali': 'Tanggal Harus Kembali',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hanya tampilkan anggota (bukan admin) dan buku yang stoknya > 0
        self.fields['user'].queryset = CustomUser.objects.filter(role='anggota', is_active=True)
        self.fields['buku'].queryset = Buku.objects.filter(stok__gt=0)

class PengaturanForm(forms.ModelForm):
    """Form untuk mengatur denda dan batas pinjam"""
    class Meta:
        model = PengaturanSistem
        fields = ['denda_per_hari', 'denda_hilang_buku', 'batas_hari_pinjam']
        widgets = {
            'denda_per_hari': forms.NumberInput(attrs={
                'class': CSS_INPUT,
                'placeholder': '2000',
                'min': '0',
                'step': '500',
            }),
            'denda_hilang_buku': forms.NumberInput(attrs={
                'class': CSS_INPUT,
                'placeholder': '100000',
                'min': '0',
                'step': '1000',
            }),
            'batas_hari_pinjam': forms.NumberInput(attrs={
                'class': CSS_INPUT,
                'placeholder': '7',
                'min': '1',
                'max': '60',
            }),
        }
        labels = {
            'denda_per_hari': 'Denda Per Hari (Rp)',
            'denda_hilang_buku': 'Denda Buku Hilang (Rp)',
            'batas_hari_pinjam': 'Batas Hari Peminjaman',
        }
        help_texts = {
            'denda_per_hari': 'Nominal denda rupiah per hari keterlambatan.',
            'denda_hilang_buku': 'Nominal denda jika anggota menghilangkan buku.',
            'batas_hari_pinjam': 'Jumlah hari maksimal peminjaman sebelum dianggap terlambat.',
        }

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': CSS_INPUT, 'placeholder': 'Username..'}),
            'email': forms.EmailInput(attrs={'class': CSS_INPUT, 'placeholder': 'Email baru..'}),
        }
        labels = {
            'username': 'Username Baru',
            'email': 'Alamat Email',
        }
