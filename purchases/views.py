from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import jdatetime

from inventory.models import Product, Stock, Transaction
from suppliers.models import Supplier
from transactions.models import FinancialTransaction
from .models import PurchaseInvoice, PurchaseItem
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
def purchase_create(request):
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        currency_id = request.POST.get('currency')
        payment_method = request.POST.get('payment_method')
        paid_amount = Decimal(request.POST.get('paid_amount', 0))
        transaction_date_jalali = request.POST.get('transaction_date')
        gregorian_date = jalali_to_gregorian(transaction_date_jalali) or timezone.now().date()

        supplier = get_object_or_404(Supplier, id=supplier_id)
        currency = get_object_or_404(Currency, id=currency_id)

        with transaction.atomic():
            invoice = PurchaseInvoice.objects.create(
                supplier=supplier,
                date=gregorian_date,
                currency=currency,
                payment_method=payment_method,
                total_amount=0,
                paid_amount=paid_amount
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

                    PurchaseItem.objects.create(
                        invoice=invoice,
                        product=product,
                        quantity=qty,
                        unit_price=unit_price,
                        total_price=total_price
                    )

                    stock, _ = Stock.objects.get_or_create(product=product)
                    stock.quantity += qty
                    stock.save()

                    Transaction.objects.create(
                        product=product,
                        transaction_type='IN',
                        quantity=qty,
                        price_at_time=unit_price,
                        description=f"خرید فاکتور {invoice.invoice_number}"
                    )

            invoice.total_amount = total
            if payment_method == 'CASH':
                invoice.paid_amount = total
            else:
                invoice.paid_amount = paid_amount
            invoice.save()

            FinancialTransaction.objects.create(
                transaction_date=gregorian_date,
                amount=total,
                transaction_type='IN',
                person_type='SUPPLIER',
                supplier=supplier,
                description=f"خرید فاکتور {invoice.invoice_number}",
                created_by=request.user
            )

            messages.success(request, f'خرید با موفقیت ثبت شد. شماره فاکتور: {invoice.invoice_number}')
            return redirect('purchases:purchase_list')

    suppliers = Supplier.objects.all()
    products = Product.objects.filter(is_active=True)
    currencies = Currency.objects.filter(is_active=True)   # <-- دریافت واحدهای پول فعال
    today_jalali = jdatetime.date.today().strftime('%Y/%m/%d')
    return render(request, 'purchases/purchase_form.html', {
        'suppliers': suppliers,
        'products': products,
        'currencies': currencies,
        'today_jalali': today_jalali,
    })

@login_required
def purchase_list(request):
    purchases = PurchaseInvoice.objects.all().order_by('-date')
    from_date_jalali = request.GET.get('from_date', '').strip()
    to_date_jalali = request.GET.get('to_date', '').strip()
    invoice_no = request.GET.get('invoice_no', '').strip()
    supplier_name = request.GET.get('supplier_name', '').strip()

    from_date = jalali_to_gregorian(from_date_jalali) if from_date_jalali else None
    to_date = jalali_to_gregorian(to_date_jalali) if to_date_jalali else None

    if from_date:
        purchases = purchases.filter(date__gte=from_date)
    if to_date:
        purchases = purchases.filter(date__lte=to_date)
    if invoice_no:
        purchases = purchases.filter(invoice_number__icontains=invoice_no)
    if supplier_name:
        purchases = purchases.filter(supplier__name__icontains=supplier_name)

    context = {
        'purchases': purchases,
        'from_date': from_date_jalali,
        'to_date': to_date_jalali,
        'invoice_no': invoice_no,
        'supplier_name': supplier_name,
        'today_jalali': jdatetime.date.today().strftime('%Y/%m/%d'),
    }
    return render(request, 'purchases/purchase_list.html', context)

@login_required
def purchase_detail(request, pk):
    purchase = get_object_or_404(PurchaseInvoice, pk=pk)
    items = purchase.items.all()
    shop_info, created = ShopInfo.objects.get_or_create(pk=1)
    if created:
        shop_info.shop_name = "فروشگاه مواد غذایی توفیق الهی"
        shop_info.address = "کابل، جادهٔ میوند، پلاک ۱۲۳"
        shop_info.phone = "۰۷۸۲ ۱۲۳ ۴۵۶"
        shop_info.email = "info@tofiq.com"
        shop_info.save()
    return render(request, 'purchases/purchase_detail.html', {
        'purchase': purchase,
        'items': items,
        'shop_info': shop_info,
    })

@login_required
def purchase_edit(request, pk):
    purchase = get_object_or_404(PurchaseInvoice, pk=pk)
    if request.method == 'POST':
        with transaction.atomic():
            for item in purchase.items.all():
                stock = Stock.objects.get(product=item.product)
                stock.quantity -= item.quantity
                stock.save()
                Transaction.objects.filter(
                    product=item.product,
                    description__contains=f"خرید فاکتور {purchase.invoice_number}"
                ).delete()

            purchase.items.all().delete()
            FinancialTransaction.objects.filter(
                person_type='SUPPLIER',
                supplier=purchase.supplier,
                description__contains=f"خرید فاکتور {purchase.invoice_number}"
            ).delete()

            supplier_id = request.POST.get('supplier')
            currency_id = request.POST.get('currency')
            payment_method = request.POST.get('payment_method')
            paid_amount = Decimal(request.POST.get('paid_amount', 0))
            transaction_date_jalali = request.POST.get('transaction_date')
            gregorian_date = jalali_to_gregorian(transaction_date_jalali) or timezone.now().date()

            supplier = get_object_or_404(Supplier, id=supplier_id)
            currency = get_object_or_404(Currency, id=currency_id)
            purchase.supplier = supplier
            purchase.date = gregorian_date
            purchase.currency = currency
            purchase.payment_method = payment_method
            purchase.paid_amount = paid_amount

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

                    PurchaseItem.objects.create(
                        invoice=purchase,
                        product=product,
                        quantity=qty,
                        unit_price=unit_price,
                        total_price=total_price
                    )

                    stock, _ = Stock.objects.get_or_create(product=product)
                    stock.quantity += qty
                    stock.save()

                    Transaction.objects.create(
                        product=product,
                        transaction_type='IN',
                        quantity=qty,
                        price_at_time=unit_price,
                        description=f"ویرایش خرید فاکتور {purchase.invoice_number}"
                    )

            purchase.total_amount = total
            if payment_method == 'CASH':
                purchase.paid_amount = total
            else:
                purchase.paid_amount = paid_amount
            purchase.save()

            FinancialTransaction.objects.create(
                transaction_date=gregorian_date,
                amount=total,
                transaction_type='IN',
                person_type='SUPPLIER',
                supplier=supplier,
                description=f"خرید فاکتور {purchase.invoice_number}",
                created_by=request.user
            )

            messages.success(request, f'فاکتور خرید {purchase.invoice_number} با موفقیت ویرایش شد.')
            return redirect('purchases:purchase_list')

    suppliers = Supplier.objects.all()
    products = Product.objects.filter(is_active=True)
    currencies = Currency.objects.filter(is_active=True)   # <-- دریافت واحدهای پول فعال
    today_jalali = jdatetime.date.today().strftime('%Y/%m/%d')
    return render(request, 'purchases/purchase_edit.html', {
        'purchase': purchase,
        'suppliers': suppliers,
        'products': products,
        'currencies': currencies,
        'today_jalali': today_jalali,
    })

@login_required
def purchase_delete(request, pk):
    purchase = get_object_or_404(PurchaseInvoice, pk=pk)
    with transaction.atomic():
        for item in purchase.items.all():
            stock = Stock.objects.get(product=item.product)
            stock.quantity -= item.quantity
            stock.save()
            Transaction.objects.filter(
                product=item.product,
                description__contains=f"خرید فاکتور {purchase.invoice_number}"
            ).delete()

        FinancialTransaction.objects.filter(
            person_type='SUPPLIER',
            supplier=purchase.supplier,
            description__contains=f"خرید فاکتور {purchase.invoice_number}"
        ).delete()

        purchase.delete()
    messages.success(request, f'فاکتور خرید {purchase.invoice_number} با موفقیت حذف شد.')
    return redirect('purchases:purchase_list')