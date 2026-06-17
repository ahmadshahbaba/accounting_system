from django import template
import jdatetime

register = template.Library()

@register.filter
def to_jalali(date):
    if not date:
        return ""
    try:
        jalali_date = jdatetime.date.fromgregorian(date=date)
        month_names = ['حمل', 'ثور', 'جوزا', 'سرطان', 'اسد', 'سنبله', 
                       'میزان', 'عقرب', 'قوس', 'جدی', 'دلو', 'حوت']
        return f"{jalali_date.day} {month_names[jalali_date.month - 1]} {jalali_date.year}"
    except:
        return str(date)

@register.filter
def to_jalali_number(date):
    if not date:
        return ""
    try:
        jalali_date = jdatetime.date.fromgregorian(date=date)
        return jalali_date.strftime('%Y/%m/%d')
    except:
        return str(date)