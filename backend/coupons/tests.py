"""优惠券模块 · 测试"""
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from .models import Coupon, UserCoupon


class CouponTestCase(TestCase):
    """优惠券领取测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(openid="test_coupon_user", nickname="优惠券用户")
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        now = timezone.now()
        self.active_coupon = Coupon.objects.create(
            name="满100减20", type="full_reduce", value=20,
            min_amount=100, stock=100,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=7),
            status="active",
        )
        self.expired_coupon = Coupon.objects.create(
            name="已过期优惠券", type="full_reduce", value=10,
            min_amount=50, stock=50,
            start_date=now - timedelta(days=30),
            end_date=now - timedelta(days=1),
            status="active",
        )
        self.sold_out_coupon = Coupon.objects.create(
            name="库存为0优惠券", type="discount", value=85,
            min_amount=0, stock=0,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=7),
            status="active",
        )

    def test_coupon_list(self):
        resp = self.client.get("/api/coupons/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["code"], 0)
        self.assertEqual(len(data["data"]["results"]), 3)

    def test_claim_coupon_success(self):
        resp = self.client.post(f"/api/coupons/{self.active_coupon.id}/claim/")
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["msg"], "领取成功")
        self.assertTrue(UserCoupon.objects.filter(user=self.user, coupon=self.active_coupon).exists())

    def test_claim_coupon_duplicate(self):
        self.client.post(f"/api/coupons/{self.active_coupon.id}/claim/")
        resp = self.client.post(f"/api/coupons/{self.active_coupon.id}/claim/")
        data = resp.json()
        self.assertEqual(resp.status_code, 400)
        self.assertIn("已领取", data["msg"])

    def test_claim_expired_coupon(self):
        resp = self.client.post(f"/api/coupons/{self.expired_coupon.id}/claim/")
        data = resp.json()
        self.assertEqual(resp.status_code, 400)
        self.assertIn("过期", data["msg"])

    def test_claim_sold_out_coupon(self):
        """stock=0 表示不限量，仍可领取"""
        resp = self.client.post(f"/api/coupons/{self.sold_out_coupon.id}/claim/")
        self.assertEqual(resp.status_code, 201)

    def test_my_coupons_list(self):
        self.client.post(f"/api/coupons/{self.active_coupon.id}/claim/")
        resp = self.client.get("/api/my-coupons/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        results = data["data"]["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["coupon_name"], "满100减20")

    def test_claim_unauthorized(self):
        unauth = APIClient()
        resp = unauth.post(f"/api/coupons/{self.active_coupon.id}/claim/")
        self.assertEqual(resp.status_code, 401)
