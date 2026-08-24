"""订单模块 · Admin"""
from django.contrib import admin, messages
from .models import CartItem, Order, OrderItem
from .services import ship_order


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
    actions = ["mark_shipped"]

    @admin.action(description="标记为已发货（仅已支付订单）")
    def mark_shipped(self, request, queryset):
        """批量发货：勾选订单 → 下拉选择「标记为已发货」

        仅状态为「已支付」的订单会发货；其余订单跳过并提示原因。
        与 OrderViewSet.ship API 共用 ship_order 业务逻辑。
        """
        shipped = 0
        skipped = []
        for order in queryset:
            _, err = ship_order(order)
            if err:
                skipped.append(f"{order.order_no}（{err}）")
            else:
                shipped += 1
        if shipped:
            self.message_user(request, f"已发货 {shipped} 单", messages.SUCCESS)
        if skipped:
            self.message_user(request, "跳过：" + "；".join(skipped), messages.WARNING)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ["user", "product", "spec", "quantity", "created_at"]
    search_fields = ["user__nickname", "product__name"]
