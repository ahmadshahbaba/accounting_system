from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction, models
from django.utils import timezone
from django.http import JsonResponse
from decimal import Decimal
import requests
from bs4 import BeautifulSoup
import jdatetime
from django.db.models import Sum, F

from .models import Product, Category, Stock, Transaction
from sales.models import Sale, SaleItem
from purchases.models import PurchaseItem
from settings_app.models import UnitOfMeasure, Currency

# ==================== نرخ ارز (با fallback) ====================
def get_usd_afn_rate():
    try:
        url = "https://sarafi.af/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return Decimal('64.35'), Decimal('64.40')
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 4 and 'USD' in cells[0].get_text():
                buy_text = cells[1].get_text().strip()
                sell_text = cells[2].get_text().strip()
                buy = Decimal(buy_text.replace(',', '').replace(' ', ''))
                sell = Decimal(sell_text.replace(',', '').replace(' ', ''))
                return buy, sell
        return Decimal('64.35'), Decimal('64.40')
    except:
        return Decimal('64.35'), Decimal('64.40')

def get_exchange_rate_api(request):
    buy, sell = get_usd_afn_rate()
    return JsonResponse({'buy': float(buy), 'sell': float(sell), 'updated_at': timezone.now().isoformat()})

# ==================== داشبورد ====================
@login_required
def dashboard(request):
    total_products = Product.objects.filter(is_active=True).count()
    low_stocks = Stock.objects.filter(quantity__lte=F('minimum_threshold')).count()
    total_categories = Category.objects.count()
    total_inventory_value = sum((s.product.purchase_price * s.quantity) for s in Stock.objects.all())
    usd_buy, usd_sell = get_usd_afn_rate()
    today = timezone.now().date()
    today_sales = Sale.objects.filter(transaction_date=today)
    total_sales_today = sum(sale.total_amount for sale in today_sales)
    profit_today = Decimal('0')
    for sale in today_sales:
        for item in sale.items.all():
            purchase_price = item.product.purchase_price
            profit_today += (item.unit_price - purchase_price) * item.quantity
    now_jalali = jdatetime.date.today()
    current_jyear = now_jalali.year
    persian_months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
                      'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
    monthly_sales = []
    for month in range(1, 13):
        start_jalali = jdatetime.date(current_jyear, month, 1)
        if month == 12:
            end_jalali = jdatetime.date(current_jyear+1, 1, 1) - jdatetime.timedelta(days=1)
        else:
            end_jalali = jdatetime.date(current_jyear, month+1, 1) - jdatetime.timedelta(days=1)
        start_greg = start_jalali.togregorian()
        end_greg = end_jalali.togregorian()
        total = Sale.objects.filter(transaction_date__gte=start_greg, transaction_date__lte=end_greg).aggregate(total=Sum('total_amount'))['total'] or 0
        monthly_sales.append(float(total))
    context = {
        'total_products': total_products,
        'low_stocks': low_stocks,
        'total_categories': total_categories,
        'total_inventory_value': total_inventory_value,
        'usd_buy': usd_buy,
        'usd_sell': usd_sell,
        'total_sales_today': total_sales_today,
        'profit_today': profit_today,
        'months': persian_months,
        'monthly_sales': monthly_sales,
    }
    return render(request, 'inventory/dashboard.html', context)

# ==================== مدیریت اجناس ====================
@login_required
def product_list(request):
    products = Product.objects.filter(is_active=True)
    for p in products:
        p.stock_qty = p.stock.quantity if hasattr(p, 'stock') else 0
    return render(request, 'inventory/product_list.html', {'products': products})

@login_required
def product_create(request):
    if request.user.groups.filter(name='حسابدار').exists():
        raise PermissionDenied("شما مجوز ایجاد جنس جدید ندارید.")
    last_product = Product.objects.all().order_by('-code').first()
    new_code = last_product.code + 1 if last_product else 101
    if request.method == 'POST':
        name = request.POST['name']
        currency_id = request.POST['currency']
        unit_id = request.POST['unit']
        purchase_price = request.POST['purchase_price']
        selling_price = request.POST['selling_price']
        initial_stock = int(request.POST.get('initial_stock', 0))
        description = request.POST.get('description', '')
        currency = get_object_or_404(Currency, id=currency_id)
        unit = get_object_or_404(UnitOfMeasure, id=unit_id)
        with transaction.atomic():
            product = Product.objects.create(
                name=name, code=new_code, category=None, currency=currency,
                purchase_price=purchase_price, selling_price=selling_price,
                unit=unit, description=description, is_active=True
            )
            Stock.objects.create(product=product, quantity=initial_stock)
            if initial_stock > 0:
                Transaction.objects.create(
                    product=product, transaction_type='IN', quantity=initial_stock,
                    price_at_time=purchase_price, description="موجودی اولیه"
                )
        messages.success(request, f'جنس {name} با کد {new_code} اضافه شد.')
        return redirect('inventory:product_list')
    units = UnitOfMeasure.objects.filter(is_active=True)
    currencies = Currency.objects.filter(is_active=True)
    return render(request, 'inventory/product_form.html', {
        'new_code': new_code,
        'units': units,
        'currencies': currencies,
    })

