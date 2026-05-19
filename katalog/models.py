from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta

import os
import uuid
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django.utils.text import slugify


def process_image_to_webp(image_field, base_name=None):
    """Fungsi pembantu untuk crop 4:3, rename sesuai produk, convert WebP, dan limit 100KB"""
    if not image_field:
        return

    img = Image.open(image_field)
    if img.mode != "RGB":
        img = img.convert("RGB")

    # 1. Logika Crop 4:3 (Tetap aman pakai kodemu)
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

    # 2. Kompresi Dinamis (Tetap aman pakai kodemu)
    quality = 85
    output = BytesIO()
    while True:
        output.seek(0)
        output.truncate(0)
        img.save(output, format="WEBP", quality=quality, optimize=True)
        if output.tell() <= 100 * 1024 or quality <= 20:
            break
        quality -= 5

    # 3. Logika Ganti Nama Sesuai Nama Produk
    if base_name:
        # Ubah "Lenovo X250" menjadi "lenovo-x250" agar aman untuk URL web
        clean_name = slugify(base_name)
        
        # Tambahkan string unik pendek di belakangnya (misal: lenovo-x250-a1b2) 
        # Ini trik wajib agar jika user upload gambar dengan nama produk yang sama, filenya tidak saling menimpa
        unique_suffix = uuid.uuid4().hex[:4]
        file_name = f"{clean_name}-{unique_suffix}.webp"
    else:
        # Fallback jika lupa passing nama produk
        file_name = os.path.splitext(image_field.name)[0] + ".webp"

    # Simpan kembali ke fieldnya
    image_field.save(file_name, ContentFile(output.getvalue()), save=False)
    

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=50, blank=True)
    required_spec_keys = models.CharField(
        max_length=500,
        help_text="Pisahkan dengan koma. Contoh: Processor, RAM, SSD",
        blank=True,
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
        ("NEW", "Baru / Brand New"),
        ("A", "Second Grade A"),
        ("AA", "Second Grade AA"),
        ("AA+", "Second Grade AA+"),
        ("AAA+", "Second Grade AAA+"),
    ]

    GARANSI_CHOICES = [
        ("NW", "Tanpa Garansi"),
        ("1", "1 Bulan"),
        ("3", "3 Bulan"),
        ("6", "6 Bulan"),
        ("1YD", "1 Tahun Dist"),
        ("1YR", "1 Tahun Resmi"),
    ]

    sku = models.CharField(max_length=50, unique=True, null=True, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    short_description = models.TextField()
    specifications = models.JSONField(
        default=dict,  # Memberikan {} secara otomatis jika kosong
        blank=True,  # Mengizinkan kosong di Form Django
        null=True,  # Mengizinkan kosong di Database
    )

    price = models.IntegerField(default=0)
    old_price = models.IntegerField(default=0, null=True, blank=True)
    garansi = models.CharField(max_length=20, choices=GARANSI_CHOICES, default="1")
    condition = models.CharField(max_length=5, choices=CONDITION_CHOICES, default="AA+")
    is_sale = models.BooleanField(default=False)
    stock = models.IntegerField(default=1)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # --- PINTASAN GAMBAR UTAMA DARI GALLERY (ANTI CRASH) ---
    @property
    def main_image_url(self):
        """Otomatis mengambil gambar pertama dari multiple images (ProductImage)"""
        first_image = self.images.first() # mengambil data pertama dari related_name='images'
        if first_image and first_image.image:
            return first_image.image.url
        # Fallback kalau admin lupa masukin foto sama sekali
        return "/static/images/no-image.png"

    # --- METHOD & PROPERTY SPESIFIKASI ---
    def get_specs_as_list(self):
        """Mengambil nilai spesifikasi sebagai list untuk badge di card"""
        data = self.specifications
        if isinstance(data, str):
            try:
                valid_json_str = data.replace("'", '"')
                data = json.loads(valid_json_str)
            except:
                return []

        if data and isinstance(data, dict):
            return list(data.values())[:4]
        return []

    @property
    def get_specs_list(self):
        """Mengembalikan data spesifikasi agar aman di-loop di template"""
        if isinstance(self.specifications, dict):
            return self.specifications.items()
        return {}.items()

    # --- PROPERTY HARGA & STATUS BARU ---
    @property
    def price_diff_percent(self):
        if self.old_price and self.old_price != self.price:
            diff = abs(self.price - self.old_price)
            percent = (diff / self.old_price) * 100
            return int(round(percent))
        return 0

    @property
    def is_price_up(self):
        if self.old_price:
            return self.price > self.old_price
        return False

    @property
    def is_new_product(self):
        return self.created_at >= timezone.now() - timedelta(days=7)

    # --- FUNGSI SAVE (SUDAH DISATUKAN, TIDAK DOUBLE LAGI) ---
    def save(self, *args, **kwargs):
        # 1. Otomatisasi Slug
        if not self.slug:
            self.slug = slugify(self.name)
            
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="products/gallery/")

    def save(self, *args, **kwargs):
        if self.image:
            # Sebelum dikonversi, kita cek apakah gambar ini baru di-upload 
            # (agar tidak melakukan ganti nama berulang-ulang saat update teks produk)
            is_new_image = False
            if not self.pk:
                is_new_image = True
            else:
                try:
                    orig = ProductImage.objects.get(pk=self.pk)
                    if orig.image != self.image:
                        is_new_image = True
                except ProductImage.DoesNotExist:
                    is_new_image = True

            # Jika gambarnya baru, eksekusi konversi + rename pakai nama produk induknya
            if is_new_image:
                # Mengirimkan nama produk induk (contoh: self.product.name = "Lenovo X250")
                process_image_to_webp(self.image, base_name=self.product.name)
                
        super().save(*args, **kwargs)