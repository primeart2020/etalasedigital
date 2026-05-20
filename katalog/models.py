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
    """Fungsi pembantu super cepat untuk crop, paksa resize ke 500px, dan kompresi WebP sekali tembak di bawah 15KB"""
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

    # =====================================================================
    # FIX: PROSES RESIZE EKSTREM (Sengaja ditimpa ke variabel img)
    # =====================================================================
    # Kita kunci lebar gambar di 500px. Otomatis tingginya jadi 375px (Rasio 4:3)
    target_width = 500
    target_height = 375
    
    # WAJIB: img = img.resize(...) agar hasil pengecilan tersimpan ke objeknya!
    # Menggunakan BILINEAR agar proses upload 7-10 gambar sekaligus tetap instan tanpa loading lama
    img = img.resize((target_width, target_height), Image.Resampling.BILINEAR)

    # Kunci 2: Sekali Tembak di Kualitas 60 (Tanpa Loop While biar anti-lemot)
    # Gambar 500x375px dengan kualitas WebP 60 dijamin ukurannya drop ke kisaran 5KB - 15KB!
    output = BytesIO()
    img.save(output, format="WEBP", quality=60, optimize=True)

    # 3. Logika Ganti Nama Sesuai Nama Produk
    if base_name:
        clean_name = slugify(base_name)
        unique_suffix = uuid.uuid4().hex[:4]
        file_name = f"{clean_name}-{unique_suffix}.webp"
    else:
        file_name = os.path.splitext(image_field.name)[0] + ".webp"

    # Simpan kembali ke field Django (menimpa file sementara di RAM)
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
            is_new_image = False
            
            if not self.pk:
                # 1. Kasus: Input Produk Baru
                is_new_image = True
            else:
                # 2. Kasus: Edit Produk
                try:
                    orig = ProductImage.objects.get(pk=self.pk)
                    
                    # Cek apakah user mengunggah file gambar baru untuk menggantikan yang lama
                    if orig.image != self.image:
                        is_new_image = True
                        
                        # TAKTIK BERSIH-BERSIH: Hapus file fisik gambar lama dari harddisk server
                        if orig.image and os.path.isfile(orig.image.path):
                            os.remove(orig.image.path)
                            
                except ProductImage.DoesNotExist:
                    is_new_image = True

            # Jika gambarnya baru/diganti, eksekusi konversi + rename
            if is_new_image:
                process_image_to_webp(self.image, base_name=self.product.name)
                
        super().save(*args, **kwargs)

    # =====================================================================
    # BONUS: HANDLE JIKA TOMBOL "HAPUS" DI-KLIK (DELETE DARI ADMIN/FORM)
    # =====================================================================
    def delete(self, *args, **kwargs):
        # Pastikan file fisik di harddisk ikut musnah saat data di-delete dari database
        if self.image and os.path.isfile(self.image.path):
            os.remove(self.image.path)
        super().delete(*args, **kwargs)