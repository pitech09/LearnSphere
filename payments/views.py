import uuid
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.contrib import messages

from .models import Invoice
from .models import Invoice
from .form import ManualPaymentForm 

logger = logging.getLogger(__name__)


@login_required
def create_invoice(request):
    from django.conf import settings
    plan_key = request.session.get('selected_plan')
    if not plan_key:
        return redirect('select_plan')
    
    plan = settings.SCHOOL_PLANS.get(plan_key)
    if not plan:
        return redirect('select_plan')
    
    amount = plan['amount']
    
    if request.method == "POST":
        # Create invoice with the plan amount
        invoice = Invoice.objects.create(
            user=request.user,
            amount=amount,
            total=amount,
            invoice_code=str(uuid.uuid4()),
        )
        request.session["invoice_session"] = invoice.invoice_code
        # Clear selected plan from session
        del request.session['selected_plan']
        return redirect("manual_payment_upload")
    
    # For GET, just show confirmation (you could skip this and redirect directly)
    return render(request, 'payments/create_invoice.html', {'plan': plan, 'amount': amount})

@login_required
def select_plan(request):
    """Display available plans and let user choose."""
    from django.conf import settings
    plans = settings.SCHOOL_PLANS
    if request.method == 'POST':
        plan_key = request.POST.get('plan')
        if plan_key in plans:
            # Store selected plan in session and redirect to invoice creation
            request.session['selected_plan'] = plan_key
            return redirect('create_invoice')
        else:
            messages.error(request, "Invalid plan selected.")
    return render(request, 'payments/select_plan.html', {'plans': plans})

@login_required
def manual_payment_upload(request):
    """Display payment details and a form to upload proof of payment."""
    invoice_code = request.session.get("invoice_session")
    if not invoice_code:
        return redirect("create_invoice")
    
    invoice = get_object_or_404(Invoice, invoice_code=invoice_code, user=request.user)
    
    if invoice.payment_verified:
        messages.info(request, "This invoice has already been paid and verified.")
        return redirect("payment_succeed")
    
    if request.method == "POST":
        form = ManualPaymentForm(request.POST, request.FILES)
        if form.is_valid():
            invoice.payment_method = form.cleaned_data["payment_method"]
            invoice.proof_of_payment = form.cleaned_data["proof_of_payment"]
            invoice.save()
            # Clear session so the same invoice is not reused
            del request.session["invoice_session"]
            messages.success(request, "Proof of payment uploaded. We will verify it shortly.")
            return redirect("payment_pending_verification")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ManualPaymentForm()
    
    # Payment details to show
    bank_details = {
        "bank_name": "Example Bank",
        "account_name": "Your School Name",
        "account_number": "1234567890",
        "branch": "Main Branch",
        "swift_code": "EXBKZAJJ",
    }
    mobile_money_details = {
        "mpesa": "68578790",
        "ecocash": "57843443",
    }
    
    return render(request, "payments/manual_payment_upload.html", {
        "form": form,
        "invoice": invoice,
        "bank_details": bank_details,
        "mobile_money_details": mobile_money_details,
    })


@login_required
def payment_pending_verification(request):
    """Confirmation page after proof upload."""
    return render(request, "payments/pending_verification.html")


@login_required
def payment_succeed(request):
    """Page shown when payment is already verified."""
    return render(request, "payments/payment_succeed.html")


@login_required
def invoice_detail(request, invoice_code):
    """Display details of a specific invoice."""
    invoice = get_object_or_404(Invoice, invoice_code=invoice_code, user=request.user)
    return render(request, "payments/invoice_detail.html", {"invoice": invoice})