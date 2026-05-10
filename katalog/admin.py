from django.contrib import admin
from django.utils.formats import number_format # Perlu import ini
from .models import Category, Product, ProductImage

# Register your models here.
admin.site.register(Category)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3

class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]
    
    # Menampilkan format ribuan di form detail
    readonly_fields = ['formatted_price_detail']
    
    list_display = ('sku', 'name', 'stock', 'old_price', 'price', 'garansi', 'is_available')
    
    # price harus dihapus dari sini agar formatted_price bisa muncul
    list_editable = ['stock', 'old_price', 'price', 'garansi'] 
    
    search_fields = ('sku', 'name')
    list_filter = ('category', 'condition', 'is_available')
    list_display_links = ('sku', 'name')
    list_per_page = 20

    # Tampilan di Halaman Detail (Read Only)
    def formatted_price_detail(self, obj):
        return f"Rp {number_format(obj.price, decimal_pos=0, use_l10n=True)}"
    
    formatted_price_detail.short_description = 'Price (Formatted)'

    def get_changeform_initial_data(self, request):
        return {'specifications': {}}

# Gunakan cara ini agar lebih bersih
admin.site.register(Product, ProductAdmin)
