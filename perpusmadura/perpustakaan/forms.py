from django import forms
from django.contrib.auth import authenticate
from .models import Buku, Kategori, CustomUser, Peminjaman

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-primary',
        'placeholder': 'Buat Password Rahasia'
    }))
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-primary',
        'placeholder': 'Masukkan Username'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-primary',
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
        'class': 'w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all',
        'placeholder': 'Masukkan Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all',
        'placeholder': 'Masukkan Password'
    }))

class BukuForm(forms.ModelForm):
    class Meta:
        model = Buku
        fields = ['judul', 'pengarang', 'penerbit', 'tahun_terbit', 'kategori', 'stok']
        widgets = {
            'judul': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2 mt-1'}),
            'pengarang': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2 mt-1'}),
            'penerbit': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2 mt-1'}),
            'tahun_terbit': forms.NumberInput(attrs={'class': 'w-full border rounded-lg p-2 mt-1'}),
            'kategori': forms.Select(attrs={'class': 'w-full border rounded-lg p-2 mt-1'}),
            'stok': forms.NumberInput(attrs={'class': 'w-full border rounded-lg p-2 mt-1'}),
        }

class BukuEditForm(forms.ModelForm):
    class Meta:
        model = Buku
        fields = ['judul', 'pengarang', 'penerbit', 'tahun_terbit', 'kategori', 'stok']
        widgets = {
            'judul': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2 mt-1'}),
            'pengarang': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2 mt-1'}),
            'penerbit': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2 mt-1'}),
            'tahun_terbit': forms.NumberInput(attrs={'class': 'w-full border rounded-lg p-2 mt-1'}),
            'kategori': forms.Select(attrs={'class': 'w-full border rounded-lg p-2 mt-1'}),
            'stok': forms.NumberInput(attrs={'class': 'w-full border rounded-lg p-2 mt-1'}),
        }

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'w-full border rounded-lg p-2 mt-1'}))
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2 mt-1'}),
            'email': forms.EmailInput(attrs={'class': 'w-full border rounded-lg p-2 mt-1'}),
            'role': forms.Select(attrs={'class': 'w-full border rounded-lg p-2 mt-1'}),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
