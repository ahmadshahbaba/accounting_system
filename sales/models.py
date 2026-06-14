from django.db import models
from inventory.models import Product
from customers.models import Customer
from settings_app.models import Currency

class Sale(models.Model):
    PAYMENT_METHODS = [('CASH', 'نقد'), ('CREDIT', 'قرض')]
    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    date = models.DateTimeField(auto_now_add=True)
    transaction_date = models.DateField(null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    customer_name = models.CharField(max_length=200, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, default=1, verbose_name="واحد پول")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default='CASH')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last = Sale.objects.all().order_by('id').last()
            if last and last.invoice_number.isdigit():
                next_num = int(last.invoice_number) + 1
            else:
                next_num = 1001
            self.invoice_number = str(next_num)
        self.remaining_amount = self.total_amount - self.paid_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"فاکتور {self.invoice_number}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)