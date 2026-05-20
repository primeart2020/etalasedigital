from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from .models import Product, Category, ProductImage
from .forms import ProductForm
from django.db.models import Q

from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.db.models import Case, When, Value, IntegerField

from django.shortcuts import render
from django.db.models import Q, Case, When, Value, IntegerField, Count # <-- Pastikan Q di-import
from .models import Product, Category

def store(request):
    # 1. Ambil semua produk yang aktif/tersedia terlebih dahulu
    products = Product.objects.all() # atau .filter(is_active=True) jika ada
    categories = Category.objects.all()

    # 2. TANGKAP INPUT KEYWORD LIVE SEARCH (name="q")
    query = request.GET.get('q', '').strip()
    if query:
        # Mencari berdasarkan nama produk ATAU deskripsi/spesifikasi
        products = products.filter(name__icontains=query)

    # 3. TANGKAP FILTER KATEGORI (Mendukung multi-select dari desktop & mobile)
    category_ids = request.GET.getlist('category')
    if category_ids:
        products = products.filter(category_id__in=category_ids)

    # 4. TANGKAP RENTANG HARGA (Dari modal mobile)
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # 5. PROSES UTAMA: FITUR SORTIR / URUTKAN (name="sort")
    sort_by = request.GET.get('sort', 'latest') # 'latest' jadi default jika kosong
    if sort_by == 'price_low':
        products = products.order_by('price') # Harga terendah ke tertinggi
    elif sort_by == 'price_high':
        products = products.order_by('-price') # Harga tertinggi ke terendah (pake tanda minus)
    else:
        products = products.order_by('-created_at') # 'latest' -> Berdasarkan tanggal input terbaru

    # KUNCI BARU: Jika request datang dari HTMX
    if request.headers.get('HX-Request'):
        context = {
            'products': products,
            'categories': categories, # Kita ikut sertakan categories agar checkbox tahu mana yang aktif
        }
        # Kita arahkan ke file partial khusus HTMX
        return render(request, 'katalog/partials/store_partials.html', context)

    # Jika request biasa (refresh halaman)
    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'katalog/store.html', context)



def product_list(request):
    all_product = Product.objects.filter(is_available=True)
    return render(request, 'katalog/product_list.html', {'products': all_product})


def product_detail(request, slug):
    # Ambil produk berdasarkan slug
    product = get_object_or_404(Product, slug=slug, is_available=True)
    
    # Ambil produk terkait (opsional, dari kategori yang sama)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:20]
    site_url = request.build_absolute_uri('/')[:-1]  # Dapatkan URL dasar situs (tanpa trailing slash)
    
    context = {
        'product': product,
        'related_products': related_products,
        'site_url': site_url
    }
    return render(request, 'katalog/product_detail.html', context)


def get_spec_fields(request):
    category_id = request.GET.get('category')
    if not category_id:
        return HttpResponse('<p class="text-muted small mb-0">Pilih kategori untuk mengisi spesifikasi.</p>')
    
    category = Category.objects.get(id=category_id)
    # Ambil string "Processor, RAM, SSD" dan jadikan list
    if category.required_spec_keys:
        spec_keys = [k.strip() for k in category.required_spec_keys.split(',')]
    else:
        spec_keys = []

    return render(request, 'katalog/partials/spec_inputs.html', {'spec_keys': spec_keys})


def index(request):
    # Ambil semua produk, urutkan berdasarkan yang terbaru dulu
    all_products = list(Product.objects.all().order_by('-created_at'))
    
    # Pisahkan jadi dua list manual
    ready_stock = [p for p in all_products if p.stock > 0]
    sold_out = [p for p in all_products if p.stock <= 0]
    
    # Gabungkan kembali: Ready dulu, baru Sold
    products = ready_stock + sold_out
    
    return render(request, 'index.html', {'products': products})

# ==========================================
# 1. ADD PRODUCT (MODIFIKASI SIKIT UNTUK TEMPLATE DINAMIS)
# ==========================================
@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save() 
            
            # Ambil banyak file dari field extra_images
            files = request.FILES.getlist('extra_images') 
            for f in files:
                ProductImage.objects.create(product=product, image=f)
            
            messages.success(request, 'Produk berhasil disimpan!')
            return redirect('store')
    else:
        form = ProductForm()
    
    # Kirim title agar template fleksibel
    return render(request, 'katalog/add_product.html', {
        'form': form, 
        'title': 'Tambah Produk Baru'
    })

@login_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            
            # Sekarang gambar baru sifatnya MENAMBAHKAN, tidak menghapus paksa semuanya
            files = request.FILES.getlist('extra_images')
            for f in files:
                ProductImage.objects.create(product=product, image=f)
            
            messages.success(request, 'Produk berhasil diperbarui!')
            return redirect('product_detail', slug=product.slug)
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'katalog/add_product.html', {
        'form': form,
        'product': product,
        'title': f'Edit Produk: {product.name}'
    })

@login_required
def delete_product(request, pk):
    # Cari pakai PK
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Produk berhasil dihapus!')
        return redirect('store')
        
    return render(request, 'katalog/confirm_delete.html', {'product': product})


@login_required
def delete_product_image(request, img_id):
    if request.method == 'POST':
        # Cari gambar ekstra berdasarkan ID-nya
        image = get_object_or_404(ProductImage, id=img_id)
        image.delete() # Hapus dari database
        
        # Kembalikan response kosong agar elemen gambar di HTML langsung hilang (fitur HTMX)
        return HttpResponse("") 
    return HttpResponse(status=400)