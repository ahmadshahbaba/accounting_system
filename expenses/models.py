from django.db import models
from django.contrib.auth.models import User

class GeneralExpense(models.Model):
    EXPENSE_TYPES = [
        ('rent', 'کرایه دوکان'),
        ('electricity', 'بل برق'),
        ('daily', 'مصارف روزانه'),
        ('personal', 'مصارف شخصی'),
    ]
    CURRENCY_CHOICES = [
        ('AFN', 'افغانی'),
        ('USD', 'دالر'),
    ]
    date = models.DateField(verbose_name="تاریخ")
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPES, verbose_name="نوع مصرف")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='AFN', verbose_name="واحد پول")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="مبلغ")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="ثبت کننده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")

    def __str__(self):
        return f"{self.get_expense_type_display()} - {self.amount} {self.get_currency_display()}"

    class Meta:
        verbose_name = "مصرف مالی"
        verbose_name_plural = "مصارف مالی"
        ordering = ['-date']