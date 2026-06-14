from django.urls import path
from . import views

app_name = 'suppliers'

urlpatterns = [
    path('', views.supplier_list, name='supplier_list'),
    path('add/', views.supplier_create, name='supplier_create'),
    path('edit/<int:pk>/', views.supplier_edit, name='supplier_edit'),
    path('delete/<int:pk>/', views.supplier_delete, name='supplier_delete'),
    path('transactions/<int:pk>/', views.supplier_transactions, name='supplier_transactions'),
]