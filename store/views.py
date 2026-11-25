import json
import uuid
import logging

from decimal import Decimal
from json import JSONDecodeError
from xml.dom import ValidationErr

from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import Product, Order, OrderItem, ContactMessage

def contact(request):
    return render(request, "contact.html")


# ==================================================
# 1. HOME PAGE
# Database se products lekar website par dikhata hai
# ==================================================

@ensure_csrf_cookie
def home(request):

    products = Product.objects.filter(is_available=True)

    products_data = []

    for product in products:

        product_images = product.images or []

        # Agar multiple images nahi hain, toh single image use karo
        if not product_images and product.image_url:
            product_images = [product.image_url]

        products_data.append({
            "id": product.id,
            "sku": product.sku,
            "name": product.name,
            "category": product.category,
            "price": float(product.price),
            "originalPrice": float(product.original_price),
            "rating": float(product.rating),
            "reviewsCount": product.reviews_count,
            "stock": product.stock,
            "isBestseller": product.is_bestseller,
            "isNewArrival": product.is_new_arrival,
            "shortDesc": product.short_desc,
            "description": product.description,
            "highlights": product.highlights or [],
            "images": product_images,
        })

    return render(
        request,
        "home.html",
        {
            "products": products,
            "products_data": products_data,
        }
    )


# ==================================================
# 2. CREATE ORDER
# Checkout form se order receive karta hai
# ==================================================

@require_POST

