from django import forms

class ManualPaymentForm(forms.Form):
    payment_method = forms.ChoiceField(
        choices=[('bank', 'Bank Transfer'), ('mpesa', 'M-Pesa'), ('ecocash', 'EcoCash')],
        widget=forms.RadioSelect,
        label="Select Payment Method"
    )
    proof_of_payment = forms.FileField(
        label="Upload Proof (screenshot, receipt, or transaction reference)",
        help_text="Upload an image or PDF of your payment confirmation."
    )