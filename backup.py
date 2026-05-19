# backup.py
import os
import json
import django
from django.core.serializers import serialize

# SEKARANG SUDAH DIARAHKAN KE FOLDER 'core'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings') 
django.setup()

from katalog.models import Product, Category
from django.db import connection

# backup.py (Bagian fungsi jalankan_proses saja yang diganti)

def jalankan_proses():
    print("1. Memulai proses backup data...")
    try:
        data_product = serialize('json', Product.objects.all())
        data_category = serialize('json', Category.objects.all())
        all_data = json.loads(data_product) + json.loads(data_category)

        with open('backup_katalog_clean.json', 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        print("✅ BACKUP SUKSES! File 'backup_katalog_clean.json' berhasil dibuat.")
        
        print("2. Menghapus tabel lama yang bermasalah di database...")
        with connection.cursor() as cursor:
            # 1. Matikan proteksi foreign key sementara
            cursor.execute("PRAGMA foreign_keys = OFF;")
            
            # 2. Hapus tabel produk yang bermasalah
            cursor.execute("DROP TABLE IF EXISTS katalog_product;")
            
            # 3. Hidupkan kembali proteksinya
            cursor.execute("PRAGMA foreign_keys = ON;")
            
        print("✅ TABEL LAMA BERHASIL DIHAPUS DENGAN FORCE!")
        
    except Exception as e:
        print(f"❌ Terjadi kesalahan: {e}")

if __name__ == '__main__':
    jalankan_proses()