import json
import random
from uuid import uuid4

from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest, Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required

from .models import Combat, PlayerProfile

# ---------- Утилиты ----------
def make_player_from_profile(profile, overrides=None):
    # строим сущность игрока для боя на основе PlayerProfile
    overrides = overrides or {}
    return {
        "id": str(overrides.get("id") or f"player-{profile.user_id}"),
        "name": overrides.get("name") or profile.name,
        "hp": int(overrides.get("hp", profile.current_hp or profile.max_hp or 100)),
        "atk": int(overrides.get("atk", max(1, getattr(profile, 'phys_damage_min', 5)))),
        "def": int(overrides.get("def", getattr(profile, 'phys_defense', 0))),
        "speed": int(overrides.get("speed", getattr(profile, 'agility_base', 5))),
        "is_player": True,
    }

def make_monster(template, idx=0):
    return {
        "id": str(uuid4()),
        "name": f"{template['name']}" + (f" #{idx+1}" if idx else ""),
        "hp": template["hp"],
        "atk": template["atk"],
        "def": template.get("def", 0),
        "speed": template.get("speed", 8),
        "is_player": False,
    }

def generate_monsters(difficulty=1):
    templates = [
        {"name": "Гоблин", "hp": 30 * difficulty, "atk": 6 * difficulty, "def": 1, "speed": 8},
        {"name": "Волк", "hp": 45 * difficulty, "atk": 8 * difficulty, "def": 2, "speed": 12},
        {"name": "Огр",   "hp": 80 * difficulty, "atk": 14 * difficulty, "def": 4, "speed": 6},
    ]
    count = 1 + random.randint(0, 2)
    return [make_monster(random.choice(templates), i) for i in range(count)]

# ---------- Инициатива и создание состояния ----------
def roll_initiative(entity):
    return entity.get("speed", 0) + (1 + random.randint(0, 19))

def create_combat_state(player_entity, monster_entities, monsters_start=False, resolve_first_monster_turn=False):
    participants = [player_entity] + monster_entities
    by_init = [{"entity": p, "init": roll_initiative(p)} for p in participants]
    by_init.sort(key=lambda x: x["init"], reverse=True)

    if monsters_start:
        first_monster_index = next((i for i, x in enumerate(by_init) if not x["entity"].get("is_player")), None)
        if first_monster_index is not None and first_monster_index > 0:
            by_init = by_init[first_monster_index:] + by_init[:first_monster_index]

    turn_order = [x["entity"]["id"] for x in by_init]
    entities_by_id = {p["id"]: dict(p) for p in participants}

    combat = {
        "entities_by_id": entities_by_id,
        "turn_order": turn_order,
        "current_turn_index": 0,
        "log": [],
        "finished": False,
        "winner": None,
    }

    if resolve_first_monster_turn and monsters_start:
        take_turn(combat)

    return combat

# ---------- Боевая логика ----------
def apply_damage(target, dmg):
    target["hp"] = max(0, target.get("hp", 0) - dmg)

def choose_target(attacker, combat):
    entities = [e for e in combat["entities_by_id"].values() if e.get("hp", 0) > 0]
    if attacker.get("is_player"):
        for e in entities:
            if not e.get("is_player"):
                return e
        return None
    else:
        for e in entities:
            if e.get("is_player"):
                return e
        return None

def calc_damage(attacker, defender):
    base = max(1, attacker.get("atk", 1) - defender.get("def", 0))
    rand = random.randint(0, 5)
    return base + rand

def check_combat_end(combat):
    any_players_alive = any(e.get("hp", 0) > 0 and e.get("is_player") for e in combat["entities_by_id"].values())
    any_monsters_alive = any(e.get("hp", 0) > 0 and not e.get("is_player") for e in combat["entities_by_id"].values())
    if not any_players_alive:
        combat["finished"] = True
        combat["winner"] = "monsters"
        combat["log"].append("Монстры победили.")
    elif not any_monsters_alive:
        combat["finished"] = True
        combat["winner"] = "players"
        combat["log"].append("Игрок победил.")

