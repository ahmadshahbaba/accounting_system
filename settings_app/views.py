from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Permission
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import PermissionDenied
from django.db import transaction
from .models import ShopInfo, UnitOfMeasure, Currency

# ==================== تعریف بخش‌ها و مجوزها برای مدیران ====================
SECTIONS = {
    'اجناس': {'app_label': 'inventory', 'models': ['product', 'stock', 'category', 'transaction']},
    'مشتریان': {'app_label': 'customers', 'models': ['customer']},
    'فروشات': {'app_label': 'sales', 'models': ['sale', 'saleitem']},
    'خریداری': {'app_label': 'purchases', 'models': ['purchaseinvoice', 'purchaseitem']},
    'تهیه‌کنندگان': {'app_label': 'suppliers', 'models': ['supplier']},
    'اشخاص متفرقه': {'app_label': 'misc_persons', 'models': ['miscperson']},
    'تراکنش': {'app_label': 'transactions', 'models': ['financialtransaction']},
    'مصارف': {'app_label': 'expenses', 'models': ['generalexpense']},
}

def get_all_permissions_for_section(section_key):
    section = SECTIONS[section_key]
    app_label = section['app_label']
    perms = []
    for model_name in section['models']:
        for action in ['view', 'add', 'change', 'delete']:
            codename = f'{action}_{model_name}'
            try:
                perm = Permission.objects.get(content_type__app_label=app_label, codename=codename)
                perms.append(perm)
            except Permission.DoesNotExist:
                continue
    return perms

# ==================== معلومات عمومی ====================
@login_required
def general_info(request):
    shop_info, created = ShopInfo.objects.get_or_create(pk=1)
    password_form = PasswordChangeForm(request.user)

    if request.method == 'POST':
        if 'update_shop_info' in request.POST:
            shop_info.shop_name = request.POST.get('shop_name')
            shop_info.address = request.POST.get('address')
            shop_info.phone = request.POST.get('phone')
            shop_info.whatsapp = request.POST.get('whatsapp')  # ← اضافه شد
            shop_info.email = request.POST.get('email')
            shop_info.footer_text = request.POST.get('footer_text')
            shop_info.save()
            messages.success(request, 'اطلاعات فروشگاه با موفقیت به‌روز شد.')

        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'رمز عبور با موفقیت تغییر کرد.')
            else:
                messages.error(request, 'خطا در تغییر رمز عبور.')

        elif 'change_username' in request.POST:
            new_username = request.POST.get('new_username')
            if User.objects.exclude(pk=request.user.pk).filter(username=new_username).exists():
                messages.error(request, 'این نام کاربری قبلاً ثبت شده است.')
            else:
                request.user.username = new_username
                request.user.save()
                messages.success(request, 'نام کاربری تغییر کرد.')

        return redirect('settings_app:general_info')

    return render(request, 'settings_app/general_info.html', {
        'shop_info': shop_info,
        'user': request.user,
        'password_form': password_form,
    })

# ==================== مدیریت واحدها ====================
@login_required
def units_list(request):
    units = UnitOfMeasure.objects.all()
    currencies = Currency.objects.all()
    return render(request, 'settings_app/units_list.html', {'units': units, 'currencies': currencies})

@login_required
def unit_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        symbol = request.POST.get('symbol')
        UnitOfMeasure.objects.create(name=name, symbol=symbol)
        messages.success(request, 'واحد اندازه‌گیری اضافه شد.')
        return redirect('settings_app:units_list')
    return redirect('settings_app:units_list')

@login_required
def unit_edit(request, pk):
    unit = get_object_or_404(UnitOfMeasure, pk=pk)
    if request.method == 'POST':
        unit.name = request.POST.get('name')
        unit.symbol = request.POST.get('symbol')
        unit.save()
        messages.success(request, 'واحد ویرایش شد.')
    return redirect('settings_app:units_list')

