"""支付模块 · 路由"""
from django.urls import path

from .views import payment_callback

urlpatterns = [
    path("callback/", payment_callback, name="payment-callback"),
]
