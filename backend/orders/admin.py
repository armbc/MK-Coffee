"""订单模块 · Admin"""
from django.contrib import admin
from .models import CartItem, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ["product_name", "spec_name", "price", "quantity"]
    extra = 0
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_no", "user", "total", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["order_no", "user__nickname"]
    readonly_fields = ["order_no", "created_at", "updated_at"]
    inlines = [OrderItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ["user", "product", "spec", "quantity", "created_at"]
    search_fields = ["user__nickname", "product__name"]
