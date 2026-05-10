from django.urls import path
from . import views

urlpatterns = [
    path('', views.store, name='store'),
    path('add-product/', views.add_product, name='add_product'),
    path('product_list', views.product_list, name='product_list'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    
    path('get-spec-fields/', views.get_spec_fields, name='get_spec_fields'),
]