from django.db import models
from settings_app.models import Currency

class MiscPerson(models.Model):
    name = models.CharField(max_length=200, verbose_name="نام شخص")
    phone = models.CharField(max_length=20, blank=True, verbose_name="شماره تماس")
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, verbose_name="واحد پول")
    address = models.TextField(blank=True, verbose_name="آدرس")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "شخص متفرقه"
        verbose_name_plural = "اشخاص متفرقه"