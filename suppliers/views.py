from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.db import models
from .models import Supplier
from purchases.models import PurchaseInvoice
from transactions.models import FinancialTransaction
from settings_app.models import Currency

def calculate_supplier_balance(supplier):
    # خریدها (بدهکار - افزایش بدهی به تهیه‌کننده)
    total_purchases = PurchaseInvoice.objects.filter(supplier=supplier).aggregate(
        total=models.Sum('total_amount')
    )['total'] or Decimal('0')

    # واریز به تهیه‌کننده (IN) = بستانکار (کاهش بدهی)
    total_in = FinancialTransaction.objects.filter(
        person_type='SUPPLIER', supplier=supplier, transaction_type='IN'
    ).exclude(description__icontains='قرض').aggregate(
        total=models.Sum('amount')
    )['total'] or Decimal('0')
    
    # برداشت از تهیه‌کننده (OUT) = بدهکار (افزایش بدهی)
    total_out = FinancialTransaction.objects.filter(
        person_type='SUPPLIER', supplier=supplier, transaction_type='OUT'
    ).exclude(description__icontains='قرض').aggregate(
        total=models.Sum('amount')
    )['total'] or Decimal('0')

    debit = total_purchases + total_out
    credit = total_in
    balance = debit - credit
    return balance

@login_required
def supplier_list(request):
    name_query = request.GET.get('name', '').strip()
    phone_query = request.GET.get('phone', '').strip()
    currency_query = request.GET.get('currency', '')

    suppliers = Supplier.objects.all().order_by('-created_at')
    if name_query:
        suppliers = suppliers.filter(name__icontains=name_query)
    if phone_query:
        suppliers = suppliers.filter(phone__icontains=phone_query)
    if currency_query:
        suppliers = suppliers.filter(currency__id=currency_query)

    for s in suppliers:
        s.balance = calculate_supplier_balance(s)

    currencies = Currency.objects.filter(is_active=True)
    return render(request, 'suppliers/supplier_list.html', {
        'suppliers': suppliers,
        'currencies': currencies,
    })

@login_required
def supplier_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone', '')
        currency_id = request.POST.get('currency')
        address = request.POST.get('address', '')
        currency = get_object_or_404(Currency, id=currency_id)
        Supplier.objects.create(name=name, phone=phone, currency=currency, address=address)
        messages.success(request, f'تهیه‌کننده {name} با موفقیت اضافه شد.')
        return redirect('suppliers:supplier_list')
    currencies = Currency.objects.filter(is_active=True)
    return render(request, 'suppliers/supplier_form.html', {'currencies': currencies})

@login_required
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.name = request.POST.get('name')
        supplier.phone = request.POST.get('phone', '')
        supplier.currency_id = request.POST.get('currency')
        supplier.address = request.POST.get('address', '')
        supplier.save()
        messages.success(request, f'تهیه‌کننده {supplier.name} با موفقیت ویرایش شد.')
        return redirect('suppliers:supplier_list')
    currencies = Currency.objects.filter(is_active=True)
    return render(request, 'suppliers/supplier_form.html', {
        'supplier': supplier,
        'currencies': currencies,
        'edit_mode': True,
    })

@login_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    name = supplier.name
    supplier.delete()
    messages.success(request, f'تهیه‌کننده {name} با موفقیت حذف شد.')
    return redirect('suppliers:supplier_list')

@login_required
def supplier_transactions(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)

    purchases = PurchaseInvoice.objects.filter(supplier=supplier).order_by('date')
    financial_transactions = FinancialTransaction.objects.filter(
        supplier=supplier
    ).exclude(description__icontains='قرض').order_by('date_created')

    transactions_list = []
    total_debit = Decimal('0')
    total_credit = Decimal('0')

    for p in purchases:
        amount = p.total_amount
        total_debit += amount
        transactions_list.append({
            'date': p.date,
            'type': 'خرید',
            'description': f'فاکتور {p.invoice_number}',
            'debit': amount,
            'credit': None,
            'balance': None,
        })

    for ft in financial_transactions:
        if ft.transaction_type == 'OUT':  # برداشت = بدهکار
            amount = ft.amount
            total_debit += amount
            transactions_list.append({
                'date': ft.date_created,
                'type': 'برداشت',
                'description': ft.description,
                'debit': amount,
                'credit': None,
                'balance': None,
            })
        else:  # IN = واریز = بستانکار
            amount = ft.amount
            total_credit += amount
            transactions_list.append({
                'date': ft.date_created,
                'type': 'واریز',
                'description': ft.description,
                'debit': None,
                'credit': amount,
                'balance': None,
            })

    transactions_list.sort(key=lambda x: x['date'])

    balance = Decimal('0')
    for item in transactions_list:
        if item['debit']:
            balance += item['debit']
        if item['credit']:
            balance -= item['credit']
        item['balance'] = balance

    return render(request, 'suppliers/supplier_transactions.html', {
        'supplier': supplier,
        'transactions': transactions_list,
        'total_debit': total_debit,
        'total_credit': total_credit,
    })