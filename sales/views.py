from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from decimal import Decimal
import jdatetime

from inventory.models import Product, Stock, Transaction
from customers.models import Customer
from .models import Sale, SaleItem
from settings_app.models import ShopInfo, Currency

def jalali_to_gregorian(jalali_str):
    try:
        parts = jalali_str.split('/')
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
        return jdatetime.date(year, month, day).togregorian()
    except:
        return None

@login_required
def new_sale(request):
    if request.method == 'POST':
        customer_type = request.POST.get('customer_type')
        currency_id = request.POST.get('currency')
        payment_method = request.POST.get('payment_method')
        paid_amount = Decimal(request.POST.get('paid_amount', 0))
        transaction_date_jalali = request.POST.get('transaction_date')
        gregorian_date = jalali_to_gregorian(transaction_date_jalali) or timezone.now().date()

        if customer_type == 'existing':
            customer = get_object_or_404(Customer, id=request.POST.get('customer_id'))
            customer_name = customer.name
            customer_phone = customer.phone
        else:
            customer = None
            customer_name = request.POST.get('customer_name')
            customer_phone = request.POST.get('customer_phone')

        currency = get_object_or_404(Currency, id=currency_id)

        with transaction.atomic():
            sale = Sale.objects.create(
                transaction_date=gregorian_date,
                customer=customer,
                customer_name=customer_name,
                customer_phone=customer_phone,
                currency=currency,
                payment_method=payment_method,
                total_amount=0,
                paid_amount=paid_amount,
                remaining_amount=0
            )
            total = Decimal('0')
            product_ids = request.POST.getlist('product_id')
            quantities = request.POST.getlist('quantity')
            prices = request.POST.getlist('unit_price')

            for i in range(len(product_ids)):
                if product_ids[i] and quantities[i]:
                    product = get_object_or_404(Product, id=product_ids[i])
                    qty = int(quantities[i])
                    unit_price = Decimal(prices[i])
                    total_price = qty * unit_price
                    total += total_price

                    SaleItem.objects.create(
                        sale=sale,
                        product=product,
                        quantity=qty,
                        unit_price=unit_price,
                        total_price=total_price
                    )

                    stock = get_object_or_404(Stock, product=product)
                    if stock.quantity < qty:
                        raise Exception(f"موجودی {product.name} کافی نیست")
                    stock.quantity -= qty
                    stock.save()

                    Transaction.objects.create(
                        product=product,
                        transaction_type='OUT',
                        quantity=qty,
                        price_at_time=unit_price,
                        description=f"فروش فاکتور {sale.invoice_number}"
                    )

            sale.total_amount = total
            if payment_method == 'CASH':
                sale.paid_amount = total
            else:
                sale.paid_amount = paid_amount
            sale.save()

            messages.success(request, f'فروش با موفقیت ثبت شد. شماره فاکتور: {sale.invoice_number}')
            return redirect('sales:sale_list')

    products = Product.objects.filter(is_active=True)
    customers = Customer.objects.all()
    currencies = Currency.objects.filter(is_active=True)   # <-- دریافت واحدهای پول فعال
    today_jalali = jdatetime.date.today().strftime('%Y/%m/%d')
    return render(request, 'sales/sale_form.html', {
        'products': products,
        'customers': customers,
        'currencies': currencies,
        'today_jalali': today_jalali,
    })

@login_required
def sale_list(request):
    sales = Sale.objects.all().order_by('-transaction_date', '-id')
    from_date_jalali = request.GET.get('from_date', '').strip()
    to_date_jalali = request.GET.get('to_date', '').strip()
    invoice_no = request.GET.get('invoice_no', '').strip()
    customer_name = request.GET.get('customer_name', '').strip()
    customer_phone = request.GET.get('customer_phone', '').strip()

    from_date = jalali_to_gregorian(from_date_jalali) if from_date_jalali else None
    to_date = jalali_to_gregorian(to_date_jalali) if to_date_jalali else None

    if from_date:
        sales = sales.filter(transaction_date__gte=from_date)
    if to_date:
        sales = sales.filter(transaction_date__lte=to_date)
    if invoice_no:
        sales = sales.filter(invoice_number__icontains=invoice_no)
    if customer_name:
        sales = sales.filter(Q(customer__name__icontains=customer_name) | Q(customer_name__icontains=customer_name))
    if customer_phone:
        sales = sales.filter(Q(customer__phone__icontains=customer_phone) | Q(customer_phone__icontains=customer_phone))

    total_profit = Decimal('0')
    for sale in sales:
        for item in sale.items.all():
            profit = (item.unit_price - item.product.purchase_price) * item.quantity
            total_profit += profit

    context = {
        'sales': sales,
        'from_date': from_date_jalali,
        'to_date': to_date_jalali,
        'invoice_no': invoice_no,
        'customer_name': customer_name,
        'customer_phone': customer_phone,
        'total_profit': total_profit,
        'today_jalali': jdatetime.date.today().strftime('%Y/%m/%d'),
    }
    return render(request, 'sales/sale_list.html', context)

