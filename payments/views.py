import stripe
import uuid
import json
import logging

from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.shortcuts import redirect
from django.views.generic.base import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.http import JsonResponse

import gopay
from gopay.enums import Recurrence, PaymentInstrument, BankSwiftCode, Currency, Language
from .models import Invoice

logger = logging.getLogger(__name__)


@login_required
def payment_paypal(request):
    return render(request, "payments/paypal.html", context={})


@login_required
def payment_stripe(request):
    return render(request, "payments/stripe.html", context={})


@login_required
def payment_coinbase(request):
    return render(request, "payments/coinbase.html", context={})


@login_required
def payment_paylike(request):
    return render(request, "payments/paylike.html", context={})


@login_required
def payment_succeed(request):
    return render(request, "payments/payment_succeed.html", context={})


@method_decorator(login_required, name="dispatch")
class PaymentGetwaysView(TemplateView):
    template_name = "payments/payment_gateways.html"

    def get_context_data(self, **kwargs):
        context = super(PaymentGetwaysView, self).get_context_data(**kwargs)
        context["key"] = settings.STRIPE_PUBLISHABLE_KEY
        context["amount"] = 500
        context["description"] = "Stripe Payment"
        context["invoice_session"] = self.request.session["invoice_session"]
        return context


@login_required
def stripe_charge(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    if request.method == "POST":
        charge = stripe.Charge.create(
            amount=500,
            currency="eur",
            description="A Django charge",
            source=request.POST["stripeToken"],
        )
        invoice_code = request.session["invoice_session"]
        invoice = Invoice.objects.get(invoice_code=invoice_code, user=request.user)
        invoice.payment_complete = True
        invoice.save()
        return redirect("completed")
        # return JsonResponse({"invoice_code": invoice.invoice_code}, status=201)
        # return render(request, 'payments/charge.html')


@login_required
def gopay_charge(request):
    if request.method == "POST":
        user = request.user

        payments = gopay.payments(
            {
                "goid": "[PAYMENT_ID]",
                "clientId": "[GOPAY_CLIENT_ID]",
                "clientSecret": "[GOPAY_CLIENT_SECRET]",
                "isProductionMode": False,
                "scope": gopay.TokenScope.ALL,
                "language": gopay.Language.ENGLISH,
                "timeout": 30,
            }
        )

        # recurrent payment must have field ''
        recurrentPayment = {
            "recurrence": {
                "recurrence_cycle": Recurrence.DAILY,
                "recurrence_period": "7",
                "recurrence_date_to": "2015-12-31",
            }
        }

        # pre-authorized payment must have field 'preauthorization'
        preauthorizedPayment = {"preauthorization": True}

        response = payments.create_payment(
            {
                "payer": {
                    "default_payment_instrument": PaymentInstrument.BANK_ACCOUNT,
                    "allowed_payment_instruments": [PaymentInstrument.BANK_ACCOUNT],
                    "default_swift": BankSwiftCode.FIO_BANKA,
                    "allowed_swifts": [BankSwiftCode.FIO_BANKA, BankSwiftCode.MBANK],
                    "contact": {
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "phone_number": user.phone,
                        "city": "example city",
                        "street": "Plana 67",
                        "postal_code": "373 01",
                        "country_code": "CZE",
                    },
                },
                "amount": 150,
                "currency": Currency.CZECH_CROWNS,
                "order_number": "001",
                "order_description": "pojisteni01",
                "items": [
                    {"name": "item01", "amount": 50},
                    {"name": "item02", "amount": 100},
                ],
                "additional_params": [{"name": "invoicenumber", "value": "2015001003"}],
                "callback": {
                    "return_url": "http://www.your-url.tld/return",
                    "notification_url": "http://www.your-url.tld/notify",
                },
                "lang": Language.CZECH,  # if lang is not specified, then default lang is used
            }
        )

        if response.has_succeed():
            logger.info("GoPay payment succeeded for user_id=%s", user.id)
        else:
            logger.warning("GoPay payment failed for user_id=%s status=%s", user.id, response.status_code)
        return JsonResponse({"message": str(response)})

    return JsonResponse({"message": "GET requested"})


@login_required
def paymentComplete(request):
    if request.method == "POST":
        invoice_id = request.session["invoice_session"]
        invoice = Invoice.objects.get(id=invoice_id, user=request.user)
        invoice.payment_complete = True
        invoice.save()
    if request.body:
        json.loads(request.body)
    return JsonResponse("Payment completed!", safe=False)


@login_required
def create_invoice(request):
    if request.method == "POST":
        invoice = Invoice.objects.create(
            user=request.user,
            amount=request.POST.get("amount"),
            total=26,
            invoice_code=str(uuid.uuid4()),
        )
        request.session["invoice_session"] = invoice.invoice_code
        return redirect("payment_gateways")
    return render(
        request,
        "invoices.html",
        context={"invoices": Invoice.objects.filter(user=request.user)},
    )


@login_required
def invoice_detail(request, slug):
    return render(
        request,
        "invoice_detail.html",
        context={"invoice": Invoice.objects.get(invoice_code=slug, user=request.user)},
    )
