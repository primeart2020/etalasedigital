from django import template

register = template.Library()

@register.filter
def replace_dash(value):
    """Mengubah 'laptop-gaming' menjadi 'Laptop Gaming'"""
    return value.replace('-', ' ')

@register.filter
def slice_url(full_path, count):
    """Membangun URL kembali. Contoh: /katalog/produk/ -> /katalog/"""
    segments = [s for s in full_path.split('/') if s]
    return '/' + '/'.join(segments[:count]) + '/'