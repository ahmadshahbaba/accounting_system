from django.db import models
from django.contrib.auth.models import User
from customers.models import Customer
from suppliers.models import Supplier
from misc_persons.models import MiscPerson

class FinancialTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('IN', 'واریز (جمع به حساب)'),
        ('OUT', 'برداشت از حساب'),
    ]
    PERSON_TYPES = [
        ('CUSTOMER', 'مشتری'),
        ('SUPPLIER', 'تهیه‌کننده'),
        ('MISC', 'متفرقه'),
    ]
    transaction_date = models.DateField(verbose_name="تاریخ تراکنش")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="مبلغ")
    transaction_type = models.CharField(max_length=3, choices=TRANSACTION_TYPES, verbose_name="نوع تراکنش")
    person_type = models.CharField(max_length=10, choices=PERSON_TYPES, verbose_name="نوع شخص")
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="مشتری")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="تهیه‌کننده")
    misc_person = models.ForeignKey(MiscPerson, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="شخص متفرقه")
    description = models.CharField(max_length=255, blank=True, verbose_name="توضیحات")
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت در سیستم")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="ثبت کننده")

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} - {self.get_person_name()}"

    def get_person_name(self):
        if self.person_type == 'CUSTOMER' and self.customer:
            return self.customer.name
        elif self.person_type == 'SUPPLIER' and self.supplier:
            return self.supplier.name
        elif self.person_type == 'MISC' and self.misc_person:
            return self.misc_person.name
        return "نامشخص"

    class Meta:
        verbose_name = "تراکنش مالی"
        verbose_name_plural = "تراکنش‌های مالی"
        ordering = ['-transaction_date']