def advance_index(combat):
    if not combat["turn_order"]:
        combat["finished"] = True
        return
    combat["current_turn_index"] = (combat["current_turn_index"] + 1) % len(combat["turn_order"])

def take_turn(combat):
    if combat.get("finished"):
        return
    if not combat.get("turn_order"):
        combat["finished"] = True
        return

    combat["current_turn_index"] %= len(combat["turn_order"])
    start_index = combat["current_turn_index"]
    found = False
    for i in range(len(combat["turn_order"])):
        idx = (start_index + i) % len(combat["turn_order"])
        actor_id = combat["turn_order"][idx]
        actor = combat["entities_by_id"].get(actor_id)
        if actor and actor.get("hp", 0) > 0:
            combat["current_turn_index"] = idx
            found = True
            break
    if not found:
        combat["finished"] = True
        check_combat_end(combat)
        return

    actor_id = combat["turn_order"][combat["current_turn_index"]]
    actor = combat["entities_by_id"].get(actor_id)
    if not actor or actor.get("hp", 0) <= 0:
        combat["log"].append(f"({actor_id}) пропускает ход (мертв/отсутствует).")
        advance_index(combat)
        check_combat_end(combat)
        return

    target = choose_target(actor, combat)
    if not target:
        combat["log"].append(f"{actor.get('name','Неизвестный')} не нашёл цель.")
        advance_index(combat)
        check_combat_end(combat)
        return

    dmg = calc_damage(actor, target)
    apply_damage(target, dmg)
    combat["log"].append(f"{actor.get('name','?')} наносит {dmg} урона {target.get('name','?')} (HP {target.get('hp')}).")

    check_combat_end(combat)
    if not combat.get("finished"):
        advance_index(combat)

# ---------- Сериализация ----------
def serialize_combat(combat):
    return {
        "entities": list(combat["entities_by_id"].values()),
        "turn_order": combat["turn_order"],
        "current_turn_index": combat["current_turn_index"],
        "log": combat["log"][-50:],
        "finished": combat["finished"],
        "winner": combat.get("winner"),
    }

# ---------- Views (API) ----------
@require_POST
@login_required
def api_hunt(request):
    """
    POST /api/hunt
    Тело (JSON, опционально): { "player": {...}, "difficulty":1, "monsters_start":true, "resolve_first_monster_turn":false }
    """
    try:
        payload = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    try:
        profile = PlayerProfile.objects.get(user=request.user)
    except PlayerProfile.DoesNotExist:
        return HttpResponseBadRequest("Player profile not found")

    player_data = payload.get("player", {})
    player = make_player_from_profile(profile, overrides=player_data)
    difficulty = int(payload.get("difficulty", 1))
    monsters_start = bool(payload.get("monsters_start", True))
    resolve_first = bool(payload.get("resolve_first_monster_turn", False))

    monsters = generate_monsters(difficulty=difficulty)
    combat_state = create_combat_state(player, monsters, monsters_start=monsters_start, resolve_first_monster_turn=resolve_first)

    with transaction.atomic():
        combat = Combat.objects.create(owner=request.user, state=combat_state)

    return JsonResponse({"combat_id": str(combat.id), "state": serialize_combat(combat_state)})

@require_POST
@login_required
def api_combat_turn(request, combat_id):
    """
    POST /api/combat/<combat_id>/turn
    Выполнить один ход (блокировка с select_for_update).
    """
    try:
        with transaction.atomic():
            combat_obj = Combat.objects.select_for_update().get(id=combat_id, owner=request.user)
            state = combat_obj.state or {}
            if state.get("finished"):
                return JsonResponse({"combat_id": str(combat_obj.id), "state": serialize_combat(state)})

            take_turn(state)

            combat_obj.state = state
            combat_obj.save(update_fields=["state", "updated_at"])
    except Combat.DoesNotExist:
        raise Http404("Combat not found")

    return JsonResponse({"combat_id": str(combat_obj.id), "state": serialize_combat(state)})

@require_GET
@login_required
def api_combat_state(request, combat_id):
    combat = get_object_or_404(Combat, id=combat_id, owner=request.user)
    return JsonResponse({"combat_id": str(combat.id), "state": serialize_combat(combat.state or {})})