from django.db import models
from suppliers.models import Supplier
from inventory.models import Product
from settings_app.models import Currency

class PurchaseInvoice(models.Model):
    PAYMENT_METHODS = [('CASH', 'نقد'), ('CREDIT', 'قرض')]
    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    date = models.DateField()
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, default=1, verbose_name="واحد پول")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default='CASH')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last = PurchaseInvoice.objects.all().order_by('id').last()
            if last and last.invoice_number.isdigit():
                next_num = int(last.invoice_number) + 1
            else:
                next_num = 2001
            self.invoice_number = str(next_num)
        self.remaining_amount = self.total_amount - self.paid_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"خرید {self.invoice_number}"

class PurchaseItem(models.Model):
    invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)