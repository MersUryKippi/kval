from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Record(models.Model):
    name = models.CharField("Название", max_length=160)
    code = models.CharField("Код", max_length=50, unique=True)
    price = models.DecimalField(
        "Сумма",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    active = models.BooleanField("Активно", default=True)
    on_date = models.DateField("Дата", null=True, blank=True)
    created = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        db_table = "record"
        verbose_name = "Запись"
        verbose_name_plural = "Записи"
        ordering = ("-created",)

    def __str__(self):
        return self.name

    def clean(self):
        normalized = (self.name or "").strip()
        if not normalized:
            raise ValidationError({"name": "Название обязательно."})
        self.name = normalized
        if self.price is not None and self.price <= 0:
            raise ValidationError({"price": "Сумма должна быть больше 0."})