def create_order(request):
    # 1. JSON data read karo
    try:
        data = json.loads(request.body)
    except (JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"error": "Invalid order data."},
            status=400
        )

    if not isinstance(data, dict):
        return JsonResponse(
            {"error": "Invalid order data."},
            status=400
        )

    customer = data.get("customer", {})
    items = data.get("items", [])
    pricing = data.get("pricing", {})

    if not isinstance(customer, dict) or not isinstance(pricing, dict):
        return JsonResponse(
            {"error": "Invalid customer or pricing details."},
            status=400
        )

    # 2. Customer details
    name = str(customer.get("full_name", "")).strip()
    phone = str(customer.get("phone", "")).strip()
    email = str(customer.get("email", "")).strip()
    address = str(customer.get("street_address", "")).strip()
    city = str(customer.get("city", "")).strip()
    state = str(customer.get("state", "")).strip()
    pincode = str(customer.get("pincode", "")).strip()
    note = str(customer.get("note", "")).strip()

    if len(name) < 3:
        return JsonResponse(
            {"error": "Please enter a valid name."}, status=400
        )

    if not phone.isdigit() or len(phone) != 10:
        return JsonResponse(
            {"error": "Please enter a valid 10-digit phone number."},
            status=400
        )

    if email and (
    "@" not in email or "." not in email.split("@")[-1]
):
        return JsonResponse(
        {"error": "Please enter a valid email address."},
        status=400
    )

    if len(address) < 8 or not city or not state:
        return JsonResponse(
            {"error": "Please enter a complete delivery address."},
            status=400
        )

    if not pincode.isdigit() or len(pincode) != 6:
        return JsonResponse(
            {"error": "Please enter a valid 6-digit PIN code."},
            status=400
        )

    # 3. Cart validate karo aur duplicate products combine karo
    if not isinstance(items, list) or not items or len(items) > 100:
        return JsonResponse(
            {"error": "Cart is empty or contains too many items."},
            status=400
        )

    quantities = {}

    try:
        for item in items:
            if not isinstance(item, dict):
                return JsonResponse(
                    {"error": "Invalid cart item."}, status=400
                )

            product_id = int(item.get("product_id"))
            quantity = int(item.get("quantity"))

            if product_id < 1 or quantity < 1 or quantity > 50:
                return JsonResponse(
                    {"error": "Invalid product ID or quantity."},
                    status=400
                )

            quantities[product_id] = (
                quantities.get(product_id, 0) + quantity
            )

            if quantities[product_id] > 50:
                return JsonResponse(
                    {"error": "Maximum 50 units per product allowed."},
                    status=400
                )

    except (ValueError, TypeError):
        return JsonResponse(
            {"error": "Invalid product ID or quantity."},
            status=400
        )

    payment_method = data.get("payment_method", "COD")

    if payment_method not in ["COD", "RAZORPAY_ONLINE"]:
        return JsonResponse(
            {"error": "Invalid payment method."},
            status=400
        )

    # 4. Order aur stock ko ek transaction mein save karo
    try:
        with transaction.atomic():

            order_items = []
            subtotal = Decimal("0.00")

            # Products ko ID ke order mein lock karo
            # Taaki simultaneous orders stock ko oversell na karein.
            for product_id in sorted(quantities):
                product = (
                    Product.objects
                    .select_for_update()
                    .get(id=product_id, is_available=True)
                )

                quantity = quantities[product_id]

                # Latest database stock check
                if product.stock < quantity:
                    return JsonResponse(
                        {
                            "error": (
                                f"Not enough stock for {product.name}. "
                                f"Available stock: {product.stock}"
                            )
                        },
                        status=400
                    )

                subtotal += product.price * quantity

                order_items.append({
                    "product": product,
                    "product_name": product.name,
                    "sku": product.sku,
                    "price": product.price,
                    "quantity": quantity,
                })

            # 5. Coupon calculate karo
            coupon_code = str(
                pricing.get("coupon_code") or ""
            ).strip().upper()

            discount = Decimal("0.00")

            if coupon_code == "TWAMEV10":
                discount = (
                    subtotal * Decimal("10") / Decimal("100")
                ).quantize(Decimal("1"))

            elif (
                coupon_code == "DIVINE20"
                and subtotal >= Decimal("1299")
            ):
                discount = (
                    subtotal * Decimal("20") / Decimal("100")
                ).quantize(Decimal("1"))

            else:
                coupon_code = ""

            after_discount = subtotal - discount

            if after_discount >= Decimal("999"):
                delivery_charge = Decimal("0.00")
            else:
                delivery_charge = Decimal("79.00")

            total_amount = after_discount + delivery_charge

            # 6. Main order save karo
            order_number = "TWM-" + uuid.uuid4().hex[:10].upper()

            order = Order.objects.create(
                order_number=order_number,
                customer_name=name,
                phone=phone,
                email=email,
                address=address,
                city=city,
                state=state,
                pincode=pincode,
                customer_note=note,
                subtotal=subtotal,
                discount=discount,
                coupon_code=coupon_code,
                delivery_charge=delivery_charge,
                total_amount=total_amount,
                payment_method=payment_method,
                payment_status="Pending",
                status="Pending",
            )

            # 7. Order items save karo aur stock deduct karo
            for item in order_items:
                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    product_name=item["product_name"],
                    sku=item["sku"],
                    price=item["price"],
                    quantity=item["quantity"],
                )

                product = item["product"]
                product.stock -= item["quantity"]
                product.save(update_fields=["stock"])

    except Product.DoesNotExist:
        return JsonResponse(
            {"error": "A selected product is unavailable."},
            status=400
        )

    except Exception:
        logging.exception("Twamev order creation failed.")
        return JsonResponse(
            {"error": "Order save nahi ho saka. Please try again."},
            status=500
        )

    # 8. Frontend ko success response
    return JsonResponse(
        {
            "success": True,
            "order_number": order.order_number,
            "status": order.status,
            "total_amount": str(order.total_amount),
            "message": "Order successfully saved in the database.",
        },
        status=201
    )

def order_confirmation(request):
    return render(request, "order_confirmation.html")




@require_POST
def submit_contact(request):
    name = request.POST.get("name", "").strip()
    phone = request.POST.get("phone", "").strip()
    email = request.POST.get("email", "").strip()
    subject = request.POST.get("subject", "").strip()
    message = request.POST.get("message", "").strip()

    if len(name) < 2:
        return JsonResponse(
            {"error": "Please enter a valid name."},
            status=400
        )

    if not phone.isdigit() or len(phone) != 10 or phone[0] not in "6789":
        return JsonResponse(
            {"error": "Please enter a valid 10-digit phone number."},
            status=400
        )

    if email:
        try:
            validate_email(email) # type: ignore
        except ValidationErr:
            return JsonResponse(
                {"error": "Please enter a valid email address."},
                status=400
            )

    if len(message) < 10:
        return JsonResponse(
            {"error": "Message must contain at least 10 characters."},
            status=400
        )

    if len(name) > 100 or len(subject) > 200:
        return JsonResponse(
            {"error": "Name or subject is too long."},
            status=400
        )

    enquiry = ContactMessage.objects.create(
        name=name,
        phone=phone,
        email=email,
        subject=subject,
        message=message
    )

    return JsonResponse(
        {
            "success": True,
            "message": "Your enquiry has been saved successfully.",
            "id": enquiry.id
        },
        status=201
    )

