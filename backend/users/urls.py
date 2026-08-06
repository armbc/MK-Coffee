"""用户模块 · 路由"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AuthViewSet, UserViewSet, AddressViewSet

router = DefaultRouter()
router.register("auth", AuthViewSet, basename="auth")
router.register("user", UserViewSet, basename="user")
router.register("addresses", AddressViewSet, basename="address")

urlpatterns = [
    path("", include(router.urls)),
]
