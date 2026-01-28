import json
from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest, Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required

from .models import Combat, PlayerProfile
from .combat_logic import start_battle, handle_player_turn, finish_battle

@require_POST
@login_required
def api_hunt(request):
    """
    POST /api/hunt
    Запуск боя с монстром
    """
    try:
        profile = PlayerProfile.objects.get(user=request.user)
    except PlayerProfile.DoesNotExist:
        return HttpResponseBadRequest("Player profile not found")

    if profile.current_hp <= 0:
        return JsonResponse({"error": "Вы слишком слабы для боя. Подлечитесь!"}, status=400)

    # Проверяем, нет ли уже активного боя
    active_combat = Combat.objects.filter(owner=request.user, state__status='active').first()
    if active_combat:
        return JsonResponse({"combat_id": str(active_combat.id), "status": "already_in_combat"})

    combat_state = start_battle(profile)

    with transaction.atomic():
        combat = Combat.objects.create(owner=request.user, state=combat_state)

    return JsonResponse({"combat_id": str(combat.id), "state": combat_state})

@require_POST
@login_required
def api_combat_turn(request, combat_id):
    """
    POST /api/combat/<combat_id>/turn
    Обработка хода игрока
    Тело: {"attack_zone": 1, "defense_block": 1}
    """
    try:
        data = json.loads(request.body)
        attack_zone = int(data.get('attack_zone'))
        defense_block = int(data.get('defense_block'))
    except (json.JSONDecodeError, ValueError, TypeError):
        return HttpResponseBadRequest("Invalid input data")

    if not attack_zone or not defense_block:
        return JsonResponse({"error": "Выберите зону атаки и блок защиты"}, status=400)

    try:
        with transaction.atomic():
            combat_obj = Combat.objects.select_for_update().get(id=combat_id, owner=request.user)
            state = combat_obj.state

            if state.get('status') != 'active':
                return JsonResponse({"combat_id": str(combat_obj.id), "state": state, "message": "Бой уже завершен"})

            # Обработка хода
            new_state = handle_player_turn(state, attack_zone, defense_block)

            # Если бой завершился на этом ходу
            message = ""
            if new_state['status'] in ['victory', 'defeat']:
                profile = PlayerProfile.objects.get(user=request.user)
                message = finish_battle(combat_obj, profile)
                new_state['finish_message'] = message

            combat_obj.state = new_state
            combat_obj.save(update_fields=["state", "updated_at"])

    except Combat.DoesNotExist:
        raise Http404("Combat not found")

    return JsonResponse({"combat_id": str(combat_obj.id), "state": new_state, "message": message})

@require_GET
@login_required
def api_combat_state(request, combat_id):
    """
    GET /api/combat/<combat_id>/state
    Получение текущего состояния боя
    """
    combat = get_object_or_404(Combat, id=combat_id, owner=request.user)
    return JsonResponse({"combat_id": str(combat.id), "state": combat.state})
