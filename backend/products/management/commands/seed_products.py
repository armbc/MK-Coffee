"""种子数据：分类 + 商品（2026-08-25 按同事《产品分类与价格》更新）

3 条产品线：铁罐（罐装咖啡豆）/ 挂耳咖啡 / 袋装咖啡豆
- 商品命名对齐同事清单（旧名通过 rename_map 迁移，保留 id 与订单引用）
- 罐装仅保留 250g 单规格（同事未给 500g 价格）
- 同事清单外的旧商品下架（status=off，保留数据）
"""
from django.core.management.base import BaseCommand
from products.models import Category, Product, Spec


class Command(BaseCommand):
    help = "初始化商品分类和商品（3 条产品线：铁罐/挂耳/袋装）"

    def handle(self, *args, **options):
        # === 分类 ===
        categories = {
            "袋装咖啡豆": {"sort": 1, "icon": "☕"},
            "罐装咖啡豆": {"sort": 2, "icon": "🫙"},
            "定制烘焙咖啡豆": {"sort": 3, "icon": "🔥"},  # 分类保留，清单外商品已下架
            # "咖啡器皿": {"sort": 4, "icon": "🫖"},  # 已停用（2026-08-25），恢复时取消注释
            "挂耳咖啡": {"sort": 5, "icon": "🫘"},
        }
        cat_objs = {}
        for name, attrs in categories.items():
            obj, created = Category.objects.get_or_create(
                name=name,
                defaults={"sort_order": attrs["sort"], "icon": attrs["icon"]},
            )
            cat_objs[name] = obj
            self.stdout.write(f"  {'✓' if created else '·'} 分类: {name}")

        # === 旧挂耳占位商品：下架而非删除（有历史订单引用的不能删，置 off 隐藏）===
        stale = Product.objects.filter(
            category=cat_objs["挂耳咖啡"], name__regex=r"^挂耳咖啡 \d+$"
        )
        n = stale.update(status="off")
        if n:
            self.stdout.write(f"  ✗ 下架旧挂耳占位商品: {n} 个")

        # === 旧名 → 同事命名 迁移（保留商品 id，订单引用不断）===
        rename_map = [
            ("印尼 曼特宁", "罐装咖啡豆", "印度尼西亚·曼特宁咖啡豆"),
            ("耶加雪菲", "罐装咖啡豆", "埃塞俄比亚·耶加雪菲咖啡豆"),
            ("低因咖啡豆", "罐装咖啡豆", "哥伦比亚·低因咖啡豆"),
            ("意式拼配", "罐装咖啡豆", "意式拼配咖啡豆"),
            ("意式拼配 500g", "袋装咖啡豆", "经典意式拼配咖啡豆"),
            ("巴西 挂耳咖啡", "挂耳咖啡", "巴西·喜拉多挂耳咖啡"),
            ("低因 挂耳咖啡", "挂耳咖啡", "哥伦比亚·低因处理挂耳咖啡"),
            ("曼特宁 挂耳咖啡", "挂耳咖啡", "印度尼西亚·曼特宁挂耳咖啡"),
            ("耶加雪菲 挂耳咖啡", "挂耳咖啡", "埃塞俄比亚·耶加雪菲挂耳咖啡"),
        ]
        for old_name, cat_name, new_name in rename_map:
            qs = Product.objects.filter(name=old_name, category=cat_objs[cat_name])
            if qs.exists():
                qs.update(name=new_name)
                self.stdout.write(f"  ↻ 改名: {old_name} → {new_name}")

        # === 商品数据（同事清单：3 条产品线 9 个商品）===
        products_data = [
            # ---- 袋装线 ----
            {
                "name": "经典意式拼配咖啡豆",
                "image": "https://api.mk-coffee.cn/static/products/500g_yishi.jpg",
                "category": "袋装咖啡豆",
                "description": "大包装深烘意式拼配，浓郁醇厚，适合日常口粮与办公场景",
                "price": 109.00,
                "stock": 50,
                "specs": [("500g", 109.00, 50)],
            },
            # ---- 罐装线（200g 单规格）----
            {
                "name": "印度尼西亚·曼特宁咖啡豆",
                "image": "https://api.mk-coffee.cn/static/products/bin_mantening.jpg",
                "category": "罐装咖啡豆",
                "description": "草本、香料、黑巧克力风味，湿刨法",
                "price": 69.00,
                "stock": 35,
                "specs": [("200g", 69.00, 35)],
            },
            {
                "name": "埃塞俄比亚·耶加雪菲咖啡豆",
                "image": "https://api.mk-coffee.cn/static/products/bin_yejia.jpg",
                "category": "罐装咖啡豆",
                "description": "柑橘、茉莉花、蜂蜜风味，水洗处理",
                "price": 69.00,
                "stock": 30,
                "specs": [("200g", 69.00, 30)],
            },
            {
                "name": "哥伦比亚·低因咖啡豆",
                "image": "https://api.mk-coffee.cn/static/products/bin_diyin.jpg",
                "category": "罐装咖啡豆",
                "description": "脱因处理，风味柔和，晚间也可安心饮用",
                "price": 79.00,
                "stock": 30,
                "specs": [("200g", 79.00, 30)],
            },
            {
                "name": "意式拼配咖啡豆",
                "image": "https://api.mk-coffee.cn/static/products/bin_yishi.jpg",
                "category": "罐装咖啡豆",
                "description": "经典意式拼配，浓郁醇厚、油脂丰富，适合浓缩与奶咖",
                "price": 59.00,
                "stock": 40,
                "specs": [("200g", 59.00, 40)],
            },
            # ---- 挂耳线（10袋装）----
            {
                "name": "印度尼西亚·曼特宁挂耳咖啡",
                "image": "https://api.mk-coffee.cn/static/products/drip_mantening.jpg",
                "category": "挂耳咖啡",
                "description": "草本、香料、黑巧克力风味，湿刨法",
                "price": 69.00,
                "stock": 25,
                "specs": [("10袋装", 69.00, 25)],
            },
            {
                "name": "埃塞俄比亚·耶加雪菲挂耳咖啡",
                "image": "https://api.mk-coffee.cn/static/products/drip_yejia.jpg",
                "category": "挂耳咖啡",
                "description": "柑橘、茉莉花、蜂蜜风味，水洗处理",
                "price": 69.00,
                "stock": 30,
                "specs": [("10袋装", 69.00, 30)],
            },
            {
                "name": "哥伦比亚·低因处理挂耳咖啡",
                "image": "https://api.mk-coffee.cn/static/products/drip_diyin.jpg",
                "category": "挂耳咖啡",
                "description": "脱因处理，柔和顺口，适合晚间饮用",
                "price": 79.00,
                "stock": 25,
                "specs": [("10袋装", 79.00, 25)],
            },
            {
                "name": "巴西·喜拉多挂耳咖啡",
                "image": "https://api.mk-coffee.cn/static/products/drip_baxi.jpg",
                "category": "挂耳咖啡",
                "description": "坚果、可可、焦糖风味，日晒处理",
                "price": 59.00,
                "stock": 30,
                "specs": [("10袋装", 59.00, 30)],
            },
        ]

        for item in products_data:
            cat = cat_objs[item["category"]]
            product, created = Product.objects.update_or_create(
                name=item["name"],
                category=cat,
                defaults={
                    "description": item["description"],
                    "price": item["price"],
                    "stock": item["stock"],
                    "status": "on",
                    "image": item.get("image", ""),
                },
            )
            # 同步规格：删除重建（CartItem/OrderItem 对 spec 均为 SET_NULL，安全）
            product.specs.all().delete()
            for spec_name, spec_price, spec_stock in item["specs"]:
                Spec.objects.create(
                    product=product,
                    name=spec_name,
                    price=spec_price,
                    stock=spec_stock,
                )
            self.stdout.write(f"  {'✓' if created else '↻'} 商品: {item['name']}")

        # === 下架同事清单外的旧商品（保留数据，可恢复）===
        # 注：按商品名匹配（全库唯一），跨环境幂等（本地已删分类/商品，生产因订单引用保留）
        down_list = [
            ("埃塞俄比亚 耶加雪菲", "袋装咖啡豆"),
            ("哥伦比亚 蕙兰", "袋装咖啡豆"),
            ("巴西 喜拉多", "罐装咖啡豆"),
            ("定制拼配·深烘", "定制烘焙咖啡豆"),
            ("定制拼配·中烘", "定制烘焙咖啡豆"),
            ("HARIO V60 滤杯", "咖啡器皿"),   # 器皿分类已停用；商品有历史订单引用不能删
            ("手冲壶·细嘴", "咖啡器皿"),
        ]
        off_count = Product.objects.filter(
            name__in=[name for name, _ in down_list]
        ).update(status="off")
        if off_count:
            self.stdout.write(f"  ✗ 下架清单外商品: {off_count} 个")

        self.stdout.write(self.style.SUCCESS(f"\n种子数据完成: {Category.objects.count()} 分类, {Product.objects.count()} 商品"))
