from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.customer_list, name='customer_list'),
    path('add/', views.customer_create, name='customer_create'),
    path('edit/<int:pk>/', views.customer_edit, name='customer_edit'),
    path('delete/<int:pk>/', views.customer_delete, name='customer_delete'),
    path('transactions/<int:pk>/', views.customer_transactions, name='customer_transactions'),  # <-- جدید
]