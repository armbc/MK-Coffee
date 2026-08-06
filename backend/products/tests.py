"""商品模块 · 测试"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Category, Product, Spec


class CategoryModelTest(TestCase):
    def test_create_category(self):
        cat = Category.objects.create(name="测试分类", sort_order=1, icon="☕")
        self.assertEqual(cat.name, "测试分类")
        self.assertEqual(cat.sort_order, 1)


class ProductModelTest(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="咖啡豆")

    def test_create_product(self):
        p = Product.objects.create(
            name="测试商品", category=self.cat,
            price=99.00, stock=10, status="on",
        )
        self.assertEqual(p.price, 99.00)
        self.assertEqual(p.status, "on")

    def test_product_with_specs(self):
        p = Product.objects.create(
            name="多规格商品", category=self.cat,
            price=128.00, stock=100,
        )
        Spec.objects.create(product=p, name="200g", price=68.00, stock=30)
        Spec.objects.create(product=p, name="500g", price=158.00, stock=20)
        self.assertEqual(p.specs.count(), 2)

    def test_off_product_not_in_queryset(self):
        Product.objects.create(name="下架商品", category=self.cat, status="off")
        self.assertEqual(Product.objects.filter(status="on").count(), 0)


class ProductAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.cat = Category.objects.create(name="袋装咖啡豆")
        self.p1 = Product.objects.create(
            name="耶加雪菲", category=self.cat, price=88.00, stock=50,
        )
        self.p2 = Product.objects.create(
            name="曼特宁", category=self.cat, price=75.00, stock=30,
        )
        Spec.objects.create(product=self.p1, name="200g", price=88.00, stock=30)

    def test_category_list(self):
        resp = self.client.get(reverse("category-list"))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        results = data["data"]["results"]  # 分页格式
        self.assertGreaterEqual(len(results), 1)
        names = [c["name"] for c in results]
        self.assertIn("袋装咖啡豆", names)

    def test_product_list(self):
        resp = self.client.get(reverse("product-list"))
        self.assertEqual(resp.status_code, 200)
        results = resp.json()["data"]["results"]
        self.assertEqual(len(results), 2)

    def test_product_list_filter_by_category(self):
        resp = self.client.get(reverse("product-list") + f"?category={self.cat.id}")
        self.assertEqual(resp.status_code, 200)
        results = resp.json()["data"]["results"]
        self.assertEqual(len(results), 2)

    def test_product_detail(self):
        resp = self.client.get(reverse("product-detail", args=[self.p1.id]))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["name"], "耶加雪菲")
        self.assertEqual(data["category_name"], "袋装咖啡豆")
        self.assertEqual(len(data["specs"]), 1)
        self.assertEqual(data["specs"][0]["name"], "200g")

    def test_off_product_not_listed(self):
        Product.objects.create(name="隐藏商品", category=self.cat, status="off")
        resp = self.client.get(reverse("product-list"))
        results = resp.json()["data"]["results"]
        self.assertEqual(len(results), 2)  # 仍然是 2 个，隐藏的不出现

    def test_product_detail_404(self):
        resp = self.client.get(reverse("product-detail", args=[9999]))
        self.assertEqual(resp.status_code, 404)
