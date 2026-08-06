"""商品模块 · Admin"""
from django.contrib import admin
from .models import Category, Product, Spec


class SpecInline(admin.TabularInline):
    model = Spec
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "sort_order", "created_at"]
    search_fields = ["name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "stock", "status", "created_at"]
    list_filter = ["category", "status"]
    search_fields = ["name"]
    inlines = [SpecInline]
