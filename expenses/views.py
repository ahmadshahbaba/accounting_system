from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal
import jdatetime
from .models import GeneralExpense

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
def expense_list(request):
    expenses = GeneralExpense.objects.all().order_by('-date')
    
    # دریافت پارامترهای جستجو
    from_date_jalali = request.GET.get('from_date', '').strip()
    to_date_jalali = request.GET.get('to_date', '').strip()
    expense_type = request.GET.get('expense_type', '').strip()
    currency = request.GET.get('currency', '').strip()
    
    # تبدیل تاریخ‌ها به میلادی
    from_date = jalali_to_gregorian(from_date_jalali) if from_date_jalali else None
    to_date = jalali_to_gregorian(to_date_jalali) if to_date_jalali else None
    
    # اعمال فیلترها
    if from_date:
        expenses = expenses.filter(date__gte=from_date)
    if to_date:
        expenses = expenses.filter(date__lte=to_date)
    if expense_type:
        expenses = expenses.filter(expense_type=expense_type)
    if currency:
        expenses = expenses.filter(currency=currency)
    
    # محاسبه جمع کل مبلغ برای هر واحد پول
    total_afn = expenses.filter(currency='AFN').aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_usd = expenses.filter(currency='USD').aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    context = {
        'expenses': expenses,
        'from_date': from_date_jalali,
        'to_date': to_date_jalali,
        'expense_type': expense_type,
        'currency': currency,
        'total_afn': total_afn,
        'total_usd': total_usd,
        'today_jalali': jdatetime.date.today().strftime('%Y/%m/%d'),
    }
    return render(request, 'expenses/expense_list.html', context)

@login_required
def expense_create(request):
    if request.method == 'POST':
        expense_type = request.POST.get('expense_type')
        currency = request.POST.get('currency')
        amount = request.POST.get('amount')
        description = request.POST.get('description', '')
        jalali_date = request.POST.get('transaction_date')
        gregorian_date = jalali_to_gregorian(jalali_date)
        if gregorian_date is None:
            gregorian_date = timezone.now().date()

        GeneralExpense.objects.create(
            date=gregorian_date,
            expense_type=expense_type,
            currency=currency,
            amount=amount,
            description=description,
            created_by=request.user
        )
        messages.success(request, 'مصرف با موفقیت ثبت شد.')
        return redirect('expenses:expense_list')

    today_jalali = jdatetime.date.today().strftime('%Y/%m/%d')
    return render(request, 'expenses/expense_form.html', {'today_jalali': today_jalali})