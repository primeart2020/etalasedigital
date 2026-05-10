from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=50, blank=True)
    required_spec_keys = models.CharField(
        max_length=500, 
        help_text="Pisahkan dengan koma. Contoh: Processor, RAM, SSD",
        blank=True
    )
    
    # Tambahkan icon jika ingin menampilkan icon kategori di sidebar
    icon = models.CharField(max_length=50, blank=True, help_text="Contoh: fa-laptop")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
            if not self.slug:
                self.slug = slugify(self.name)
            super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(models.Model):
    # Pilihan untuk Condition
    CONDITION_CHOICES = [
        ('NEW', 'Baru / Brand New'),
        ('A', 'Second Grade A'),
        ('AA', 'Second Grade AA'),
        ('AA+', 'Second Grade AA+'),
        ('AAA+', 'Second Grade AAA+'),
    ]
    
    GARANSI_CHOICES = [
        ('NW', 'Tanpa Garansi'),
        ('1', '1 Bulan'),
        ('3', '3 Bulan'),
        ('6', '6 Bulan'),
        ('1YD', '1 Tahun Dist'),
        ('1YR', '1 Tahun Resmi'),
    ]

    sku = models.CharField(max_length=50, unique=True, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    short_description = models.TextField()
    specifications = models.JSONField(
        default=dict,   # Memberikan {} secara otomatis jika kosong
        blank=True,     # Mengizinkan kosong di Form Django
        null=True       # Mengizinkan kosong di Database (Penting!)
    )
    
    price = models.DecimalField(max_digits=12, decimal_places=0) # Pakai 0 decimal_places untuk Rupiah agar bersih
    old_price = models.DecimalField(max_digits=12, decimal_places=0, blank=True, null=True)
        
    garansi = models.CharField(max_length=20, choices=GARANSI_CHOICES, default='1')
    
    # Field baru: Condition
    condition = models.CharField(max_length=5, choices=CONDITION_CHOICES, default='AA+')
    
    is_sale = models.BooleanField(default=False)
    discount_percent = models.IntegerField(default=0, blank=True, null=True)
    
    image = models.ImageField(upload_to='products/')
    stock = models.IntegerField(default=1)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Otomatisasi is_new (True jika produk berumur kurang dari 7 hari)
    @property
    def is_new_product(self):
        return self.created_at >= timezone.now() - timedelta(days=7)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')

    def __str__(self):
        return f"Image for {self.product.name}"