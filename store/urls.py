from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    path(
        "api/orders/",
        views.create_order,
        name="create_order"
    ),

    path(
        "order-confirmation/",
        views.order_confirmation,
        name="order_confirmation"
    ),

    path(
        "api/contact/",
        views.submit_contact,
        name="submit_contact"
    ),

    path(
        "contact/",
        views.contact,
        name="contact"
    ),
]