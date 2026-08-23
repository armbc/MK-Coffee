"""用户模块 · 视图"""
import logging
import uuid

import requests
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Address
from .serializers import UserSerializer, WxLoginSerializer, AddressSerializer

logger = logging.getLogger(__name__)

WX_SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"


class AuthViewSet(viewsets.GenericViewSet):
    """认证接口：微信登录"""
    permission_classes = [AllowAny]
    serializer_class = WxLoginSerializer

    @action(detail=False, methods=["post"], url_path="wx-login")
    def wx_login(self, request):
        """微信登录：code → openid → JWT token"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data["code"]
        nickname = serializer.validated_data.get("nickname", "")
        avatar = serializer.validated_data.get("avatar", "")

        # 调用微信 jscode2session
        resp = requests.get(WX_SESSION_URL, params={
            "appid": settings.WX_APP_ID,
            "secret": settings.WX_APP_SECRET,
            "js_code": code,
            "grant_type": "authorization_code",
        }, timeout=10)
        wx_data = resp.json()

        if "errcode" in wx_data and wx_data["errcode"] != 0:
            logger.warning("wx jscode2session failed: %s", wx_data)
            return Response(
                {"code": 400, "data": None, "msg": f"微信登录失败: {wx_data.get('errmsg', '')}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        openid = wx_data["openid"]
        session_key = wx_data.get("session_key", "")

        # 查找或创建用户
        user, created = User.objects.get_or_create(
            openid=openid,
            defaults={"nickname": nickname, "avatar": avatar},
        )

        if not created:
            # 已存在用户，更新昵称和头像
            updated = False
            if nickname and user.nickname != nickname:
                user.nickname = nickname
                updated = True
            if avatar and user.avatar != avatar:
                user.avatar = avatar
                updated = True
            if updated:
                user.save(update_fields=["nickname", "avatar"])

        # 生成 JWT
        refresh = RefreshToken.for_user(user)

        return Response({
            "code": 0,
            "data": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
                "is_new": created,
            },
            "msg": "ok",
        })


class UserViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """用户信息接口（需登录）"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    def get_object(self):
        return self.request.user

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """当前用户信息（GET /api/user/me/）"""
        return Response({
            "code": 0,
            "data": UserSerializer(request.user).data,
            "msg": "ok",
        })

    @action(detail=False, methods=["post"], url_path="me/update")
    def update_profile(self, request):
        """更新昵称（POST /api/user/me/update/）"""
        nickname = (request.data.get("nickname") or "").strip()
        if not nickname:
            return Response(
                {"code": 400, "data": None, "msg": "昵称不能为空"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = request.user
        user.nickname = nickname[:64]
        user.save(update_fields=["nickname"])
        return Response({
            "code": 0,
            "data": UserSerializer(user).data,
            "msg": "ok",
        })

    @action(detail=False, methods=["post"], url_path="me/avatar")
    def upload_avatar(self, request):
        """上传头像（POST /api/user/me/avatar/）"""
        file = request.FILES.get("avatar")
        if not file:
            return Response(
                {"code": 400, "data": None, "msg": "缺少头像文件"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # 校验类型（微信 chooseAvatar 产出 jpg/png/webp）
        allowed = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
        ext = allowed.get(file.content_type)
        if not ext:
            return Response(
                {"code": 400, "data": None, "msg": "仅支持 JPG/PNG/WebP 图片"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # 大小限制 2MB
        if file.size > 2 * 1024 * 1024:
            return Response(
                {"code": 400, "data": None, "msg": "头像不能超过 2MB"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        filename = f"avatars/{uuid.uuid4().hex}{ext}"
        saved = default_storage.save(filename, file)
        avatar_url = request.build_absolute_uri(f"{settings.MEDIA_URL}{saved}")
        user = request.user
        user.avatar = avatar_url
        user.save(update_fields=["avatar"])
        return Response({
            "code": 0,
            "data": {"avatar": avatar_url},
            "msg": "头像已更新",
        })


class AddressViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """收货地址 CRUD（需登录，用户仅操作自己的）"""
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_object(self):
        return get_object_or_404(
            Address, id=self.kwargs["pk"], user=self.request.user,
        )

    @action(detail=True, methods=["post"], url_path="update")
    def update_address(self, request, pk=None):
        """修改地址（POST 版本，兼容微信小程序）"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "code": 0, "data": serializer.data, "msg": "ok",
        })

    @action(detail=True, methods=["post"], url_path="remove")
    def remove_address(self, request, pk=None):
        """删除地址（POST 版本，兼容微信小程序）"""
        instance = self.get_object()
        instance.delete()
        return Response({
            "code": 0, "data": None, "msg": "已删除",
        })

    @action(detail=True, methods=["post"], url_path="set-default")
    def set_default(self, request, pk=None):
        address = self.get_object()
        address.is_default = True
        address.save()
        return Response({
            "code": 0,
            "data": AddressSerializer(address).data,
            "msg": "已设为默认地址",
        })
