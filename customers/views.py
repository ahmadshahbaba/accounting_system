from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from .models import Customer
from transactions.models import FinancialTransaction
from sales.models import Sale
from settings_app.models import Currency

def calculate_customer_balance(customer):
    financial_transactions = FinancialTransaction.objects.filter(
        person_type='CUSTOMER', customer=customer
    )
    total_debit = sum(ft.amount for ft in financial_transactions if ft.transaction_type == 'IN')
    total_credit = sum(ft.amount for ft in financial_transactions if ft.transaction_type == 'OUT')
    sales = Sale.objects.filter(customer_name=customer.name)
    sales_total = sum(sale.total_amount for sale in sales)
    return (total_debit + sales_total) - total_credit

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

    for customer in customers:
        customer.balance = calculate_customer_balance(customer)

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
            name=name, phone=phone, currency=currency, address=address
        )
        messages.success(request, f'مشتری {name} اضافه شد.')
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
        messages.success(request, f'مشتری {customer.name} ویرایش شد.')
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
    messages.success(request, f'مشتری {name} حذف شد.')
    return redirect('customers:customer_list')

@login_required
def customer_transactions(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    financial_transactions = FinancialTransaction.objects.filter(
        person_type='CUSTOMER', customer=customer
    ).order_by('-date_created')
    sales = Sale.objects.filter(customer_name=customer.name).order_by('-date')
    transactions_list = []
    for ft in financial_transactions:
        transactions_list.append({
            'date': ft.date_created,
            'type': 'واریز' if ft.transaction_type == 'IN' else 'برداشت',
            'description': ft.description,
            'debit': ft.amount if ft.transaction_type == 'IN' else None,
            'credit': ft.amount if ft.transaction_type == 'OUT' else None,
            'balance': None,
        })
    for sale in sales:
        transactions_list.append({
            'date': sale.date,
            'type': 'فروش',
            'description': f'فاکتور شماره {sale.invoice_number}',
            'debit': sale.total_amount,
            'credit': None,
            'balance': None,
        })
    transactions_list.sort(key=lambda x: x['date'], reverse=True)
    balance = Decimal('0')
    for item in transactions_list:
        if item['debit']:
            balance += item['debit']
        if item['credit']:
            balance -= item['credit']
        item['balance'] = balance
    context = {
        'customer': customer,
        'transactions': transactions_list,
    }
    return render(request, 'customers/customer_transactions.html', context)