@login_required
def unit_delete(request, pk):
    unit = get_object_or_404(UnitOfMeasure, pk=pk)
    unit.delete()
    messages.success(request, 'واحد حذف شد.')
    return redirect('settings_app:units_list')

@login_required
def currency_add(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        name = request.POST.get('name')
        symbol = request.POST.get('symbol')
        Currency.objects.create(code=code, name=name, symbol=symbol)
        messages.success(request, 'واحد پول اضافه شد.')
    return redirect('settings_app:units_list')

@login_required
def currency_edit(request, pk):
    currency = get_object_or_404(Currency, pk=pk)
    if request.method == 'POST':
        currency.code = request.POST.get('code')
        currency.name = request.POST.get('name')
        currency.symbol = request.POST.get('symbol')
        currency.save()
        messages.success(request, 'واحد پول ویرایش شد.')
    return redirect('settings_app:units_list')

@login_required
def currency_delete(request, pk):
    currency = get_object_or_404(Currency, pk=pk)
    currency.delete()
    messages.success(request, 'واحد پول حذف شد.')
    return redirect('settings_app:units_list')

# ==================== مدیریت مدیران ====================
@login_required
def managers_list(request):
    if not request.user.is_superuser:
        raise PermissionDenied("شما دسترسی به این بخش ندارید.")
    managers = User.objects.filter(is_staff=True).order_by('-is_superuser', 'username')
    return render(request, 'settings_app/managers_list.html', {'managers': managers})

@login_required
def manager_add(request):
    if not request.user.is_superuser:
        raise PermissionDenied("شما دسترسی به این بخش ندارید.")
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        is_superuser = request.POST.get('is_superuser') == 'on'
        is_staff = True

        if User.objects.filter(username=username).exists():
            messages.error(request, 'این نام کاربری قبلاً ثبت شده است.')
            return redirect('settings_app:manager_add')

        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_staff=is_staff,
                is_superuser=is_superuser
            )
            if not is_superuser:
                for section_key in SECTIONS.keys():
                    if request.POST.get(f'perm_{section_key}'):
                        perms = get_all_permissions_for_section(section_key)
                        user.user_permissions.add(*perms)
        messages.success(request, f'مدیر {username} اضافه شد.')
        return redirect('settings_app:managers_list')
    return render(request, 'settings_app/manager_form.html', {'sections': SECTIONS})

@login_required
def manager_edit(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied("شما دسترسی به این بخش ندارید.")
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        is_superuser = request.POST.get('is_superuser') == 'on'
        user.is_superuser = is_superuser
        password = request.POST.get('password')
        if password:
            user.set_password(password)
        user.save()

        if not is_superuser:
            all_perms = []
            for section_key in SECTIONS.keys():
                all_perms.extend(get_all_permissions_for_section(section_key))
            user.user_permissions.remove(*all_perms)
            for section_key in SECTIONS.keys():
                if request.POST.get(f'perm_{section_key}'):
                    perms = get_all_permissions_for_section(section_key)
                    user.user_permissions.add(*perms)
        else:
            all_perms = []
            for section_key in SECTIONS.keys():
                all_perms.extend(get_all_permissions_for_section(section_key))
            user.user_permissions.remove(*all_perms)

        messages.success(request, f'مدیر {user.username} ویرایش شد.')
        return redirect('settings_app:managers_list')

    allowed_sections = []
    if not user.is_superuser:
        for section_key in SECTIONS.keys():
            perms = get_all_permissions_for_section(section_key)
            if user.has_perms([p.codename for p in perms]):
                allowed_sections.append(section_key)

    return render(request, 'settings_app/manager_form.html', {
        'manager': user,
        'sections': SECTIONS,
        'allowed_sections': allowed_sections,
    })

@login_required
def manager_delete(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied("شما دسترسی به این بخش ندارید.")
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'شما نمی‌توانید خودتان را حذف کنید.')
    else:
        user.delete()
        messages.success(request, f'مدیر {user.username} حذف شد.')
    return redirect('settings_app:managers_list')