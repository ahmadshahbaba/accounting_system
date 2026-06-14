from django.urls import path
from . import views

app_name = 'misc_persons'

urlpatterns = [
    path('', views.misc_list, name='misc_list'),
    path('add/', views.misc_create, name='misc_create'),
    path('edit/<int:pk>/', views.misc_edit, name='misc_edit'),
    path('delete/<int:pk>/', views.misc_delete, name='misc_delete'),
    path('transactions/<int:pk>/', views.misc_transactions, name='misc_transactions'),
]