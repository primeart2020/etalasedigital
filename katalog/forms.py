from django import forms
from .models import Product # Sesuaikan dengan nama model Anda

from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        # Hapus 'is_new' karena sekarang otomatis (property)
        fields = [
            'category', 'sku', 'name', 'specifications', 'condition', 'price', 'old_price', 
            'short_description', 'image', 'stock', 'is_sale', 'discount_percent'
        ]
        
        # Menggunakan class Bootstrap 5 (form-control & form-select)
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Laptop (Contoh: Thinkpad X1 Carbon)'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SKU (Contoh: 5825)'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Harga Jual Sekarang'}),
            'old_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Harga Sebelum Diskon (Opsional)'}),
            'short_description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Contoh: Laptop slim dan elegan....', 'rows': 3}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_percent': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Persentase %'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tambahkan styling khusus untuk checkbox agar rapi di Bootstrap 5
        self.fields['is_sale'].widget.attrs.update({'class': 'form-check-input'})