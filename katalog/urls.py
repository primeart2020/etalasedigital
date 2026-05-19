from django.urls import path
from . import views

urlpatterns = [
    path('', views.store, name='store'),
    path('add-product/', views.add_product, name='add_product'),
    # Path baru untuk Edit dan Delete (menggunakan ID/Primary Key produk)
    path('product/edit/<int:pk>/', views.edit_product, name='edit_product'),
    path('product/delete/<int:pk>/', views.delete_product, name='delete_product'),
    
    path('product/image/delete/<int:img_id>/', views.delete_product_image, name='delete_product_image'),
    
    
    path('product_list', views.product_list, name='product_list'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    
    path('get-spec-fields/', views.get_spec_fields, name='get_spec_fields'),
]