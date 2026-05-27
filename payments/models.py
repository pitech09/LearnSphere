from django.db import models
from django.conf import settings

class Invoice(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('bank', 'Bank Transfer'),
        ('mpesa', 'M-Pesa'),
        ('ecocash', 'EcoCash'),
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total = models.FloatField(null=True, blank=True)
    amount = models.FloatField(null=True, blank=True)
    payment_complete = models.BooleanField(default=False)
    invoice_code = models.CharField(max_length=200, blank=True, null=True)
    
    # New fields for manual payment
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    proof_of_payment = models.FileField(upload_to='proofs/', blank=True, null=True)
    payment_verified = models.BooleanField(default=False)
    verification_notes = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "payment_complete"], name="invoice_user_complete_idx"),
            models.Index(fields=["invoice_code"], name="invoice_code_idx"),
            models.Index(fields=["payment_verified"], name="invoice_verified_idx"),
        ]

    def __str__(self):
        return f"Invoice {self.invoice_code or self.id} - {self.user.username}"