from rest_framework import response, status
from django.http import JsonResponse

# Utility to convert Django Template response logic to JSON
def json_response_wrapper(view_func, request, *args, **kwargs):
    res = view_func(request, *args, **kwargs)
    if isinstance(res, JsonResponse):
        return res
    # If it's a standard Django response (like a redirect or template render)
    # we might need to handle it or at least ensure it's JSON for our API
    if hasattr(res, 'content'):
        try:
            data = json.loads(res.content)
            return JsonResponse(data)
        except:
            pass
    return JsonResponse({'success': True}) # Fallback

from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import PlayerProfile, Item, ShopItem, InventoryItem, Combat, TavernItem, ChatRoom, ChatMessage
from .serializers import PlayerProfileSerializer, ItemSerializer, InventoryItemSerializer, CombatSerializer, ChatMessageSerializer
from django.db import transaction
import json
from django.shortcuts import get_object_or_404
from .combat_logic import start_battle, handle_player_turn

class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            profile = PlayerProfile.objects.get(user=user)
            return Response(PlayerProfileSerializer(profile).data)
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class RegisterView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = User.objects.create_user(username=username, password=password)
            profile = PlayerProfile.objects.create(
                user=user,
                name=user.username,
                level=0,
                classification='warrior'
            )

        login(request, user)
        return Response(PlayerProfileSerializer(profile).data, status=status.HTTP_201_CREATED)

class LogoutView(views.APIView):
    def post(self, request):
        logout(request)
        return Response({'success': True})

class MeView(views.APIView):
    def get(self, request):
        profile = PlayerProfile.objects.get(user=request.user)
        return Response(PlayerProfileSerializer(profile).data)

class DistributeStatView(views.APIView):
    def post(self, request):
        stat_name = request.data.get('stat_name')
        profile = PlayerProfile.objects.get(user=request.user)
        if profile.distribute_stat(stat_name):
            return Response(PlayerProfileSerializer(profile).data)
        return Response({'error': 'Failed to distribute stat'}, status=status.HTTP_400_BAD_REQUEST)

class InventoryListView(views.APIView):
    def get(self, request):
        profile = PlayerProfile.objects.get(user=request.user)
        items = InventoryItem.objects.filter(owner=profile)
        return Response(InventoryItemSerializer(items, many=True).data)

class EquipItemView(views.APIView):
    def post(self, request):
        from .views import equip_item
        res = equip_item(request)
        return Response(json.loads(res.content))

class UnequipItemView(views.APIView):
    def post(self, request):
        from .views import unequip_item
        res = unequip_item(request)
        return Response(json.loads(res.content))

class UseItemView(views.APIView):
    def post(self, request):
        from .views import api_use_item
        res = api_use_item(request)
        return Response(json.loads(res.content))

class ShopListView(views.APIView):
    def get(self, request):
        shop_items = ShopItem.objects.filter(is_available=True).select_related('item')
        data = []
        for si in shop_items:
            data.append({
                'id': si.id,
                'item': ItemSerializer(si.item).data,
                'price_money': si.price_money,
                'price_silver': si.price_silver,
                'price_gold': si.price_gold,
            })
        return Response(data)

class ShopPurchaseView(views.APIView):
    def post(self, request):
        from .views import api_shop_purchase
        res = api_shop_purchase(request)
        return Response(json.loads(res.content))

class TavernListView(views.APIView):
    def get(self, request):
        items = TavernItem.objects.filter(is_available=True)
        data = {}
        for item in items:
            if item.category not in data:
                data[item.category] = []
            data[item.category].append({
                'id': item.id,
                'name': item.name,
                'price': item.price,
                'hp_restore': item.hp_restore,
                'mp_restore': item.mp_restore,
                'image': item.image.url if item.image else None,
                'stock': item.stock
            })
        return Response(data)

class TavernPurchaseView(views.APIView):
    def post(self, request):
        from .views import tavern_purchase
        res = tavern_purchase(request)
        return Response(json.loads(res.content))

class CombatStateView(views.APIView):
    def get(self, request, combat_id):
        combat = get_object_or_404(Combat, id=combat_id, owner=request.user)
        return Response(CombatSerializer(combat).data)

class CombatTurnView(views.APIView):
    def post(self, request, combat_id):
        combat = get_object_or_404(Combat, id=combat_id, owner=request.user)
        attack_zone = request.data.get('attack_zone')
        defense_zones = request.data.get('defense_zones')

        new_state = handle_player_turn(combat.state, attack_zone, defense_zones)
        combat.state = new_state
        combat.save()

        if new_state['status'] != 'active':
            from .combat_logic import finish_battle
            player_profile = PlayerProfile.objects.get(user=request.user)
            result_msg = finish_battle(combat, player_profile)
            new_state['result_message'] = result_msg
            combat.state = new_state
            combat.save()

        return Response(CombatSerializer(combat).data)

class StartHuntView(views.APIView):
    def post(self, request):
        player_profile = PlayerProfile.objects.get(user=request.user)

        # Check if already in combat
        active_combat = Combat.objects.filter(owner=request.user, state__status='active').first()
        if active_combat:
            return Response(CombatSerializer(active_combat).data)

        combat_state = start_battle(player_profile)
        combat = Combat.objects.create(owner=request.user, state=combat_state)
        return Response(CombatSerializer(combat).data, status=status.HTTP_201_CREATED)
