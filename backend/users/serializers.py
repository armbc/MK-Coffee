"""用户模块 · 序列化器"""
import re
from rest_framework import serializers
from .models import User, Address


class WxLoginSerializer(serializers.Serializer):
    """微信登录请求"""
    code = serializers.CharField(required=True, max_length=128, help_text="wx.login 返回的 code")
    nickname = serializers.CharField(required=False, allow_blank=True, max_length=64)
    avatar = serializers.URLField(required=False, allow_blank=True)


class UserSerializer(serializers.ModelSerializer):
    """用户信息"""

    class Meta:
        model = User
        fields = ["id", "nickname", "avatar", "phone", "created_at"]
        read_only_fields = ["id", "created_at"]


class AddressSerializer(serializers.ModelSerializer):
    """收货地址"""

    def validate_phone(self, value):
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError("请输入正确的手机号码")
        return value

    class Meta:
        model = Address
        fields = [
            "id", "name", "phone",
            "province", "city", "district", "detail",
            "is_default", "created_at",
        ]
        read_only_fields = ["id", "created_at"]
