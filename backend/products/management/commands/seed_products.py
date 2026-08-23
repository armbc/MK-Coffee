"""种子数据：分类 + 占位商品"""
from django.core.management.base import BaseCommand
from products.models import Category, Product, Spec


class Command(BaseCommand):
    help = "初始化商品分类和占位商品"

    def handle(self, *args, **options):
        # === 分类 ===
        categories = {
            "袋装咖啡豆": {"sort": 1, "icon": "☕"},
            "罐装咖啡豆": {"sort": 2, "icon": "🫙"},
            "定制烘焙咖啡豆": {"sort": 3, "icon": "🔥"},
            "咖啡器皿": {"sort": 4, "icon": "🫖"},
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

        # === 占位商品 ===
        products_data = [
            {
                "name": "埃塞俄比亚 耶加雪菲",
                "image": "https://api.mk-coffee.cn/static/products/yirgacheffe.jpg",
                "category": "袋装咖啡豆",
                "description": "柑橘、茉莉花、蜂蜜风味，水洗处理",
                "price": 88.00,
                "stock": 50,
                "specs": [("200g", 88.00, 30), ("500g", 198.00, 20)],
            },
            {
                "name": "哥伦比亚 蕙兰",
                "image": "https://api.mk-coffee.cn/static/products/colombia.jpg",
                "category": "袋装咖啡豆",
                "description": "焦糖、坚果、巧克力风味，水洗处理",
                "price": 78.00,
                "stock": 40,
                "specs": [("200g", 78.00, 25), ("500g", 178.00, 15)],
            },
            {
                "name": "巴西 喜拉多",
                "image": "https://api.mk-coffee.cn/static/products/brazil.jpg",
                "category": "罐装咖啡豆",
                "description": "花生、奶油、可可风味，日晒处理",
                "price": 68.00,
                "stock": 60,
                "specs": [("250g", 68.00, 40), ("500g", 128.00, 20)],
            },
            {
                "name": "印尼 曼特宁",
                "image": "https://api.mk-coffee.cn/static/products/mandheling.jpg",
                "category": "罐装咖啡豆",
                "description": "草本、香料、黑巧克力风味，湿刨法",
                "price": 75.00,
                "stock": 35,
                "specs": [("250g", 75.00, 20), ("500g", 138.00, 15)],
            },
            {
                "name": "定制拼配·深烘",
                "image": "https://api.mk-coffee.cn/static/products/custom-dark.jpg",
                "category": "定制烘焙咖啡豆",
                "description": "根据您的口味定制烘焙程度，适合意式浓缩",
                "price": 128.00,
                "stock": 20,
                "specs": [("500g", 128.00, 10), ("1kg", 238.00, 10)],
            },
            {
                "name": "定制拼配·中烘",
                "image": "https://api.mk-coffee.cn/static/products/custom-medium.jpg",
                "category": "定制烘焙咖啡豆",
                "description": "均衡口感，适合手冲和法压壶",
                "price": 118.00,
                "stock": 20,
                "specs": [("500g", 118.00, 10), ("1kg", 218.00, 10)],
            },
            {
                "name": "HARIO V60 滤杯",
                "image": "https://api.mk-coffee.cn/static/products/v60.jpg",
                "category": "咖啡器皿",
                "description": "经典锥形滤杯，陶瓷材质，1-2人份",
                "price": 128.00,
                "stock": 15,
                "specs": [("白色", 128.00, 10), ("黑色", 128.00, 5)],
            },
            {
                "name": "手冲壶·细嘴",
                "image": "https://api.mk-coffee.cn/static/products/kettle.jpg",
                "category": "咖啡器皿",
                "description": "不锈钢细嘴手冲壶，600ml，精准控流",
                "price": 168.00,
                "stock": 10,
                "specs": [("600ml", 168.00, 10)],
            },
            # === 挂耳咖啡（占位，信息待补充）===
            {
                "name": "挂耳咖啡 1",
                "image": "",
                "category": "挂耳咖啡",
                "description": "商品信息待补充",
                "price": 39.00,
                "stock": 10,
                "specs": [("10袋装", 39.00, 10)],
            },
            {
                "name": "挂耳咖啡 2",
                "image": "",
                "category": "挂耳咖啡",
                "description": "商品信息待补充",
                "price": 39.00,
                "stock": 10,
                "specs": [("10袋装", 39.00, 10)],
            },
            {
                "name": "挂耳咖啡 3",
                "image": "",
                "category": "挂耳咖啡",
                "description": "商品信息待补充",
                "price": 39.00,
                "stock": 10,
                "specs": [("10袋装", 39.00, 10)],
            },
            {
                "name": "挂耳咖啡 4",
                "image": "",
                "category": "挂耳咖啡",
                "description": "商品信息待补充",
                "price": 39.00,
                "stock": 10,
                "specs": [("10袋装", 39.00, 10)],
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
            if created:
                for spec_name, spec_price, spec_stock in item["specs"]:
                    Spec.objects.create(
                        product=product,
                        name=spec_name,
                        price=spec_price,
                        stock=spec_stock,
                    )
            self.stdout.write(f"  {'✓' if created else '↻'} 商品: {item['name']}")

        self.stdout.write(self.style.SUCCESS(f"\n种子数据完成: {Category.objects.count()} 分类, {Product.objects.count()} 商品"))
