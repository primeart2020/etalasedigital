from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from .models import Product, Category
from .forms import ProductForm
from django.db.models import Count

def store(request):
    # Mengambil semua produk yang tersedia
    all_product = Product.objects.filter(is_available=True).order_by('-created_at')
    
    # Mengambil semua kategori dan menghitung jumlah produk di setiap kategori
    # annotate(total=Count('products')) akan memberikan atribut .total pada tiap objek kategori
    categories = Category.objects.annotate(total=Count('products'))
    
    context = {
        'products': all_product,
        'categories': categories,
    }
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


def store(request):
    products = Product.objects.all()
    
    # Ambil parameter dari request
    category_ids = request.GET.getlist('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort') # Ini yang menyebabkan error

    # --- LOGIKA FILTER ---
    if category_ids:
        products = products.filter(category_id__in=category_ids)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # --- LOGIKA SORTIR (Perbaikan di sini) ---
    if sort_by == 'price_low':
        products = products.order_by('price')  # Field 'price' (kecil ke besar)
    elif sort_by == 'price_high':
        products = products.order_by('-price') # Field '-price' (besar ke kecil)
    elif sort_by == 'latest':
        products = products.order_by('-id')
    else:
        products = products.order_by('-created_at') # Default

    context = {
        'products': products,
        'categories': Category.objects.all(),
    }

    if request.headers.get('HX-Request'):
        return render(request, 'katalog/partials/product_cards.html', context)
    return render(request, 'katalog/store.html', context)



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