from typing import ClassVar

from django.db import models


class Item(models.Model):
    name = models.CharField(max_length=80)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering: ClassVar = ["id"]
        constraints: ClassVar = [
            models.CheckConstraint(condition=models.Q(quantity__gte=1, quantity__lte=1000), name="item_quantity_1_1000"),
        ]
