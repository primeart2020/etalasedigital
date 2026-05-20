# pindah_gambar.py
import os
import json
import django

# Inisialisasi Django agar bisa akses database
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings') # Sesuaikan nama setting jika berbeda
django.setup()

from katalog.models import Product, ProductImage

def migrasi_gambar_ke_galeri():
    print("⏳ Memulai proses sinkronisasi gambar lama ke galeri baru...")
    
    # 1. Buka file backup JSON yang berisi catatan nama gambar lama
    if not os.path.exists('backup_katalog_clean.json'):
        print("❌ File backup_katalog_clean.json tidak ditemukan!")
        return
        
    with open('backup_katalog_clean.json', 'r', encoding='utf-8') as f:
        data_json = json.load(f)
        
    jumlah_terpindah = 0
    
    # 2. Cari data produk di dalam JSON
    for item in data_json:
        if item['model'] == 'katalog.product':
            product_id = item['pk']
            fields = item['fields']
            image_path = fields.get('image') # Mengambil nama file gambar lama (ex: 'products/laptop.jpg')
            
            if image_path:
                try:
                    # Ambil produknya dari database berdasarkan ID
                    product = Product.objects.get(id=product_id)
                    
                    # Cek apakah gambar ini sudah terdaftar di ProductImage agar tidak double
                    exists = ProductImage.objects.filter(product=product, image=image_path).exists()
                    
                    if not exists:
                        # Daftarkan gambar lama ke dalam tabel galeri baru
                        ProductImage.objects.create(
                            product=product,
                            image=image_path
                        )
                        jumlah_terpindah += 1
                        print(f"✅ Berhasil mendaftarkan gambar untuk produk: {product.name}")
                except Product.DoesNotExist:
                    print(f"⚠️ Produk ID {product_id} tidak ditemukan di database, dilewati.")
                except Exception as e:
                    print(f"❌ Error pada produk ID {product_id}: {e}")

    print(f"\n🎉 SELESAI! {jumlah_terpindah} gambar lama berhasil dipindahkan ke sistem galeri baru.")

if __name__ == '__main__':
    migrasi_gambar_ke_galeri()