from django.contrib import admin

from users.models import User, Address


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["id", "openid", "nickname", "phone", "created_at"]
    search_fields = ["openid", "nickname", "phone"]
    list_filter = ["created_at"]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "name", "phone", "province", "city", "is_default"]
    search_fields = ["name", "phone", "detail"]
