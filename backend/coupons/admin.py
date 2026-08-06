"""优惠券模块 · Admin"""
from django.contrib import admin
from .models import Coupon, UserCoupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ["name", "type", "value", "min_amount", "stock", "status", "start_date", "end_date"]
    list_filter = ["type", "status"]
    search_fields = ["name"]


@admin.register(UserCoupon)
class UserCouponAdmin(admin.ModelAdmin):
    list_display = ["user", "coupon", "status", "used_at", "created_at"]
    list_filter = ["status"]
    search_fields = ["user__nickname", "coupon__name"]
