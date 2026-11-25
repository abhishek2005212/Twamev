
from django.contrib import admin
from .models import Product, Order, OrderItem


# =====================================
# PRODUCT ADMIN
# Products aur stock manage karne ke liye
# =====================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "category",
        "price",
        "stock",
        "is_available",
    )

    list_filter = (
        "category",
        "is_available",
        "is_bestseller",
        "is_new_arrival",
    )

    search_fields = ("name", "sku", "category")

    list_editable = ("price", "stock", "is_available")


# =====================================
# ORDER ITEMS
# Ek order ke andar ke products
# =====================================

class OrderItemInline(admin.TabularInline):

    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "sku", "price", "quantity")
    can_delete = False


# =====================================
# ORDER ADMIN
# Customer orders aur payment status
# =====================================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "order_number",
        "customer_name",
        "phone",
        "total_amount",
        "payment_method",
        "payment_status",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "payment_status",
        "payment_method",
        "created_at",
    )

    search_fields = (
        "order_number",
        "customer_name",
        "phone",
        "email",
    )

    list_editable = ("status", "payment_status")

    readonly_fields = ("order_number", "created_at")

    inlines = [OrderItemInline]


# =====================================
# ORDER ITEM ADMIN
# =====================================

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):

    list_display = (
        "order",
        "product_name",
        "sku",
        "price",
        "quantity",
    )

    search_fields = (
        "order__order_number",
        "product_name",
        "sku",
    )



from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "phone",
        "subject",
        "is_resolved",
        "created_at",
    )

    list_filter = ("is_resolved", "created_at")

    search_fields = (
        "name",
        "email",
        "phone",
        "subject",
        "message",
    )

    list_editable = ("is_resolved",)

    readonly_fields = ("created_at",)
