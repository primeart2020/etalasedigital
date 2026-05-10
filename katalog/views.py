from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from .models import Product, Category
from .forms import ProductForm
from django.db.models import Count

from django.db.models import Case, When, Value, IntegerField

def store(request):
    # 1. Ambil semua produk (jangan pakai .all() dulu, biarkan QuerySet)
    products = Product.objects.filter(is_available=True)
    
    # 2. Ambil parameter dari request
    category_ids = request.GET.getlist('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort')

    # --- LOGIKA FILTER ---
    if category_ids:
        products = products.filter(category_id__in=category_ids)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # --- LOGIKA SORTIR & PENGURUTAN STOK ---
    # Kita tambahkan anotasi is_out_of_stock untuk menandai stock 0
    products = products.annotate(
        is_out_of_stock=Case(
            When(stock__lte=0, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    )

    # Urutan Utama: Selalu 'is_out_of_stock' (stok ada dulu baru sold out)
    # Urutan Kedua: Berdasarkan input user atau default
    if sort_by == 'price_low':
        products = products.order_by('is_out_of_stock', 'price')
    elif sort_by == 'price_high':
        products = products.order_by('is_out_of_stock', '-price')
    elif sort_by == 'latest':
        products = products.order_by('is_out_of_stock', '-id')
    else:
        products = products.order_by('is_out_of_stock', '-created_at')

    context = {
        'products': products,
        'categories': Category.objects.annotate(total=Count('products')),
    }

    if request.headers.get('HX-Request'):
        return render(request, 'katalog/partials/product_cards.html', context)
    return render(request, 'katalog/store.html', context)

def product_list(request):
    all_product = Product.objects.filter(is_available=True)
    return render(request, 'katalog/product_list.html', {'products': all_product})

def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produk berhasil ditambahkan!')
            return redirect('store')
    else:
        form = ProductForm()
    
    return render(request, 'katalog/add_product.html', {'form': form})

def product_detail(request, slug):
    # Ambil produk berdasarkan slug
    product = get_object_or_404(Product, slug=slug, is_available=True)
    
    # Ambil produk terkait (opsional, dari kategori yang sama)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products
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

def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save() # Simpan produk dulu
            
            # Ambil banyak file
            files = request.FILES.getlist('extra_images') 
            from .models import ProductImage
            for f in files:
                ProductImage.objects.create(product=product, image=f)
            
            messages.success(request, 'Produk berhasil disimpan!')
            return redirect('store')
    else:
        form = ProductForm()
    return render(request, 'katalog/add_product.html', {'form': form})