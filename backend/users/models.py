"""用户模型"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    """用户管理器：以 openid 为唯一标识，支持创建管理员账号"""

    def create_user(self, openid, password=None, **extra_fields):
        if not openid:
            raise ValueError("openid 必填")
        user = self.model(openid=openid, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, openid, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("超级用户必须 is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("超级用户必须 is_superuser=True")
        return self.create_user(openid, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """小程序用户，以 openid 为唯一标识；同时是 Django admin 的登录账号"""

    openid = models.CharField(max_length=64, unique=True, verbose_name="微信 openid / 后台登录名")
    nickname = models.CharField(max_length=64, blank=True, default="", verbose_name="昵称")
    avatar = models.URLField(max_length=512, blank=True, default="", verbose_name="头像")
    phone = models.CharField(max_length=20, blank=True, default="", verbose_name="手机号")
    is_staff = models.BooleanField(default=False, verbose_name="可登录后台")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    objects = UserManager()

    USERNAME_FIELD = "openid"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        verbose_name = "用户"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return self.nickname or self.openid[:12]


class Address(models.Model):
    """收货地址"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="addresses", verbose_name="用户",
    )
    name = models.CharField(max_length=32, verbose_name="收货人")
    phone = models.CharField(max_length=20, verbose_name="手机号")
    province = models.CharField(max_length=32, verbose_name="省")
    city = models.CharField(max_length=32, verbose_name="市")
    district = models.CharField(max_length=32, verbose_name="区")
    detail = models.CharField(max_length=255, verbose_name="详细地址")
    is_default = models.BooleanField(default=False, verbose_name="默认地址")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "addresses"
        verbose_name = "收货地址"
        verbose_name_plural = verbose_name
        ordering = ["-is_default", "-created_at"]

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        if not Address.objects.filter(user=self.user).exists():
            self.is_default = True
        super().save(*args, **kwargs)
