from django.urls import path
from . import views

app_name = 'settings_app'

urlpatterns = [
    path('', views.general_info, name='index'),
    path('general-info/', views.general_info, name='general_info'),
    path('units/', views.units_list, name='units_list'),
    path('units/add/', views.unit_add, name='unit_add'),
    path('units/edit/<int:pk>/', views.unit_edit, name='unit_edit'),
    path('units/delete/<int:pk>/', views.unit_delete, name='unit_delete'),
    path('currencies/add/', views.currency_add, name='currency_add'),
    path('currencies/edit/<int:pk>/', views.currency_edit, name='currency_edit'),
    path('currencies/delete/<int:pk>/', views.currency_delete, name='currency_delete'),
    path('managers/', views.managers_list, name='managers_list'),
    path('managers/add/', views.manager_add, name='manager_add'),
    path('managers/edit/<int:pk>/', views.manager_edit, name='manager_edit'),
    path('managers/delete/<int:pk>/', views.manager_delete, name='manager_delete'),
]