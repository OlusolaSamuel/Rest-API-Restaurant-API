from django.urls import path
from . import views

urlpatterns = [
    path('add_user_to_group/', views.add_user_to_group),
    path('remove_user_from_group/', views.remove_user_from_group),
    path('menu_items/', views.menu_item_view),
    path('cart/add/', views.add_to_cart),
    path('cart/flush/', views.flush_cart),
    path('orders/', views.browse_orders),
    path('orders/place/', views.place_order),
    path('orders/mark_as_delivered/<int:order_id>/', views.mark_order_as_delivered),
    path('categories/', views.category_list),
    path('categories/<int:pk>/', views.category_detail),
    path('order-items/', views.order_item_list),
    path('order-items/<int:pk>/', views.order_item_detail),
]
