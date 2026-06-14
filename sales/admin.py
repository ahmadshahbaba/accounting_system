from django.contrib import admin
from .models import Sale, SaleItem

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'date', 'customer_name', 'total_amount', 'paid_amount', 'debt_display')
    inlines = [SaleItemInline]
    
    def debt_display(self, obj):
        """نمایش بدهی در ادمین"""
        return obj.debt
    debt_display.short_description = 'بدهی'