@login_required
def product_edit(request, pk):
    if request.user.groups.filter(name='حسابدار').exists():
        raise PermissionDenied("شما مجوز ویرایش ندارید.")
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.name = request.POST['name']
        product.currency_id = request.POST['currency']
        product.unit_id = request.POST['unit']
        product.purchase_price = request.POST['purchase_price']
        product.selling_price = request.POST['selling_price']
        product.description = request.POST.get('description', '')
        product.save()
        new_stock_qty = int(request.POST.get('initial_stock', 0))
        stock, created = Stock.objects.get_or_create(product=product)
        if new_stock_qty != stock.quantity:
            diff = new_stock_qty - stock.quantity
            stock.quantity = new_stock_qty
            stock.save()
            if diff > 0:
                Transaction.objects.create(
                    product=product, transaction_type='IN', quantity=diff,
                    price_at_time=product.purchase_price, description="افزایش موجودی"
                )
            elif diff < 0:
                Transaction.objects.create(
                    product=product, transaction_type='OUT', quantity=-diff,
                    price_at_time=product.purchase_price, description="کاهش موجودی"
                )
        messages.success(request, f'جنس {product.name} ویرایش شد.')
        return redirect('inventory:product_list')
    units = UnitOfMeasure.objects.filter(is_active=True)
    currencies = Currency.objects.filter(is_active=True)
    return render(request, 'inventory/product_form.html', {
        'product': product,
        'edit_mode': True,
        'new_code': product.code,
        'units': units,
        'currencies': currencies,
    })

@login_required
def product_delete(request, pk):
    """
    حذف جنس با مدیریت وابستگی‌ها و نمایش خطای مناسب
    """
    if request.user.groups.filter(name='حسابدار').exists():
        raise PermissionDenied("شما مجوز حذف ندارید.")
    
    product = get_object_or_404(Product, pk=pk)
    name = product.name
    
    try:
        with transaction.atomic():
            # حذف تراکنش‌های انبار
            Transaction.objects.filter(product=product).delete()
            # حذف موجودی
            Stock.objects.filter(product=product).delete()
            # حذف آیتم‌های فروش
            SaleItem.objects.filter(product=product).delete()
            # حذف آیتم‌های خرید
            PurchaseItem.objects.filter(product=product).delete()
            # حذف خود محصول
            product.delete()
        messages.success(request, f'جنس {name} با موفقیت حذف شد.')
    except Exception as e:
        messages.error(request, f'خطا در حذف جنس: {e}')
    
    return redirect('inventory:product_list')

# ==================== ورود و خروج کالا ====================
@login_required
def stock_in(request):
    if request.user.groups.filter(name='حسابدار').exists():
        raise PermissionDenied("شما مجوز ورود کالا ندارید.")
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
    products = Product.objects.filter(is_active=True)
    return render(request, 'inventory/stock_form.html', {'products': products, 'type': 'IN'})

@login_required
def stock_out(request):
    if request.user.groups.filter(name='حسابدار').exists():
        raise PermissionDenied("شما مجوز خروج کالا ندارید.")
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
    products = Product.objects.filter(is_active=True)
    return render(request, 'inventory/stock_form.html', {'products': products, 'type': 'OUT'})

# ==================== سرمایه دکان ====================
@login_required
def capital(request):
    usd_buy, _ = get_usd_afn_rate()
    afghan_capital = Stock.objects.filter(
        product__currency__code='AFN', product__is_active=True
    ).annotate(total_value=F('quantity') * F('product__purchase_price')).aggregate(sum=Sum('total_value'))['sum'] or 0
    dollar_capital = Stock.objects.filter(
        product__currency__code='USD', product__is_active=True
    ).annotate(total_value=F('quantity') * F('product__purchase_price')).aggregate(sum=Sum('total_value'))['sum'] or 0
    afghan_capital_in_usd = afghan_capital / usd_buy if usd_buy else 0
    total_capital_usd = afghan_capital_in_usd + dollar_capital
    product_count = Product.objects.filter(is_active=True).count()
    low_stock_items = Stock.objects.filter(quantity__lte=F('minimum_threshold')).count()
    context = {
        'afghan_capital': afghan_capital,
        'dollar_capital': dollar_capital,
        'total_capital_usd': total_capital_usd,
        'exchange_rate': usd_buy,
        'product_count': product_count,
        'low_stock_items': low_stock_items,
    }
    return render(request, 'inventory/capital.html', context)