from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Case, When, Value, IntegerField, Count
from .models import Product, Category, ProductImage
from .forms import ProductForm

# ==========================================
# 1. HALAMAN UTAMA / BERANDA (INDEX)
# ==========================================
def index(request):
    # Ambil semua produk, tandai stok 0 atau Null, lalu urutkan: ready dulu baru terbaru
    products = Product.objects.annotate(
        is_sold_out=Case(
            When(Q(stock__lte=0) | Q(stock__isnull=True), then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by('is_sold_out', '-created_at')
    
    return render(request, 'index.html', {'products': products})


# ==========================================
# 2. KATALOG TOKO / STORE (DENGAN LIVE SEARCH & HTMX)
# ==========================================
def store(request):
    # 1. Ambil produk dan Tandai stok 0 ATAU stok yang NULL sebagai Sold Out (Nilai 1)
    products = Product.objects.annotate(
        is_sold_out=Case(
            When(Q(stock__lte=0) | Q(stock__isnull=True), then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    )
    categories = Category.objects.all()

    # 2. TANGKAP INPUT KEYWORD LIVE SEARCH (name="q")
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(name__icontains=query)

    # 3. TANGKAP FILTER KATEGORI (Mendukung multi-select)
    category_ids = request.GET.getlist('category')
    if category_ids:
        products = products.filter(category_id__in=category_ids)

    # 4. TANGKAP RENTANG HARGA
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Reset urutan bawaan model agar tidak bentrok
    products = products.order_by()

    # 5. PROSES UTAMA SORTIR (Wajib menyelipkan 'is_sold_out' di awal parameter)
    sort_by = request.GET.get('sort', 'latest') 
    if sort_by == 'price_low':
        products = products.order_by('is_sold_out', 'price') # Stok ready dulu -> Harga termurah
    elif sort_by == 'price_high':
        products = products.order_by('is_sold_out', '-price') # Stok ready dulu -> Harga termahal
    else:
        products = products.order_by('is_sold_out', '-created_at') # Stok ready dulu -> Produk terbaru

    # KUNCI BARU: Jika request datang dari HTMX
    if request.headers.get('HX-Request'):
        context = {
            'products': products,
            'categories': categories,
        }
        return render(request, 'katalog/partials/store_partials.html', context)

    # Jika request biasa (refresh halaman)
    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'katalog/store.html', context)


# ==========================================
# 3. FUNGSI-FUNGSI PENDUKUNG PRODUK
# ==========================================
def product_list(request):
    all_product = Product.objects.filter(is_available=True)
    return render(request, 'katalog/product_list.html', {'products': all_product})


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_available=True)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:20]
    site_url = request.build_absolute_uri('/')[:-1]
    
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
    if category.required_spec_keys:
        spec_keys = [k.strip() for k in category.required_spec_keys.split(',')]
    else:
        spec_keys = []

    return render(request, 'katalog/partials/spec_inputs.html', {'spec_keys': spec_keys})


# ==========================================
# 4. MANAJEMEN PRODUK (ADD, EDIT, DELETE) - LOGIN REQUIRED
# ==========================================
@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save() 
            files = request.FILES.getlist('extra_images') 
            for f in files:
                ProductImage.objects.create(product=product, image=f)
            
            messages.success(request, 'Produk berhasil disimpan!')
            return redirect('store')
    else:
        form = ProductForm()
    
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
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Produk berhasil dihapus!')
        return redirect('store')
        
    return render(request, 'katalog/confirm_delete.html', {'product': product})


@login_required
def delete_product_image(request, img_id):
    if request.method == 'POST':
        image = get_object_or_404(ProductImage, id=img_id)
        image.delete()
        return HttpResponse("") 
    return HttpResponse(status=400)