from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta

# from djmoney.models.fields import MoneyField


import os
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile



def process_image_to_webp(image_field):
    """Fungsi pembantu untuk crop 4:3, convert WebP, dan limit 100KB"""
    if not image_field:
        return

    img = Image.open(image_field)
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Logika Crop 4:3
    width, height = img.size
    target_ratio = 4 / 3
    current_ratio = width / height

    if current_ratio > target_ratio:
        new_width = int(target_ratio * height)
        offset = (width - new_width) // 2
        img = img.crop((offset, 0, width - offset, height))
    else:
        new_height = int(width / target_ratio)
        offset = (height - new_height) // 2
        img = img.crop((0, offset, width, height - offset))

    # Kompresi Dinamis
    quality = 85
    output = BytesIO()
    while True:
        output.seek(0)
        output.truncate(0)
        img.save(output, format='WEBP', quality=quality, optimize=True)
        if output.tell() <= 100 * 1024 or quality <= 20:
            break
        quality -= 5

    # Ganti nama file jadi .webp
    file_name = os.path.splitext(image_field.name)[0] + ".webp"
    image_field.save(file_name, ContentFile(output.getvalue()), save=False)
    
    
    

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
    def get_specs_as_list(self):
        """Mengambil nilai spesifikasi sebagai list untuk badge di card"""
        data = self.specifications
        
        # Jika ternyata data tersimpan sebagai string (teks), kita ubah ke dict dulu
        if isinstance(data, str):
            try:
                # Membersihkan string jika ada tanda petik satu agar jadi JSON valid
                valid_json_str = data.replace("'", '"')
                data = json.loads(valid_json_str)
            except:
                return []

        if data and isinstance(data, dict):
            # Mengambil 4 nilai pertama dari dictionary
            return list(data.values())[:4]
        return []

    @property
    def get_specs_list(self):
        """Mengembalikan data spesifikasi agar aman di-loop di template"""
        if isinstance(self.specifications, dict):
            return self.specifications.items()
        return {}.items()
    
    price = models.DecimalField(max_digits=12, decimal_places=0) # Pakai 0 decimal_places untuk Rupiah agar bersih
    old_price = models.DecimalField(max_digits=12, decimal_places=0, blank=True, null=True)
    @property
    def price_diff_percent(self):
        if self.old_price and self.old_price != self.price:
            # Hitung selisih absolut agar hasilnya selalu positif
            diff = abs(self.price - self.old_price)
            percent = (diff / self.old_price) * 100
            return int(round(percent))
        return 0

    @property
    def is_price_up(self):
        # Mengecek apakah harga sekarang lebih mahal dari harga lama
        if self.old_price:
            return self.price > self.old_price
        return False
    
        
    garansi = models.CharField(max_length=20, choices=GARANSI_CHOICES, default='1')
    
    # Field baru: Condition
    condition = models.CharField(max_length=5, choices=CONDITION_CHOICES, default='AA+')
    
    is_sale = models.BooleanField(default=False)
    
    image = models.ImageField(upload_to='products/')
    def save(self, *args, **kwargs):
        # Buat slug jika belum ada
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Cek apakah ada gambar baru yang diupload
        # Kita cek ID untuk membedakan upload baru vs update data lain
        if self.image:
            try:
                this = Product.objects.get(id=self.id)
                if this.image != self.image:
                    process_image_to_webp(self.image)
            except Product.DoesNotExist:
                process_image_to_webp(self.image)

        super().save(*args, **kwargs)
        
        
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
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/gallery/')

    def save(self, *args, **kwargs):
        if self.image:
            process_image_to_webp(self.image)
        super().save(*args, **kwargs)