from django.contrib import admin
from django.urls import path, include
from inventory import views as inv_views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', inv_views.dashboard, name='dashboard'),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # مسیر تغییر زبان (اجباری برای کارکرد منوی زبان)
    path('i18n/', include('django.conf.urls.i18n')),
    
    # مسیرهای اپلیکیشن‌ها
    path('products/', include('inventory.urls')),
    path('sales/', include('sales.urls')),
    path('purchases/', include('purchases.urls')),
    path('customers/', include('customers.urls')),
    path('suppliers/', include('suppliers.urls')),
    path('misc-persons/', include('misc_persons.urls')),
    path('transactions/', include('transactions.urls')),
    path('expenses/', include('expenses.urls')),
    path('settings/', include('settings_app.urls')),
]