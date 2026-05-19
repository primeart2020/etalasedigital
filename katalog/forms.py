from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    # 1. Definisikan field POLOS tanpa atribut tambahan di widget
    extra_images = forms.ImageField(
        required=False,
        label="Upload Gambar Galeri (Bisa banyak sekaligus)",
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Product
        fields = [
            'category', 'sku', 'name', 'specifications', 'condition', 'price', 'old_price', 
            'short_description', 'stock', 'garansi', 'is_sale',
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Laptop...'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'old_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'short_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'garansi': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 2. SUNTIK atribut lewat dictionary attrs secara langsung
        # Kita gunakan cara ini agar tidak memicu validasi internal Django
        self.fields['extra_images'].widget.attrs['multiple'] = True
        self.fields['extra_images'].widget.attrs['accept'] = 'image/*'
        
        # Styling checkbox agar rapi di Bootstrap 5
        if 'is_sale' in self.fields:
            self.fields['is_sale'].widget.attrs.update({'class': 'form-check-input'})