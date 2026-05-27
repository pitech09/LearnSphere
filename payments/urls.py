from django.urls import path
from . import views

urlpatterns = [
    path('', views.select_plan, name='select_plan'),                 # default page shows plans
    path('create-invoice/', views.create_invoice, name='create_invoice'),
    path('manual-payment/', views.manual_payment_upload, name='manual_payment_upload'),
    path('pending-verification/', views.payment_pending_verification, name='payment_pending_verification'),
    path('success/', views.payment_succeed, name='payment_succeed'),
    path('invoice/<str:invoice_code>/', views.invoice_detail, name='invoice_detail'),
]