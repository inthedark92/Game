from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import ChatRoom, ChatMessage, PlayerProfile, Item, ShopItem, TavernItem, InventoryItem, Combat
import json
from datetime import datetime
import logging
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.utils import timezone


def is_admin(user):
    return user.is_superuser

logger = logging.getLogger(__name__)

def home(request):
    if request.user.is_authenticated:
        return redirect('game_home')
    return redirect('login')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('game_home')
    else:
        form = AuthenticationForm()
    return render(request, 'game/login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Создаём профиль игрока для нового пользователя
            PlayerProfile.objects.create(
                user=user,
                name=user.username,  # Используем имя пользователя как имя персонажа
                level=0,
                classification='warrior',  # Или 'mage' по умолчанию
                # Остальные поля будут заполнены значениями по умолчанию из модели
            )
            
            login(request, user)
            return redirect('game_home')
    else:
        form = UserCreationForm()
    return render(request, 'game/register.html', {'form': form})

@login_required
def game_home(request):
    try:
        profile, created = PlayerProfile.objects.get_or_create(user=request.user)
        
        current_location = profile.current_location
        
        context = {
            'profile': {
                'name': profile.name,
                'level': profile.level,
                'classification': profile.classification,
                'clan': None,
                'experience': profile.experience,
                'experience_to_next_level': profile.experience_to_next_level,
                'current_location': current_location.name if current_location else "Неизвестно"
            },
            'resources': {
                'current_hp': profile.current_hp,
                'max_hp': profile.max_hp,
                'current_mp': profile.current_mp,
                'max_mp': profile.max_mp,
                'hp_regen_percent': profile.hp_regen_rate,
                'mp_regen_percent': profile.mp_regen_rate
            },
            'stats': {
                'total_strength': profile.get_total_strength(),
                'strength_base': profile.strength_base,
                'strength_mod': profile.strength_mod,
                'total_agility': profile.get_total_agility(),
                'agility_base': profile.agility_base,
                'agility_mod': profile.agility_mod, 
                'total_intuition': profile.get_total_intuition(),
                'intuition_base': profile.intuition_base,
                'intuition_mod': profile.intuition_mod,
                'total_endurance': profile.get_total_endurance(),
                'endurance_base': profile.endurance_base,
                'endurance_mod': profile.endurance_mod,
                'total_intelligence': profile.get_total_intelligence(),
                'intelligence_base': profile.intelligence_base,
                'intelligence_mod': profile.intelligence_mod,
                'total_wisdom': profile.get_total_wisdom(),
                'wisdom_base': profile.wisdom_base,
                'wisdom_mod': profile.wisdom_mod,
                'total_spirit': profile.get_total_spirit(),
                'spirit_base': profile.spirit_base,
                'spirit_mod': profile.spirit_mod
            },
            'combat': profile.get_combat_stats(),
            'magic': profile.get_magic_stats(),
            'wallet': profile.get_wallet_summary()
        }
        return render(request, 'game/game_home.html', context)
    except Exception as e:
        logger.error(f"Error in game_home: {str(e)}", exc_info=True)
        return redirect('error')

@login_required
def character_panel(request):
    try:
        profile = PlayerProfile.objects.get(user=request.user)
        
        stats = {
            'total_strength': profile.get_total_strength(),
            'strength_base': profile.strength_base,
            'strength_mod': profile.strength_mod,
            'total_agility': profile.get_total_agility(),
            'agility_base': profile.agility_base,
            'agility_mod': profile.agility_mod, 
            'total_intuition': profile.get_total_intuition(),
            'intuition_base': profile.intuition_base,
            'intuition_mod': profile.intuition_mod,
            'total_endurance': profile.get_total_endurance(),
            'endurance_base': profile.endurance_base,
            'endurance_mod': profile.endurance_mod,
            'total_intelligence': profile.get_total_intelligence(),
            'intelligence_base': profile.intelligence_base,
            'intelligence_mod': profile.intelligence_mod,
            'total_wisdom': profile.get_total_wisdom(),
            'wisdom_base': profile.wisdom_base,
            'wisdom_mod': profile.wisdom_mod,
            'total_spirit': profile.get_total_spirit(),
            'spirit_base': profile.spirit_base,
            'spirit_mod': profile.spirit_mod
        }
        
        context = {
            'profile': {
                'name': profile.name,
                'level': profile.level,
                'classification': profile.classification,
                'clan': None,
                'experience': profile.experience,
                'experience_to_next_level': profile.experience_to_next_level,
            },
            'resources': {
                'current_hp': profile.current_hp,
                'max_hp': profile.max_hp,
                'current_mp': profile.current_mp,
                'max_mp': profile.max_mp,
                'hp_regen_percent': profile.hp_regen_rate,
                'mp_regen_percent': profile.mp_regen_rate,
            },
            'stats': stats,
            'combat': profile.get_combat_stats(),
            'magic': profile.get_magic_stats(),
            'wallet': profile.get_wallet_summary(),
        }
        
        return render(request, 'character_panel.html', context)
    except Exception as e:
        logger.error(f"Error in character_panel: {str(e)}", exc_info=True)
        return redirect('error')

@login_required
def inventory_panel(request):
    return render(request, 'inventory_panel.html')

@login_required
def shop_panel(request):
    try:
        shop_items = ShopItem.objects.filter(is_available=True).select_related('item')
        items_data = []
        
        for shop_item in shop_items:
            item = shop_item.item
            items_data.append({
                'id': item.id,
                'name': item.name,
                'description': item.description,
                'type': item.type,
                'subtype': item.subtype,
                'image': item.image.url if item.image else None,
                'price_money': shop_item.price_money,
                'price_silver': shop_item.price_silver,
                'price_gold': shop_item.price_gold,
                'current_durability': 100,
                'max_durability': 100,
                'bonuses': {
                    'strength': item.bonus_strength,
                    'agility': item.bonus_agility,
                    'intuition': item.bonus_intuition,
                    'endurance': item.bonus_endurance,
                    'intelligence': item.bonus_intelligence,
                    'wisdom': item.bonus_wisdom,
                    'spirit': item.bonus_spirit
                },
                'requirements': {
                    'level': item.require_level,
                    'strength': item.require_strength,
                    'agility': item.require_agility,
                    'intuition': item.require_intuition,
                    'endurance': item.require_endurance,
                    'intelligence': item.require_intelligence,
                    'wisdom': item.require_wisdom,
                    'spirit': item.require_spirit
                }
            })
        
        return render(request, 'shop_panel.html', {'items': items_data})
    except Exception as e:
        logger.error(f"Error in shop_panel: {str(e)}", exc_info=True)
        return redirect('error')

@login_required
def tavern_panel(request):
    try:
        profile = PlayerProfile.objects.get(user=request.user)
        tavern_items = TavernItem.objects.filter(is_available=True, stock__gt=0)
        
        items_by_category = {}
        for item in tavern_items:
            if item.category not in items_by_category:
                items_by_category[item.category] = []
            items_by_category[item.category].append({
                'id': item.id,
                'name': item.name,
                'image': item.image.url if item.image else None,
                'price': item.price,
                'hp_restore': item.hp_restore,
                'mp_restore': item.mp_restore,
                'max_per_purchase': min(item.max_per_purchase, item.stock),
                'stock': item.stock
            })
        
        return render(request, 'tavern_panel.html', {
            'profile': profile.get_wallet_summary(),
            'items_by_category': items_by_category
        })
    except Exception as e:
        logger.error(f"Error in tavern_panel: {str(e)}", exc_info=True)
        return redirect('error')

@login_required
def arena_panel(request):
    return render(request, 'arena_panel.html')

@login_required
def combat_view(request, combat_id):
    combat = get_object_or_404(Combat, id=combat_id, owner=request.user)
    state = combat.state

    player_hp_percent = (state['player']['current_hp'] / state['player']['max_hp']) * 100
    monster_hp_percent = (state['monster']['current_hp'] / state['monster']['max_hp']) * 100

    context = {
        'combat_id': combat_id,
        'state': state,
        'player_hp_percent': player_hp_percent,
        'monster_hp_percent': monster_hp_percent,
    }
    return render(request, 'game/combat.html', context)

@login_required
def clan_panel(request):
    return render(request, 'clan_panel.html')

@login_required
@user_passes_test(is_admin)
def admin_panel(request):
    players = User.objects.select_related('playerprofile').all()
    items = Item.objects.all()
    shop_items = ShopItem.objects.select_related('item').all()
    tavern_items = TavernItem.objects.all()
    
    context = {
        'players': players,
        'items': items,
        'shop_items': shop_items,
        'tavern_items': tavern_items,
    }
    return render(request, 'admin_panel.html', context)

@login_required
def bank_panel(request):
    return render(request, 'bank_panel.html')

@login_required
def trade_panel(request):
    return render(request, 'trade_panel.html')

@login_required
@require_http_methods(["GET"])
def inventory_api(request):
    try:
        profile = PlayerProfile.objects.get(user=request.user)
        page = int(request.GET.get('page', 1))
        filter_type = request.GET.get('filter', 'all')
        subfilter = request.GET.get('subfilter', None)
        
        items_per_page = 50
        start_index = (page - 1) * items_per_page
        total_slots = profile.get_total_inventory_slots()
        
        # Получаем предметы из инвентаря
        inventory_items = InventoryItem.objects.filter(owner=profile).select_related('item')
        
        # Применяем фильтры
        if filter_type != 'all':
            inventory_items = inventory_items.filter(item__type=filter_type)
        
        if subfilter:
            inventory_items = inventory_items.filter(item__subtype=subfilter)
        
        total_items = inventory_items.count()
        total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
        
        # Получаем предметы для текущей страницы
        paginated_items = inventory_items.order_by('inventory_position')[start_index:start_index + items_per_page]
        
        # Формируем данные для ответа
        items_data = []
        for index, inv_item in enumerate(paginated_items):
            global_slot_index = start_index + index
            item_data = {
                'id': inv_item.id,
                'item_instance': {
                    'id': inv_item.id,
                    'item': {
                        'id': inv_item.item.id,
                        'name': inv_item.item.name,
                        'type': inv_item.item.type,
                        'subtype': inv_item.item.subtype,
                        'image': inv_item.item.image.url if inv_item.item.image else '/static/img/default_item.png',
                        'is_stackable': inv_item.item.is_stackable,
                        'description': inv_item.item.description,
                        'require_level': inv_item.item.require_level
                    },
                    'quantity': inv_item.quantity,
                    'current_durability': inv_item.current_durability,
                    'max_durability': inv_item.max_durability,
                    'is_equipped': inv_item.is_equipped,
                    'can_equip': inv_item.can_equip(),
                    'equipment_slot': inv_item.get_equipment_slot()
                },
                'slot_index': index,
                'global_slot_index': global_slot_index,
                'inventory_position': inv_item.inventory_position
            }
            items_data.append(item_data)
        
        return JsonResponse({
            'items': items_data,
            'total_pages': total_pages,
            'current_page': page,
            'total_items': total_items,
            'total_slots': total_slots,
            'slots_used': total_items,
            'base_slots': profile.base_inventory_slots,
            'bonus_slots': profile.bonus_inventory_slots,
            'player_level': profile.level
        })
        
    except Exception as e:
        logger.error(f"Error in inventory_api: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def shop_items_api(request):
    try:
        shop_items = ShopItem.objects.filter(is_available=True).select_related('item')
        items_data = []
        
        for shop_item in shop_items:
            item = shop_item.item
            items_data.append({
                'id': item.id,
                'name': item.name,
                'type': item.type,
                'subtype': item.subtype,
                'image': item.image.url if item.image else None,
                'price_money': shop_item.price_money,
                'price_silver': shop_item.price_silver,
                'price_gold': shop_item.price_gold,
                'current_durability': 100,
                'max_durability': 100,
                'require_level': item.require_level,
                'bonus_strength': item.bonus_strength,
                'bonus_agility': item.bonus_agility,
                # Добавьте другие поля по необходимости
            })
        
        return JsonResponse(items_data, safe=False)
    except Exception as e:
        logger.error(f"Error in shop_items_api: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def equip_item(request):
    """Надеть предмет"""
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        
        profile = PlayerProfile.objects.get(user=request.user)
        
        # Находим предмет
        try:
            item = InventoryItem.objects.get(id=item_id, owner=profile)
        except InventoryItem.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Предмет не найден'})
        
        # Проверяем, можно ли надеть
        if not item.can_equip():
            return JsonResponse({'success': False, 'message': 'Этот предмет нельзя надеть'})
        
        # Проверяем уровень
        if item.item.require_level > profile.level:
            return JsonResponse({'success': False, 'message': f'Требуется уровень {item.item.require_level}'})
        
        equipment_slot = item.get_equipment_slot()
        
        # Проверяем, не надет ли уже предмет в этот слот
        equipped_in_slot = InventoryItem.objects.filter(
            owner=profile, 
            is_equipped=True
        ).select_related('item').first()
        
        # Если есть надетый предмет в этом слоте, снимаем его
        if equipped_in_slot and equipped_in_slot.get_equipment_slot() == equipment_slot:
            equipped_in_slot.is_equipped = False
            equipped_in_slot.save()
        
        # Надеваем новый предмет
        item.is_equipped = True
        item.save()
        
        # Обновляем характеристики персонажа
        profile.update_stats_from_equipment()
        
        return JsonResponse({
            'success': True, 
            'message': f'{item.item.name} надет',
            'equipment_slot': equipment_slot
        })
        
    except Exception as e:
        logger.error(f"Error in equip_item: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@login_required
@require_http_methods(["POST"])
def unequip_item(request):
    """Снять предмет"""
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        
        profile = PlayerProfile.objects.get(user=request.user)
        
        # Находим предмет
        try:
            item = InventoryItem.objects.get(id=item_id, owner=profile, is_equipped=True)
        except InventoryItem.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Предмет не найден или не надет'})
        
        # Снимаем предмет
        item.is_equipped = False
        item.save()
        
        # Обновляем характеристики персонажа
        profile.update_stats_from_equipment()
        
        return JsonResponse({
            'success': True, 
            'message': f'{item.item.name} снят'
        })
        
    except Exception as e:
        logger.error(f"Error in unequip_item: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["GET"])
def get_messages(request):
    try:
        tab = request.GET.get('tab', 'world')
        last_id = int(request.GET.get('last_id', 0))
        
        room = ChatRoom.objects.get_or_create(
            name=tab,
            defaults={'room_type': tab}
        )[0]
        
        last_message = ChatMessage.objects.filter(
            room=room,
            id__gt=last_id
        ).order_by('-id').first()
        
        new_last_id = last_message.id if last_message else last_id
        
        messages = ChatMessage.objects.filter(
            room=room,
            id__gt=last_id,
            id__lte=new_last_id
        ).order_by('id')[:100]
        
        serialized_messages = [{
            'id': msg.id,
            'time': msg.timestamp.strftime('%H:%M'),
            'sender': msg.sender_name,
            'text': msg.message
        } for msg in messages]
        
        return JsonResponse({
            'status': 'ok',
            'messages': serialized_messages,
            'last_id': new_last_id
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def send_message(request):
    try:
        data = json.loads(request.body)
        tab = data.get('tab', 'world')
        text = data.get('text', '').strip()
        
        if not text:
            return JsonResponse({
                'status': 'error',
                'error': 'Message cannot be empty'
            }, status=400)
        
        room, created = ChatRoom.objects.get_or_create(
            name=tab,
            defaults={'room_type': tab}
        )
        
        message = ChatMessage.objects.create(
            room=room,
            user=request.user,
            sender_name=request.user.username,
            message=text
        )
        
        return JsonResponse({
            'status': 'ok',
            'message': {
                'id': message.id,
                'time': message.timestamp.strftime('%H:%M'),
                'sender': message.sender_name,
                'text': message.message
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'error': 'Internal server error'
        }, status=500)
    


@login_required
@require_http_methods(["POST"])
def tavern_purchase(request):
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = data.get('quantity', 1)
        
        profile = PlayerProfile.objects.get(user=request.user)
        item = TavernItem.objects.get(id=item_id, is_available=True, stock__gt=0)
        
        # Проверки
        if quantity < 1 or quantity > item.max_per_purchase:
            return JsonResponse({'success': False, 'message': f'Можно купить от 1 до {item.max_per_purchase} порций'})
        
        if item.stock < quantity:
            return JsonResponse({'success': False, 'message': 'Недостаточно порций в наличии'})
        
        total_price = item.price * quantity
        if profile.gold < total_price:
            return JsonResponse({'success': False, 'message': 'Недостаточно золота'})
        
        # Совершаем покупку
        with transaction.atomic():
            profile.gold -= total_price
            profile.current_hp = min(profile.current_hp + item.hp_restore * quantity, profile.max_hp)
            profile.current_mp = min(profile.current_mp + item.mp_restore * quantity, profile.max_mp)
            item.stock -= quantity
            item.save()
            profile.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Вы купили {quantity}x {item.name} за {total_price} золота',
            'new_gold': profile.gold,
            'new_hp': profile.current_hp,
            'new_mp': profile.current_mp
        })
        
    except TavernItem.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Блюдо не найдено или закончилось'}, status=404)
    except Exception as e:
        logger.error(f"Error in tavern_purchase: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'message': 'Ошибка сервера'}, status=500)
    
@login_required
@require_http_methods(["GET"])
def tavern_menu_api(request):
    try:
        tavern_items = TavernItem.objects.filter(is_available=True)
        items_by_category = {}
        
        for item in tavern_items:
            if item.category not in items_by_category:
                items_by_category[item.category] = []
            items_by_category[item.category].append({
                'id': item.id,
                'name': item.name,
                'image': item.image.url,
                'price': item.price,
                'hp_restore': item.hp_restore,
                'mp_restore': item.mp_restore,
                'effects': f"Восстанавливает: +{item.hp_restore} HP<br>+{item.mp_restore} MP",
                'max_per_purchase': min(item.max_per_purchase, item.stock),
                'stock': item.stock
            })
        
        return JsonResponse(items_by_category)
    except Exception as e:
        logger.error(f"Error in tavern_menu_api: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)
    


@login_required
@user_passes_test(is_admin)
def admin_create_test_user(request):
    # Создаём тестового админа, если его нет
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@example.com'
        )
        return render(request, 'admin_test_user_created.html')
    
    return redirect('admin_panel')

# Дополнительные функции для обработки AJAX запросов

@login_required
@user_passes_test(is_admin)
def admin_get_player_details(request, player_id):
    try:
        player = User.objects.get(id=player_id)
        profile = player.playerprofile
        
        data = {
            'id': player.id,
            'username': player.username,
            'email': player.email,
            'is_active': player.is_active,
            'profile': {
                'name': profile.name,
                'level': profile.level,
                'gold': profile.gold,
                'current_hp': profile.current_hp,
                'max_hp': profile.max_hp,
            }
        }
        return JsonResponse(data)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Player not found'}, status=404)



@require_http_methods(["POST"])
def admin_authenticate(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        user = authenticate(username=username, password=password)
        if user is not None and user.is_superuser:
            return JsonResponse({'success': True})
        return JsonResponse({'success': False})
    except Exception as e:
        logger.error(f"Error in admin_authenticate: {str(e)}", exc_info=True)
        return JsonResponse({'success': False})
    


@login_required
@user_passes_test(is_admin)
def admin_ban_player(request, player_id):
    if request.method == 'POST':
        try:
            player = User.objects.get(id=player_id)
            player.is_active = False
            player.save()
            return JsonResponse({'success': True})
        except User.DoesNotExist:
            return JsonResponse({'error': 'Player not found'}, status=404)
    return JsonResponse({'error': 'Invalid method'}, status=400)

@login_required
@user_passes_test(is_admin)
def admin_get_data(request):
    try:
        players = User.objects.select_related('playerprofile').all().values(
            'id', 'username', 'email', 'is_active', 
            'playerprofile__name', 'playerprofile__level'
        )
        
        items = Item.objects.all().values(
            'id', 'name', 'type', 'subtype', 'base_price', 'require_level'
        )
        
        shop_items = ShopItem.objects.select_related('item').all().values(
            'id', 'item__name', 'price_money', 'price_silver', 
            'price_gold', 'is_available'
        )
        
        tavern_items = TavernItem.objects.all().values(
            'id', 'name', 'category', 'price', 'hp_restore', 
            'mp_restore', 'stock', 'is_available'
        )
        
        return JsonResponse({
            'players': list(players),
            'items': list(items),
            'shop_items': list(shop_items),
            'tavern_items': list(tavern_items),
        })
    except Exception as e:
        logger.error(f"Error in admin_get_data: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)
    
@login_required
@require_http_methods(["GET"])
def online_players_api(request):
    try:
        tab = request.GET.get('tab', 'location')
        profile = PlayerProfile.objects.get(user=request.user)
        
        # Определяем временной порог для "онлайн" (последние 5 минут)
        from datetime import timedelta
        online_threshold = timezone.now() - timedelta(minutes=5)
        
        print(f"Tab: {tab}, User: {request.user.username}")
        
        # Для тестирования показываем всех игроков в базе
        players = PlayerProfile.objects.filter(
            last_online__gte=online_threshold
        ).select_related('user')[:10]  # Ограничиваем 10 игроками для теста
        
        print(f"Found {players.count()} online players")
        
        players_data = [{
            'name': player.name,
            'level': player.level,
            'classification': player.classification,
            'is_me': player.user.id == request.user.id
        } for player in players]
        
        print(f"Returning data: {players_data}")
        
        return JsonResponse({
            'players': players_data,
            'tab': tab,
            'count': len(players_data)
        })
        
    except Exception as e:
        print(f"Error in online_players_api: {str(e)}")
        logger.error(f"Error in online_players_api: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

