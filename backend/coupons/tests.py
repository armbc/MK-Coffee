"""优惠券模块 · 测试"""
from datetime import timedelta
from django.core.management import call_command
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

    def test_value_text_display(self):
        """折扣显示：9→9折、88→8.8折、85→8.5折；满减显示 ¥X"""
        now = timezone.now()
        cases = [
            ("满100减20", "full_reduce", 20, "¥20"),
            ("新人券", "discount", 9, "9折"),
            ("复购折扣券", "discount", 88, "8.8折"),
            ("85折券", "discount", 85, "8.5折"),
        ]
        for name, ctype, value, expected in cases:
            c = Coupon.objects.create(
                name=name, type=ctype, value=value,
                min_amount=0, stock=1,
                start_date=now, end_date=now + timedelta(days=1),
            )
            self.assertEqual(c.value_text, expected, f"{name} 应显示 {expected}")


class SeedCouponsCommandTest(TestCase):
    """seed_coupons：重建 5 张运营券模板（与 COUPONS.md 台账一致）"""

    def test_seed_creates_five_templates(self):
        call_command("seed_coupons")
        self.assertEqual(Coupon.objects.count(), 5)

        # 新人券：折扣 9 折、无门槛
        newbie = Coupon.objects.get(name="新人券")
        self.assertEqual(newbie.type, "discount")
        self.assertEqual(newbie.value, 9)
        self.assertEqual(newbie.min_amount, 0)
        self.assertEqual(newbie.stock, 200)
        self.assertEqual(newbie.status, "active")

        # 满减券：减 15、门槛 100
        bean = Coupon.objects.get(name="咖啡豆满减券")
        self.assertEqual(bean.type, "full_reduce")
        self.assertEqual(bean.value, 15)
        self.assertEqual(bean.min_amount, 100)
        self.assertEqual(bean.stock, 300)

        # 复购折扣券：8.8 折、满 80
        repurchase = Coupon.objects.get(name="复购折扣券")
        self.assertEqual(repurchase.type, "discount")
        self.assertEqual(repurchase.value, 88)
        self.assertEqual(repurchase.min_amount, 80)

    def test_seed_idempotent(self):
        """重复执行不重复创建"""
        call_command("seed_coupons")
        call_command("seed_coupons")
        self.assertEqual(Coupon.objects.count(), 5)

    def test_seed_updates_existing_template(self):
        """已存在的同名券按台账参数更新（对齐有效期/库存/状态）"""
        now = timezone.now()
        Coupon.objects.create(
            name="新人券", type="full_reduce", value=5,
            min_amount=50, stock=10,
            start_date=now, end_date=now + timedelta(days=3),
            status="inactive",
        )
        call_command("seed_coupons")
        newbie = Coupon.objects.get(name="新人券")
        self.assertEqual(Coupon.objects.filter(name="新人券").count(), 1)
        self.assertEqual(newbie.type, "discount")
        self.assertEqual(newbie.value, 9)
        self.assertEqual(newbie.min_amount, 0)
        self.assertEqual(newbie.stock, 200)
        self.assertEqual(newbie.status, "active")
