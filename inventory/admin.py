from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction, models
from django.utils import timezone
from .models import Product, Category, Stock, Transaction
from sales.models import Sale, SaleItem
import requests
from bs4 import BeautifulSoup
from decimal import Decimal
from datetime import date

def get_usd_afn_rate():
    """
    دریافت نرخ لحظه‌ای دلار به افغانی از سایت sarafi.af
    بازگشت: (نرخ خرید, نرخ فروش) یا (None, None) در صورت خطا
    """
    try:
        url = "https://sarafi.af/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # جستجوی جدول حاوی USD - US Dollar
        rows = soup.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 4 and 'USD' in cells[0].get_text():
                buy_text = cells[1].get_text().strip()
                sell_text = cells[2].get_text().strip()
                # تبدیل متن به عدد (حذف کاما و فاصله)
                buy = Decimal(buy_text.replace(',', '').replace(' ', ''))
                sell = Decimal(sell_text.replace(',', '').replace(' ', ''))
                return buy, sell
        return None, None
    except Exception as e:
        print(f"خطا در دریافت نرخ ارز: {e}")
        return None, None

@login_required
def dashboard(request):
    # 1. تعداد اجناس (محصولات فعال)
    total_products = Product.objects.filter(is_active=True).count()
    
    # 2. فروشات امروز
    today = timezone.now().date()
    today_sales = Sale.objects.filter(date__date=today)
    total_sales_today = sum(sale.total_amount for sale in today_sales)
    
    # 3. سود امروز (مجموع (قیمت فروش - قیمت خرید) * تعداد برای آیتم‌های فروخته شده امروز)
    profit_today = Decimal('0')
    for sale in today_sales:
        for item in sale.items.all():
            purchase_price = item.product.purchase_price
            profit_today += (item.unit_price - purchase_price) * item.quantity
    
    # 4. نرخ ارز دلار به افغانی (از سایت)
    usd_buy, usd_sell = get_usd_afn_rate()
    if usd_buy is None:
        usd_buy = usd_sell = Decimal('0')
        rate_error = True
    else:
        rate_error = False
    
    context = {
        'total_products': total_products,
        'total_sales_today': total_sales_today,
        'profit_today': profit_today,
        'usd_buy': usd_buy,
        'usd_sell': usd_sell,
        'rate_error': rate_error,
    }
    return render(request, 'inventory/dashboard.html', context)


@login_required
def product_list(request):
    products = Product.objects.filter(is_active=True)
    for p in products:
        p.stock_qty = p.stock.quantity if hasattr(p, 'stock') else 0
    return render(request, 'inventory/product_list.html', {'products': products})

@login_required
def product_create(request):
    if request.method == 'POST':
        category = get_object_or_404(Category, id=request.POST['category'])
        product = Product.objects.create(
            name=request.POST['name'],
            code=request.POST['code'],
            category=category,
            purchase_price=request.POST['purchase_price'],
            selling_price=request.POST['selling_price'],
            description=request.POST.get('description', '')
        )
        Stock.objects.create(product=product, quantity=0)
        messages.success(request, f'محصول {product.name} اضافه شد.')
        return redirect('inventory:product_list')
    categories = Category.objects.all()
    return render(request, 'inventory/product_form.html', {'categories': categories})

@login_required
def stock_in(request):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=request.POST['product'])
        qty = int(request.POST['quantity'])
        price = request.POST['price_at_time']
        with transaction.atomic():
            stock, _ = Stock.objects.get_or_create(product=product)
            stock.quantity += qty
            stock.save()
            Transaction.objects.create(
                product=product, transaction_type='IN', quantity=qty,
                price_at_time=price, description=request.POST.get('description', '')
            )
        messages.success(request, f'{qty} عدد به {product.name} اضافه شد.')
        return redirect('dashboard')
    products = Product.objects.all()
    return render(request, 'inventory/stock_form.html', {'products': products, 'type': 'IN'})

@login_required
def stock_out(request):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=request.POST['product'])
        qty = int(request.POST['quantity'])
        stock = get_object_or_404(Stock, product=product)
        if stock.quantity < qty:
            messages.error(request, 'موجودی کافی نیست.')
            return redirect('inventory:stock_out')
        with transaction.atomic():
            stock.quantity -= qty
            stock.save()
            Transaction.objects.create(
                product=product, transaction_type='OUT', quantity=qty,
                price_at_time=request.POST['price_at_time'],
                description=request.POST.get('description', '')
            )
        messages.success(request, f'{qty} عدد از {product.name} خارج شد.')
        return redirect('dashboard')
    products = Product.objects.all()
    return render(request, 'inventory/stock_form.html', {'products': products, 'type': 'OUT'})