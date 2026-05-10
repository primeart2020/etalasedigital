from django.contrib import admin
from .models import Category, Product, ProductImage

# Register your models here.

admin.site.register(Category)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3 # Menampilkan 3 slot upload kosong secara default

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]
    list_display = ('sku', 'name', 'price', 'garansi', 'is_available')
    # Menambahkan fitur pencarian berdasarkan SKU dan Nama
    search_fields = ('sku', 'name')
    # Menambahkan filter di samping kanan
    list_filter = ('category', 'condition', 'is_available')
    # Membuat SKU bisa diklik untuk edit
    list_display_links = ('sku', 'name')
    
    def get_changeform_initial_data(self, request):
        # Memberikan data awal jika produk baru dibuat melalui link tertentu
        return {'specifications': {}}

    def save_model(self, request, obj, form, change):
        # Jika spek masih kosong, ambil dari required_spec_keys di Kategori
        if not obj.specifications and obj.category.required_spec_keys:
            keys = [k.strip() for k in obj.category.required_spec_keys.split(',')]
            obj.specifications = {k: "" for k in keys}
        super().save_model(request, obj, form, change)