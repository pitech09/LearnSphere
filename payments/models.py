from django.db import models
from django.conf import settings


class Invoice(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total = models.FloatField(null=True, blank=True)
    amount = models.FloatField(null=True, blank=True)
    payment_complete = models.BooleanField(default=False)
    invoice_code = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "payment_complete"], name="invoice_user_complete_idx"),
            models.Index(fields=["invoice_code"], name="invoice_code_idx"),
        ]
