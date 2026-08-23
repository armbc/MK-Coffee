"""用户模块 · Admin"""
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError

from users.models import User, Address


class UserCreationForm(forms.ModelForm):
    """创建用户表单（openid 为登录名 + 密码）"""
    password1 = forms.CharField(label="密码", widget=forms.PasswordInput)
    password2 = forms.CharField(label="确认密码", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("openid",)

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise ValidationError("两次密码不一致")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """修改用户表单：密码以只读 hash 展示，改密码走「重置密码」流程"""
    password = ReadOnlyPasswordHashField(
        label="密码",
        help_text="原始密码不存储，仅显示 hash。要改密码请用下方「管理员密码重置」表单。",
    )

    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ["id", "openid", "nickname", "phone", "is_staff", "is_superuser", "created_at"]
    search_fields = ["openid", "nickname", "phone"]
    list_filter = ["is_staff", "is_superuser", "created_at"]
    ordering = ["-created_at"]

    fieldsets = (
        (None, {"fields": ("openid", "password")}),
        ("个人信息", {"fields": ("nickname", "avatar", "phone")}),
        ("权限", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("时间", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    readonly_fields = ["created_at", "updated_at", "last_login"]
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("openid", "password1", "password2"),
        }),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "name", "phone", "province", "city", "is_default"]
    search_fields = ["name", "phone", "detail"]
