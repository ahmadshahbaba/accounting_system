from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from .models import MiscPerson
from transactions.models import FinancialTransaction
from settings_app.models import Currency

def calculate_misc_balance(person):
    financial_transactions = FinancialTransaction.objects.filter(
        person_type='MISC',
        misc_person=person
    )
    total_debit = sum(ft.amount for ft in financial_transactions if ft.transaction_type == 'IN')
    total_credit = sum(ft.amount for ft in financial_transactions if ft.transaction_type == 'OUT')
    return total_debit - total_credit

@login_required
def misc_list(request):
    name_query = request.GET.get('name', '').strip()
    phone_query = request.GET.get('phone', '').strip()
    currency_query = request.GET.get('currency', '')

    persons = MiscPerson.objects.all().order_by('-created_at')
    if name_query:
        persons = persons.filter(name__icontains=name_query)
    if phone_query:
        persons = persons.filter(phone__icontains=phone_query)
    if currency_query:
        persons = persons.filter(currency__id=currency_query)

    for p in persons:
        p.balance = calculate_misc_balance(p)

    currencies = Currency.objects.filter(is_active=True)
    return render(request, 'misc_persons/misc_list.html', {
        'persons': persons,
        'currencies': currencies,
    })

@login_required
def misc_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone', '')
        currency_id = request.POST.get('currency')
        address = request.POST.get('address', '')
        currency = get_object_or_404(Currency, id=currency_id)
        MiscPerson.objects.create(
            name=name,
            phone=phone,
            currency=currency,
            address=address
        )
        messages.success(request, f'شخص متفرقه {name} با موفقیت اضافه شد.')
        return redirect('misc_persons:misc_list')

    currencies = Currency.objects.filter(is_active=True)
    return render(request, 'misc_persons/misc_form.html', {'currencies': currencies})

@login_required
def misc_edit(request, pk):
    person = get_object_or_404(MiscPerson, pk=pk)
    if request.method == 'POST':
        person.name = request.POST.get('name')
        person.phone = request.POST.get('phone', '')
        person.currency_id = request.POST.get('currency')
        person.address = request.POST.get('address', '')
        person.save()
        messages.success(request, f'شخص متفرقه {person.name} با موفقیت ویرایش شد.')
        return redirect('misc_persons:misc_list')

    currencies = Currency.objects.filter(is_active=True)
    return render(request, 'misc_persons/misc_form.html', {
        'person': person,
        'currencies': currencies,
        'edit_mode': True,
    })

@login_required
def misc_delete(request, pk):
    person = get_object_or_404(MiscPerson, pk=pk)
    name = person.name
    person.delete()
    messages.success(request, f'شخص متفرقه {name} با موفقیت حذف شد.')
    return redirect('misc_persons:misc_list')

@login_required
def misc_transactions(request, pk):
    person = get_object_or_404(MiscPerson, pk=pk)
    financial_transactions = FinancialTransaction.objects.filter(
        person_type='MISC',
        misc_person=person
    ).order_by('-date_created')

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

    transactions_list.sort(key=lambda x: x['date'], reverse=True)

    balance = Decimal('0')
    for item in transactions_list:
        if item['debit']:
            balance += item['debit']
        if item['credit']:
            balance -= item['credit']
        item['balance'] = balance

    return render(request, 'misc_persons/misc_transactions.html', {
        'person': person,
        'transactions': transactions_list,
    })