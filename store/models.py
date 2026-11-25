
from django.db import models


# ==========================================
# PRODUCT MODEL
# Website ke products ki details save karega
# ==========================================

class Product(models.Model):

    name = models.CharField(max_length=200)

    category = models.CharField(
        max_length=100,
        default="Pooja Samagri"
    )

    sku = models.CharField(
        max_length=40,
        blank=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    short_desc = models.CharField(
        max_length=250,
        blank=True
    )

    description = models.TextField(blank=True)

    image_url = models.URLField(
        max_length=500,
        blank=True
    )

    images = models.JSONField(
        default=list,
        blank=True
    )

    highlights = models.JSONField(
        default=list,
        blank=True
    )

    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=5.0
    )

    reviews_count = models.PositiveIntegerField(default=0)

    stock = models.PositiveIntegerField(default=25)

    is_bestseller = models.BooleanField(default=False)

    is_new_arrival = models.BooleanField(default=False)

    is_available = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ==========================================
# ORDER MODEL
# Customer ke order ki details save karega
# ==========================================

class Order(models.Model):

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Packed", "Packed"),
        ("Shipped", "Shipped"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("COD", "Cash on Delivery"),
        ("RAZORPAY_ONLINE", "Online Payment"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Paid", "Paid"),
        ("Failed", "Failed"),
        ("Refunded", "Refunded"),
    ]

    order_number = models.CharField(
        max_length=30,
        unique=True
    )

    customer_name = models.CharField(max_length=150)

    phone = models.CharField(max_length=15)

    email = models.EmailField(blank=True)

    address = models.TextField()

    city = models.CharField(max_length=100)

    state = models.CharField(max_length=100)

    pincode = models.CharField(max_length=6)

    customer_note = models.TextField(blank=True)

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    coupon_code = models.CharField(
        max_length=30,
        blank=True
    )

    delivery_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHOD_CHOICES,
        default="COD"
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="Pending"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order_number} - {self.customer_name}"


# ==========================================
# ORDER ITEM MODEL
# Order mein kaun se products hain
# ==========================================

class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    product_name = models.CharField(max_length=200)

    sku = models.CharField(
        max_length=40,
        blank=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

    @property
    def line_total(self):
        return self.price * self.quantity


# ==========================================
# CONTACT MESSAGE MODEL
# Website ke contact form ki enquiries
# ==========================================

class ContactMessage(models.Model):

    name = models.CharField(max_length=100)

    email = models.EmailField(blank=True)

    phone = models.CharField(max_length=15, blank=True)

    subject = models.CharField(max_length=200, blank=True)

    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.created_at:%d-%m-%Y}"
