from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from decimal import Decimal
import jdatetime
import json

from .models import FinancialTransaction
from customers.models import Customer
from suppliers.models import Supplier
from misc_persons.models import MiscPerson

def jalali_to_gregorian(jalali_str):
    try:
        parts = jalali_str.split('/')
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
        return jdatetime.date(year, month, day).togregorian()
    except:
        return timezone.now().date()

@login_required
def transaction_list(request):
    transactions = FinancialTransaction.objects.all().order_by('-transaction_date')
    return render(request, 'transactions/transaction_list.html', {'transactions': transactions})

@login_required
def transaction_create_in(request):
    """
    ثبت واریز به حساب فروشگاه (IN)
    یعنی شخص به حساب ما پول واریز می‌کند => IN
    """
    if request.method == 'POST':
        person_type = request.POST.get('person_type')
        person_id = request.POST.get('person_id')
        amount = Decimal(request.POST.get('amount'))
        description = request.POST.get('description', '')
        jalali_date = request.POST.get('transaction_date')
        gregorian_date = jalali_to_gregorian(jalali_date)

        data = {
            'transaction_type': 'IN',   # ← واریز = IN
            'person_type': person_type,
            'amount': amount,
            'description': description,
            'transaction_date': gregorian_date,
            'created_by': request.user
        }
        if person_type == 'CUSTOMER':
            data['customer_id'] = person_id
        elif person_type == 'SUPPLIER':
            data['supplier_id'] = person_id
        else:
            data['misc_person_id'] = person_id

        FinancialTransaction.objects.create(**data)
        messages.success(request, 'واریز با موفقیت ثبت شد.')
        return redirect('transactions:transaction_list')

    customers = Customer.objects.all()
    suppliers = Supplier.objects.all()
    misc_persons = MiscPerson.objects.all()
    today_jalali = jdatetime.date.today().strftime('%Y/%m/%d')
    return render(request, 'transactions/transaction_form_in.html', {
        'customers_json': json.dumps(list(customers.values('id', 'name'))),
        'suppliers_json': json.dumps(list(suppliers.values('id', 'name'))),
        'misc_persons_json': json.dumps(list(misc_persons.values('id', 'name'))),
        'today_jalali': today_jalali,
    })

@login_required
def transaction_create_out(request):
    """
    ثبت برداشت از حساب فروشگاه (OUT)
    یعنی شخص از حساب ما پول برداشت می‌کند => OUT
    """
    if request.method == 'POST':
        person_type = request.POST.get('person_type')
        person_id = request.POST.get('person_id')
        amount = Decimal(request.POST.get('amount'))
        description = request.POST.get('description', '')
        jalali_date = request.POST.get('transaction_date')
        gregorian_date = jalali_to_gregorian(jalali_date)

        data = {
            'transaction_type': 'OUT',   # ← برداشت = OUT
            'person_type': person_type,
            'amount': amount,
            'description': description,
            'transaction_date': gregorian_date,
            'created_by': request.user
        }
        if person_type == 'CUSTOMER':
            data['customer_id'] = person_id
        elif person_type == 'SUPPLIER':
            data['supplier_id'] = person_id
        else:
            data['misc_person_id'] = person_id

        FinancialTransaction.objects.create(**data)
        messages.success(request, 'برداشت با موفقیت ثبت شد.')
        return redirect('transactions:transaction_list')

    customers = Customer.objects.all()
    suppliers = Supplier.objects.all()
    misc_persons = MiscPerson.objects.all()
    today_jalali = jdatetime.date.today().strftime('%Y/%m/%d')
    return render(request, 'transactions/transaction_form_out.html', {
        'customers_json': json.dumps(list(customers.values('id', 'name'))),
        'suppliers_json': json.dumps(list(suppliers.values('id', 'name'))),
        'misc_persons_json': json.dumps(list(misc_persons.values('id', 'name'))),
        'today_jalali': today_jalali,
    })

@login_required
def transaction_edit(request, pk):
    transaction = get_object_or_404(FinancialTransaction, pk=pk)
    if request.method == 'POST':
        transaction.transaction_date = jalali_to_gregorian(request.POST.get('transaction_date'))
        transaction.amount = Decimal(request.POST.get('amount'))
        transaction.description = request.POST.get('description', '')
        transaction.save()
        messages.success(request, 'تراکنش با موفقیت ویرایش شد.')
        return redirect('transactions:transaction_list')

    customers = Customer.objects.all()
    suppliers = Supplier.objects.all()
    misc_persons = MiscPerson.objects.all()
    try:
        jalali_date = jdatetime.date.fromgregorian(date=transaction.transaction_date).strftime('%Y/%m/%d')
    except:
        jalali_date = jdatetime.date.today().strftime('%Y/%m/%d')

    return render(request, 'transactions/transaction_edit.html', {
        'transaction': transaction,
        'customers': customers,
        'suppliers': suppliers,
        'misc_persons': misc_persons,
        'today_jalali': jalali_date,
        'customers_json': json.dumps(list(customers.values('id', 'name'))),
        'suppliers_json': json.dumps(list(suppliers.values('id', 'name'))),
        'misc_persons_json': json.dumps(list(misc_persons.values('id', 'name'))),
    })

@login_required
def transaction_delete(request, pk):
    transaction = get_object_or_404(FinancialTransaction, pk=pk)
    transaction.delete()
    messages.success(request, 'تراکنش با موفقیت حذف شد.')
    return redirect('transactions:transaction_list')