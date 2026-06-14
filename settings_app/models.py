from django.db import models

class ShopInfo(models.Model):
    shop_name = models.CharField(max_length=200, default="فروشگاه من", verbose_name="نام فروشگاه")
    address = models.TextField(blank=True, verbose_name="آدرس")
    phone = models.CharField(max_length=20, blank=True, verbose_name="شماره تماس")
    email = models.EmailField(blank=True, verbose_name="ایمیل")
    footer_text = models.TextField(blank=True, verbose_name="متن پایانی فاکتور")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True, verbose_name="لوگو")

    def __str__(self):
        return self.shop_name

    class Meta:
        verbose_name = "اطلاعات فروشگاه"
        verbose_name_plural = "اطلاعات فروشگاه"


class UnitOfMeasure(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="نام واحد")
    symbol = models.CharField(max_length=10, blank=True, verbose_name="نماد")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "واحد اندازه‌گیری"
        verbose_name_plural = "واحدهای اندازه‌گیری"


class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True, verbose_name="کد")
    name = models.CharField(max_length=50, verbose_name="نام واحد پول")
    symbol = models.CharField(max_length=5, verbose_name="نماد")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "واحد پول"
        verbose_name_plural = "واحدهای پول"