"""订单模块 · 测试"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from products.models import Category, Product, Spec
from orders.models import CartItem, Order, OrderItem


class CartItemModelTest(TestCase):
    """购物车模型测试"""

    def setUp(self):
        self.user = User.objects.create(openid="cart_test_user")
        self.cat = Category.objects.create(name="咖啡豆")
        self.product = Product.objects.create(
            name="测试商品", category=self.cat, price=88.00, stock=50,
        )
        self.spec = Spec.objects.create(
            product=self.product, name="500g", price=158.00, stock=20,
        )

    def test_create_cart_item(self):
        item = CartItem.objects.create(
            user=self.user, product=self.product, quantity=3,
        )
        self.assertEqual(item.quantity, 3)
        self.assertEqual(item.unit_price, 88.00)
        self.assertEqual(item.subtotal, 264.00)

    def test_cart_item_with_spec(self):
        item = CartItem.objects.create(
            user=self.user, product=self.product, spec=self.spec, quantity=2,
        )
        self.assertEqual(item.unit_price, 158.00)
        self.assertEqual(item.subtotal, 316.00)

    def test_unique_constraint(self):
        """带 spec 时不可重复，不带 spec 时 MySQL 允许多个 NULL"""
        CartItem.objects.create(user=self.user, product=self.product, quantity=1)
        # MySQL InnoDB 的 UNIQUE 约束对 NULL 视为不同值，所以不带 spec 允许重复
        # 验证第二次创建不会抛异常
        item2 = CartItem.objects.create(user=self.user, product=self.product, quantity=5)
        self.assertEqual(item2.quantity, 5)

    def test_unique_constraint_with_spec(self):
        CartItem.objects.create(user=self.user, product=self.product, spec=self.spec, quantity=1)
        with self.assertRaises(Exception):
            CartItem.objects.create(user=self.user, product=self.product, spec=self.spec, quantity=2)

    def test_different_users_can_have_same_product(self):
        user2 = User.objects.create(openid="cart_test_user2")
        CartItem.objects.create(user=self.user, product=self.product, quantity=1)
        # 不同用户可以有同商品，不抛异常
        item2 = CartItem.objects.create(user=user2, product=self.product, quantity=5)
        self.assertEqual(item2.quantity, 5)


class OrderModelTest(TestCase):
    """订单模型测试"""

    def setUp(self):
        self.user = User.objects.create(openid="order_test_user")
        self.cat = Category.objects.create(name="咖啡豆")
        self.product = Product.objects.create(
            name="耶加雪菲", category=self.cat, price=88.00, stock=50,
        )

    def test_create_order(self):
        order = Order.objects.create(user=self.user, total=88.00)
        self.assertEqual(order.status, "pending")
        self.assertEqual(order.total, 88.00)
        self.assertEqual(len(order.order_no), 32)

    def test_order_item_snapshot(self):
        order = Order.objects.create(user=self.user, total=176.00)
        item = OrderItem.objects.create(
            order=order, product=self.product,
            product_name=self.product.name, price=88.00, quantity=2,
        )
        self.assertEqual(item.product_name, "耶加雪菲")
        self.assertEqual(item.subtotal, 176.00)


class CartAPITest(TestCase):
    """购物车 API 测试"""

    def setUp(self):
        self.user = User.objects.create(openid="cart_api_user", nickname="测试")
        self.cat = Category.objects.create(name="袋装咖啡豆")
        self.product = Product.objects.create(
            name="耶加雪菲", category=self.cat, price=88.00, stock=50,
        )
        self.off_product = Product.objects.create(
            name="下架商品", category=self.cat, price=50.00, stock=10, status="off",
        )
        self.spec = Spec.objects.create(
            product=self.product, name="500g", price=158.00, stock=20,
        )

        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        self.list_url = reverse("cart-list")

    # ---- 加入购物车 ----

    def test_add_to_cart(self):
        resp = self.client.post(self.list_url, {
            "product": self.product.id, "quantity": 2,
        }, format="json")
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["data"]["product_name"], "耶加雪菲")
        self.assertEqual(data["data"]["quantity"], 2)
        self.assertEqual(float(data["data"]["unit_price"]), 88.00)

    def test_add_to_cart_with_spec(self):
        resp = self.client.post(self.list_url, {
            "product": self.product.id, "spec": self.spec.id, "quantity": 1,
        }, format="json")
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["data"]["spec_name"], "500g")
        self.assertEqual(float(data["data"]["unit_price"]), 158.00)

    def test_add_duplicate_merges_quantity(self):
        """添加已存在的商品应叠加数量"""
        resp1 = self.client.post(self.list_url, {
            "product": self.product.id, "quantity": 2,
        }, format="json")
        self.assertEqual(resp1.status_code, 201)
        resp2 = self.client.post(self.list_url, {
            "product": self.product.id, "quantity": 3,
        }, format="json")
        self.assertEqual(resp2.status_code, 201)
        self.assertEqual(resp2.json()["data"]["quantity"], 5)

    def test_cannot_add_off_product(self):
        resp = self.client.post(self.list_url, {
            "product": self.off_product.id, "quantity": 1,
        }, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_spec_must_belong_to_product(self):
        other_product = Product.objects.create(
            name="其他商品", category=self.cat, price=10.00, stock=10,
        )
        other_spec = Spec.objects.create(product=other_product, name="test", price=10.00, stock=10)
        resp = self.client.post(self.list_url, {
            "product": self.product.id, "spec": other_spec.id, "quantity": 1,
        }, format="json")
        self.assertEqual(resp.status_code, 400)

    # ---- 购物车列表 ----

    def test_cart_list(self):
        CartItem.objects.create(user=self.user, product=self.product, quantity=2)
        CartItem.objects.create(user=self.user, product=self.product, spec=self.spec, quantity=1)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data["data"]["results"]), 2)

    def test_cart_list_isolation(self):
        """用户只能看到自己的购物车"""
        user2 = User.objects.create(openid="cart_other")
        CartItem.objects.create(user=self.user, product=self.product, quantity=1)
        CartItem.objects.create(user=user2, product=self.product, quantity=5)
        resp = self.client.get(self.list_url)
        self.assertEqual(len(resp.json()["data"]["results"]), 1)

    def test_cart_list_requires_auth(self):
        client = APIClient()
        resp = client.get(self.list_url)
        self.assertEqual(resp.status_code, 401)

    # ---- 修改数量 ----

    def test_update_quantity(self):
        item = CartItem.objects.create(user=self.user, product=self.product, quantity=1)
        url = reverse("cart-detail", args=[item.id])
        resp = self.client.patch(url, {"quantity": 10}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"]["quantity"], 10)

    def test_update_quantity_below_1(self):
        item = CartItem.objects.create(user=self.user, product=self.product, quantity=1)
        url = reverse("cart-detail", args=[item.id])
        resp = self.client.patch(url, {"quantity": 0}, format="json")
        self.assertEqual(resp.status_code, 400)

    # ---- 删除购物车 ----

    def test_delete_cart_item(self):
        item = CartItem.objects.create(user=self.user, product=self.product, quantity=1)
        url = reverse("cart-detail", args=[item.id])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(CartItem.objects.filter(id=item.id).exists())

    def test_cannot_delete_others_cart(self):
        user2 = User.objects.create(openid="cart_other2")
        item = CartItem.objects.create(user=user2, product=self.product, quantity=1)
        url = reverse("cart-detail", args=[item.id])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 404)

    # ---- 清空购物车 ----

    def test_clear_cart(self):
        CartItem.objects.create(user=self.user, product=self.product, quantity=1)
        CartItem.objects.create(user=self.user, product=self.product, spec=self.spec, quantity=2)
        url = reverse("cart-clear")
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"]["deleted"], 2)
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 0)


class OrderAPITest(TestCase):
    """订单 API 测试"""

    def setUp(self):
        self.user = User.objects.create(openid="order_api_user", nickname="订单测试")
        self.cat = Category.objects.create(name="咖啡豆")
        self.product = Product.objects.create(
            name="耶加雪菲", category=self.cat, price=88.00, stock=50,
        )
        self.product2 = Product.objects.create(
            name="曼特宁", category=self.cat, price=75.00, stock=30,
        )
        self.spec = Spec.objects.create(
            product=self.product, name="500g", price=158.00, stock=20,
        )
        self.spec2 = Spec.objects.create(
            product=self.product2, name="1000g", price=150.00, stock=5,
        )

        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        self.order_list_url = reverse("order-list")

    def _fill_cart(self):
        """往购物车添加一些商品，方便测试下单"""
        CartItem.objects.create(user=self.user, product=self.product, quantity=2)
        CartItem.objects.create(user=self.user, product=self.product2, spec=self.spec2, quantity=1)

    # ---- 下单 ----

    def test_create_order_from_cart(self):
        self._fill_cart()
        resp = self.client.post(self.order_list_url, {}, format="json")
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["msg"], "下单成功")
        order_data = data["data"]
        self.assertEqual(order_data["status"], "pending")
        self.assertEqual(len(order_data["items"]), 2)
        # 两位商品：88*2 + 150*1 = 326
        self.assertEqual(float(order_data["total"]), 326.00)

    def test_create_order_clears_cart(self):
        self._fill_cart()
        self.client.post(self.order_list_url, {}, format="json")
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 0)

    def test_create_order_deducts_stock(self):
        self._fill_cart()
        self.client.post(self.order_list_url, {}, format="json")
        self.product.refresh_from_db()
        self.product2.refresh_from_db()
        self.spec2.refresh_from_db()
        self.assertEqual(self.product.stock, 48)   # 50 - 2
        self.assertEqual(self.spec2.stock, 4)       # 5 - 1

    def test_create_order_empty_cart(self):
        resp = self.client.post(self.order_list_url, {}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("购物车为空", resp.json()["msg"])

    def test_create_order_insufficient_stock(self):
        CartItem.objects.create(user=self.user, product=self.product, quantity=100)
        resp = self.client.post(self.order_list_url, {}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("库存不足", resp.json()["msg"])

    def test_create_order_off_product(self):
        self.product.status = "off"
        self.product.save()
        CartItem.objects.create(user=self.user, product=self.product, quantity=1)
        resp = self.client.post(self.order_list_url, {}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("已下架", resp.json()["msg"])

    # ---- 订单列表 ----

    def test_order_list(self):
        self._fill_cart()
        self.client.post(self.order_list_url, {}, format="json")
        resp = self.client.get(self.order_list_url)
        self.assertEqual(resp.status_code, 200)
        results = resp.json()["data"]["results"]
        self.assertEqual(len(results), 1)
        self.assertIn("order_no", results[0])
        self.assertEqual(results[0]["item_count"], 2)

    def test_order_list_isolation(self):
        user2 = User.objects.create(openid="order_other")
        CartItem.objects.create(user=user2, product=self.product, quantity=1)
        # 用 user2 下单
        client2 = APIClient()
        refresh2 = RefreshToken.for_user(user2)
        client2.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh2.access_token}")
        client2.post(reverse("order-list"), {}, format="json")

        # user1 看不到 user2 的订单
        resp = self.client.get(self.order_list_url)
        self.assertEqual(len(resp.json()["data"]["results"]), 0)

    # ---- 订单详情 ----

    def test_order_detail(self):
        self._fill_cart()
        create_resp = self.client.post(self.order_list_url, {}, format="json")
        order_id = create_resp.json()["data"]["id"]
        url = reverse("order-detail", args=[order_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(len(data["items"]), 2)
        # 验证快照字段
        item_names = {i["product_name"] for i in data["items"]}
        self.assertIn("耶加雪菲", item_names)
        self.assertIn("曼特宁", item_names)

    # ---- 取消订单 ----

    def test_cancel_order(self):
        self._fill_cart()
        create_resp = self.client.post(self.order_list_url, {}, format="json")
        order_id = create_resp.json()["data"]["id"]
        url = reverse("order-cancel", args=[order_id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"]["status"], "cancelled")

    def test_cancel_restores_stock(self):
        self._fill_cart()
        create_resp = self.client.post(self.order_list_url, {}, format="json")
        order_id = create_resp.json()["data"]["id"]
        self.client.post(reverse("order-cancel", args=[order_id]))
        self.product.refresh_from_db()
        self.spec2.refresh_from_db()
        self.assertEqual(self.product.stock, 50)    # 原样恢复
        self.assertEqual(self.spec2.stock, 5)

    def test_cannot_cancel_non_pending(self):
        self._fill_cart()
        create_resp = self.client.post(self.order_list_url, {}, format="json")
        order_id = create_resp.json()["data"]["id"]
        # 先支付
        self.client.post(reverse("order-pay", args=[order_id]))
        # 再尝试取消
        resp = self.client.post(reverse("order-cancel", args=[order_id]))
        self.assertEqual(resp.status_code, 400)
        self.assertIn("无法取消", resp.json()["msg"])

    # ---- 支付 ----

    def test_pay_order(self):
        self._fill_cart()
        create_resp = self.client.post(self.order_list_url, {}, format="json")
        order_id = create_resp.json()["data"]["id"]
        url = reverse("order-pay", args=[order_id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["method"], "mock")
        self.assertEqual(data["order"]["status"], "paid")

    def test_cannot_pay_non_pending(self):
        self._fill_cart()
        create_resp = self.client.post(self.order_list_url, {}, format="json")
        order_id = create_resp.json()["data"]["id"]
        # 先支付
        self.client.post(reverse("order-pay", args=[order_id]))
        # 再次支付
        resp = self.client.post(reverse("order-pay", args=[order_id]))
        self.assertEqual(resp.status_code, 400)
        self.assertIn("无法支付", resp.json()["msg"])
