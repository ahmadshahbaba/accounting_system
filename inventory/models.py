from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from settings_app.models import UnitOfMeasure, Currency

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="نام جنس")
    code = models.PositiveIntegerField(unique=True, verbose_name="کد جنس")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, verbose_name="واحد پول")
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, verbose_name="واحد اندازه گیری")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

class Stock(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='stock')
    quantity = models.PositiveIntegerField(default=0)
    minimum_threshold = models.PositiveIntegerField(default=5)
    def __str__(self): return f"{self.product.name} - {self.quantity}"

class Transaction(models.Model):
    TRANSACTION_TYPES = [('IN', 'ورود'), ('OUT', 'خروج')]
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='transactions')
    transaction_type = models.CharField(max_length=3, choices=TRANSACTION_TYPES)
    quantity = models.PositiveIntegerField()
    price_at_time = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.get_transaction_type_display()} {self.product.name} {self.quantity}"