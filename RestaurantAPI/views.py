from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User, Group
from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import CategorySerializer, MenuItemSerializer, CartSerializer, OrderSerializer, OrderItemSerializer

@api_view(['POST'])
@permission_classes([IsAdminUser])
def add_user_to_group(request):
    user_id = request.data.get('user_id')
    group_name = request.data.get('group')
    user = User.objects.get(id=user_id)
    group = Group.objects.get(name=group_name)
    user.groups.add(group)
    return Response({'status': 'user added to group'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def remove_user_from_group(request):
    user_id = request.data.get('user_id')
    group_name = request.data.get('group')
    user = User.objects.get(id=user_id)
    group = Group.objects.get(name=group_name)
    user.groups.remove(group)
    return Response({'status': 'user removed from group'}, status=status.HTTP_200_OK)

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def menu_item_view(request):
    if request.method == 'GET':
        items = MenuItem.objects.all()
        if request.query_params.get('category'):
            items = items.filter(category__slug=request.query_params.get('category'))
        if request.query_params.get('price'):
            items = items.filter(price=request.query_params.get('price'))
        serializer = MenuItemSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method in ['POST', 'PUT', 'DELETE']:
        if request.user.groups.filter(name='Manager').exists():
            if request.method == 'POST':
                serializer = MenuItemSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
            elif request.method == 'PUT':
                item = MenuItem.objects.get(id=request.data.get('id'))
                serializer = MenuItemSerializer(item, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
            elif request.method == 'DELETE':
                item = MenuItem.objects.get(id=request.data.get('id'))
                item.delete()
                return Response({'status': 'deleted'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    user = request.user
    menu_item_id = request.data.get('menuitem_id')
    quantity = request.data.get('quantity')

    menu_item = MenuItem.objects.get(id=menu_item_id)
    unit_price = menu_item.price
    price = unit_price * quantity

    cart_item, created = Cart.objects.update_or_create(
        user=user, menuitem=menu_item,
        defaults={'quantity': quantity, 'unit_price': unit_price, 'price': price},
    )
    serializer = CartSerializer(cart_item)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def place_order(request):
    user = request.user
    cart_items = Cart.objects.filter(user=user)
    if not cart_items.exists():
        return Response({'error': 'No items in cart'}, status=status.HTTP_400_BAD_REQUEST)

    total = sum(item.price for item in cart_items)
    order = Order.objects.create(user=user, total=total, status=False)

    for item in cart_items:
        OrderItem.objects.create(order=order, menuitem=item.menuitem, quantity=item.quantity,
                                 unit_price=item.unit_price, price=item.price)
    cart_items.delete()
    serializer = OrderSerializer(order)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def flush_cart(request):
    user = request.user
    Cart.objects.filter(user=user).delete()
    return Response({'status': 'cart flushed'}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def browse_orders(request):
    if request.user.groups.filter(name='Manager').exists():
        orders = Order.objects.all()
        if 'status' in request.query_params:
            orders = orders.filter(status=request.query_params.get('status'))
    elif request.user.groups.filter(name='Delivery Crew').exists():
        orders = Order.objects.filter(delivery_crew=request.user)
    else:
        orders = Order.objects.filter(user=request.user)

    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_order_as_delivered(request, order_id):
    order = Order.objects.get(id=order_id)
    if request.user == order.delivery_crew:
        order.status = True
        order.save()
        return Response({'status': 'order marked as delivered'}, status=status.HTTP_200_OK)
    return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def category_list(request):
    if request.method == 'GET':
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        if request.user.groups.filter(name='Manager').exists():
            serializer = CategorySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"detail": "Only managers can create categories."}, status=status.HTTP_403_FORBIDDEN)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def category_detail(request, pk):
    try:
        category = Category.objects.get(pk=pk)
    except Category.DoesNotExist:
        return Response({"detail": "Category not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = CategorySerializer(category)
        return Response(serializer.data)

    elif request.method == 'PUT':
        if request.user.groups.filter(name='Manager').exists():
            serializer = CategorySerializer(category, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"detail": "Only managers can update categories."}, status=status.HTTP_403_FORBIDDEN)

    elif request.method == 'DELETE':
        if request.user.groups.filter(name='Manager').exists():
            category.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"detail": "Only managers can delete categories."}, status=status.HTTP_403_FORBIDDEN)

# OrderItem Views
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def order_item_list(request):
    if request.method == 'GET':
        order_items = OrderItem.objects.all()
        serializer = OrderItemSerializer(order_items, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        if request.user.groups.filter(name='Manager').exists() or \
                request.user.groups.filter(name='Delivery Crew').exists():
            serializer = OrderItemSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"detail": "Only managers or delivery crew can create order items."}, status=status.HTTP_403_FORBIDDEN)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def order_item_detail(request, pk):
    try:
        order_item = OrderItem.objects.get(pk=pk)
    except OrderItem.DoesNotExist:
        return Response({"detail": "Order item not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = OrderItemSerializer(order_item)
        return Response(serializer.data)

    elif request.method == 'PUT':
        if request.user == order_item.order.delivery_crew or \
                request.user.groups.filter(name='Manager').exists():
            serializer = OrderItemSerializer(order_item, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"detail": "Only assigned delivery crew or managers can update this order item."}, status=status.HTTP_403_FORBIDDEN)

    elif request.method == 'DELETE':
        if request.user.groups.filter(name='Manager').exists():
            order_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"detail": "Only managers can delete order items."}, status=status.HTTP_403_FORBIDDEN)