from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.db import models
from .models import Customer
from transactions.models import FinancialTransaction
from sales.models import Sale
from settings_app.models import Currency

def calculate_customer_balance(customer):
    # فروش قرضی = بدهکار
    total_credit_sales = Sale.objects.filter(
        customer=customer,
        payment_method='CREDIT'
    ).aggregate(total=models.Sum('remaining_amount'))['total'] or Decimal('0')

    # واریز (IN) = بستانکار
    total_in = FinancialTransaction.objects.filter(
        person_type='CUSTOMER', 
        customer=customer, 
        transaction_type='IN'
    ).exclude(description__icontains='قرض').aggregate(
        total=models.Sum('amount')
    )['total'] or Decimal('0')
    
    # برداشت (OUT) = بدهکار
    total_out = FinancialTransaction.objects.filter(
        person_type='CUSTOMER', 
        customer=customer, 
        transaction_type='OUT'
    ).exclude(description__icontains='قرض').aggregate(
        total=models.Sum('amount')
    )['total'] or Decimal('0')

    debit = total_credit_sales + total_out
    credit = total_in
    balance = debit - credit
    return balance

@login_required
def customer_list(request):
    name_query = request.GET.get('name', '').strip()
    phone_query = request.GET.get('phone', '').strip()
    currency_query = request.GET.get('currency', '')

    customers = Customer.objects.all().order_by('-created_at')
    if name_query:
        customers = customers.filter(name__icontains=name_query)
    if phone_query:
        customers = customers.filter(phone__icontains=phone_query)
    if currency_query:
        customers = customers.filter(currency__id=currency_query)

    for c in customers:
        c.balance = calculate_customer_balance(c)

    currencies = Currency.objects.filter(is_active=True)
    return render(request, 'customers/customer_list.html', {
        'customers': customers,
        'currencies': currencies,
    })

@login_required
def customer_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone', '')
        currency_id = request.POST.get('currency')
        address = request.POST.get('address', '')
        currency = get_object_or_404(Currency, id=currency_id)
        Customer.objects.create(
            name=name,
            phone=phone,
            currency=currency,
            address=address
        )
        messages.success(request, f'مشتری {name} با موفقیت اضافه شد.')
        return redirect('customers:customer_list')
    currencies = Currency.objects.filter(is_active=True)
    return render(request, 'customers/customer_form.html', {'currencies': currencies})

@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.name = request.POST.get('name')
        customer.phone = request.POST.get('phone', '')
        customer.currency_id = request.POST.get('currency')
        customer.address = request.POST.get('address', '')
        customer.save()
        messages.success(request, f'مشتری {customer.name} با موفقیت ویرایش شد.')
        return redirect('customers:customer_list')
    currencies = Currency.objects.filter(is_active=True)
    return render(request, 'customers/customer_form.html', {
        'customer': customer,
        'currencies': currencies,
        'edit_mode': True,
    })

@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    name = customer.name
    customer.delete()
    messages.success(request, f'مشتری {name} با موفقیت حذف شد.')
    return redirect('customers:customer_list')

@login_required
def customer_transactions(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    financial_transactions = FinancialTransaction.objects.filter(
        person_type='CUSTOMER',
        customer=customer
    ).exclude(description__icontains='قرض').order_by('date_created')

    sales = Sale.objects.filter(
        customer=customer,
        payment_method='CREDIT',
        remaining_amount__gt=0
    ).order_by('date')

    transactions_list = []
    total_debit = Decimal('0')
    total_credit = Decimal('0')

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

    for sale in sales:
        amount = sale.remaining_amount
        total_debit += amount
        transactions_list.append({
            'date': sale.date,
            'type': 'فروش قرضی',
            'description': f'فاکتور {sale.invoice_number} - قرض',
            'debit': amount,
            'credit': None,
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

    return render(request, 'customers/customer_transactions.html', {
        'customer': customer,
        'transactions': transactions_list,
        'total_debit': total_debit,
        'total_credit': total_credit,
    })