@login_required
def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    items = sale.items.all()
    shop_info, created = ShopInfo.objects.get_or_create(pk=1)
    if created:
        shop_info.shop_name = "فروشگاه مواد غذایی توفیق الهی"
        shop_info.address = "کابل، جادهٔ میوند، پلاک ۱۲۳"
        shop_info.phone = "۰۷۸۲ ۱۲۳ ۴۵۶"
        shop_info.email = "info@tofiq.com"
        shop_info.save()
    return render(request, 'sales/sale_detail.html', {
        'sale': sale,
        'items': items,
        'shop_info': shop_info,
    })

@login_required
def sale_edit(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        with transaction.atomic():
            for item in sale.items.all():
                stock = Stock.objects.get(product=item.product)
                stock.quantity += item.quantity
                stock.save()
                Transaction.objects.filter(
                    product=item.product,
                    description__contains=f"فروش فاکتور {sale.invoice_number}"
                ).delete()
            sale.items.all().delete()

            customer_type = request.POST.get('customer_type')
            currency_id = request.POST.get('currency')
            payment_method = request.POST.get('payment_method')
            paid_amount = Decimal(request.POST.get('paid_amount', 0))
            transaction_date_jalali = request.POST.get('transaction_date')
            gregorian_date = jalali_to_gregorian(transaction_date_jalali) or timezone.now().date()

            if customer_type == 'existing':
                customer = get_object_or_404(Customer, id=request.POST.get('customer_id'))
                sale.customer = customer
                sale.customer_name = customer.name
                sale.customer_phone = customer.phone
            else:
                sale.customer = None
                sale.customer_name = request.POST.get('customer_name')
                sale.customer_phone = request.POST.get('customer_phone')

            currency = get_object_or_404(Currency, id=currency_id)
            sale.transaction_date = gregorian_date
            sale.currency = currency
            sale.payment_method = payment_method
            sale.paid_amount = paid_amount

            total = Decimal('0')
            product_ids = request.POST.getlist('product_id')
            quantities = request.POST.getlist('quantity')
            prices = request.POST.getlist('unit_price')

            for i in range(len(product_ids)):
                if product_ids[i] and quantities[i]:
                    product = get_object_or_404(Product, id=product_ids[i])
                    qty = int(quantities[i])
                    unit_price = Decimal(prices[i])
                    total_price = qty * unit_price
                    total += total_price

                    SaleItem.objects.create(
                        sale=sale,
                        product=product,
                        quantity=qty,
                        unit_price=unit_price,
                        total_price=total_price
                    )

                    stock = Stock.objects.get(product=product)
                    if stock.quantity < qty:
                        raise Exception(f"موجودی {product.name} کافی نیست")
                    stock.quantity -= qty
                    stock.save()

                    Transaction.objects.create(
                        product=product,
                        transaction_type='OUT',
                        quantity=qty,
                        price_at_time=unit_price,
                        description=f"ویرایش فروش فاکتور {sale.invoice_number}"
                    )

            sale.total_amount = total
            if payment_method == 'CASH':
                sale.paid_amount = total
            else:
                sale.paid_amount = paid_amount
            sale.save()

            messages.success(request, f'فاکتور {sale.invoice_number} با موفقیت ویرایش شد.')
            return redirect('sales:sale_list')

    products = Product.objects.filter(is_active=True)
    customers = Customer.objects.all()
    currencies = Currency.objects.filter(is_active=True)   # <-- دریافت واحدهای پول فعال
    today_jalali = jdatetime.date.today().strftime('%Y/%m/%d')
    return render(request, 'sales/sale_edit.html', {
        'sale': sale,
        'products': products,
        'customers': customers,
        'currencies': currencies,
        'today_jalali': today_jalali,
    })

@login_required
def sale_delete(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    with transaction.atomic():
        for item in sale.items.all():
            stock = Stock.objects.get(product=item.product)
            stock.quantity += item.quantity
            stock.save()
            Transaction.objects.filter(
                product=item.product,
                description__contains=f"فروش فاکتور {sale.invoice_number}"
            ).delete()
        sale.delete()
    messages.success(request, f'فاکتور {sale.invoice_number} حذف شد.')
    return redirect('sales:sale_list')