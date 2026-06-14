from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.sale_list, name='sale_list'),
    path('new/', views.new_sale, name='new_sale'),
    path('<int:pk>/', views.sale_detail, name='sale_detail'),
    path('<int:pk>/edit/', views.sale_edit, name='sale_edit'),
    path('<int:pk>/delete/', views.sale_delete, name='sale_delete'),
]