import random
from django.utils import timezone
from .npc_templates import MONSTER_TEMPLATES
from .models import PlayerProfile, InventoryItem, Combat, CurrencyTransaction, Monster

ZONES = {
    1: "Голова",
    2: "Корпус",
    3: "Пояс",
    4: "Ноги"
}

def start_battle(player_profile):
    """Инициализация боя с монстром"""
    # Ищем подходящих монстров по уровню игрока
    monsters = Monster.objects.filter(level=player_profile.level)

    if not monsters.exists():
        # Если нет монстров ровно этого уровня, ищем ближайших
        monsters = Monster.objects.filter(level__lte=player_profile.level).order_by('-level')
        if not monsters.exists():
            # Совсем нет монстров - используем шаблон
            monster_template = random.choice(MONSTER_TEMPLATES)
        else:
            # Берем случайного из монстров с максимальным уровнем <= уровня игрока
            max_lvl = monsters[0].level
            monsters = monsters.filter(level=max_lvl)
            monster_obj = random.choice(monsters)
            monster_template = monster_to_dict(monster_obj)
    else:
        monster_obj = random.choice(monsters)
        monster_template = monster_to_dict(monster_obj)

    # Копия монстра для боя
    monster = monster_template.copy()
    monster['current_hp'] = monster['hp']
    monster['max_hp'] = monster['hp']

    player_data = {
        'id': player_profile.user.id,
        'name': player_profile.name,
        'level': player_profile.level,
        'current_hp': player_profile.current_hp,
        'max_hp': player_profile.max_hp,
        'stats': player_profile.get_combat_stats(),
        'strength': player_profile.get_total_strength(),
        'agility': player_profile.get_total_agility(),
        'intuition': player_profile.get_total_intuition(),
        'total_damage_dealt': 0,
    }

    # Считаем количество ударов (по количеству оружия)
    equipped_weapons = InventoryItem.objects.filter(owner=player_profile, is_equipped=True, item__type='weapon').count()
    player_data['num_attacks'] = max(1, equipped_weapons)

    combat_state = {
        'player': player_data,
        'monster': monster,
        'log': ['Бой начался!'],
        'status': 'active', # active, victory, defeat
        'turn': 1,
        'winner': None
    }

    return combat_state

def calculate_damage(attacker_stats, defender_stats, attack_zone, defense_zones):
    """Расчет результата одного удара"""
    # attack_zone: 1..4
    # defense_zones: list of blocked zones (e.g. [1, 2])

    damage = 0
    result_type = "hit" # hit, crit, dodge, block, parry, miss

    # Получаем список заблокированных зон
    blocked_zones = defense_zones or []

    # 1. Промах (базовый шанс 5%)
    if random.randint(1, 100) <= 5:
        return 0, "miss", "Промахнулся"

    # 2. Уворот (зависит от ловкости защитника)
    dodge_chance = defender_stats.get('dodge_chance', 0)
    if random.randint(1, 100) <= dodge_chance:
        return 0, "dodge", "Увернулся"

    # 3. Парирование (шанс парирования)
    parry_chance = defender_stats.get('parry', 0)
    if random.randint(1, 100) <= parry_chance:
        return 0, "parry", "Парировал"

    # 4. Блок
    if attack_zone in blocked_zones:
        result_type = "block"
        return 0, "block", "Заблокировано"

    # 5. Крит (зависит от удачи/интуиции)
    is_crit = False
    crit_chance = attacker_stats.get('crit_chance', 0)
    if random.randint(1, 100) <= crit_chance:
        is_crit = True
        result_type = "crit"

    # 6. Урон
    base_damage = random.randint(attacker_stats.get('damage_min', 1), attacker_stats.get('damage_max', 5))
    # Бонус от силы: +10% за каждую единицу силы выше 3
    strength = attacker_stats.get('strength', 3)
    damage = base_damage * (1 + (max(0, strength - 3) * 0.1))

    if is_crit:
        damage *= 2

    # Вычитаем броню
    armor_keys = {1: 'armor_head', 2: 'armor_body', 3: 'armor_waist', 4: 'armor_legs'}
    armor_attr = armor_keys.get(attack_zone, 'armor')
    # Monsters have flat armor, players have zone-specific armor
    if armor_attr in defender_stats:
        armor = defender_stats[armor_attr]
    else:
        armor = defender_stats.get('armor', 0)
    damage = max(1, damage - armor)

    return int(damage), result_type, ""

def handle_player_turn(combat_state, attack_zone, defense_zones):
    """Обработка хода игрока"""
    if not isinstance(defense_zones, list) or len(defense_zones) != 2:
        # Fallback to default defense if invalid
        defense_zones = [1, 2]

    player = combat_state['player']
    monster = combat_state['monster']

    # AI монстра для этого хода
    npc_attack_zone, npc_defense_zones = handle_npc_turn(monster)

    # 1. Игрок бьет монстра
    player_attacks = player.get('num_attacks', 1)
    for i in range(player_attacks):
        dmg, res, _ = calculate_damage(
            attacker_stats={
                'damage_min': player['stats']['phys_damage_min'],
                'damage_max': player['stats']['phys_damage_max'],
                'crit_chance': player['stats']['crit_chance'],
                'strength': player['strength'],
                'intuition': player['intuition']
            },
            defender_stats={
                'armor': monster['armor'],
                'dodge_chance': monster['dodge_chance'],
                'agility': monster['agility']
            },
            attack_zone=attack_zone,
            defense_zones=npc_defense_zones
        )
        monster['current_hp'] = max(0, monster['current_hp'] - dmg)
        player['total_damage_dealt'] += dmg

        msg = f"Игрок ударил {ZONES[attack_zone]} монстра"
        if res == "crit": msg += " (КРИТ)"
        elif res == "block": msg += " (БЛОК)"
        elif res == "dodge": msg = "Монстр увернулся от удара игрока"
        elif res == "parry": msg = "Монстр парировал удар игрока"
        elif res == "miss": msg = "Игрок промахнулся"

        if res not in ["dodge", "parry", "miss"]:
            msg += f" на -{dmg} HP. [{monster['current_hp']}/{monster['max_hp']}]"

        combat_state['log'].append(msg)

        if monster['current_hp'] <= 0:
            break

    # Проверка смерти монстра
    if monster['current_hp'] <= 0:
        combat_state['status'] = 'victory'
        combat_state['winner'] = 'player'
        combat_state['log'].append("Монстр повержен!")
        return combat_state

    # 2. Монстр бьет игрока
    dmg, res, _ = calculate_damage(
        attacker_stats={
            'damage_min': monster['damage_min'],
            'damage_max': monster['damage_max'],
            'crit_chance': monster['crit_chance'],
            'strength': monster['strength'],
            'intuition': monster['intuition']
        },
        defender_stats={
            'armor_head': player['stats']['armor_head'],
            'armor_body': player['stats']['armor_body'],
            'armor_waist': player['stats']['armor_waist'],
            'armor_legs': player['stats']['armor_legs'],
            'dodge_chance': player['stats']['dodge_chance'],
            'agility': player['agility']
        },
        attack_zone=npc_attack_zone,
        defense_zones=defense_zones
    )
    player['current_hp'] = max(0, player['current_hp'] - dmg)

    msg = f"Монстр ударил {ZONES[npc_attack_zone]} игрока"
    if res == "crit": msg += " (КРИТ)"
    elif res == "block": msg += " (БЛОК)"
    elif res == "dodge": msg = "Игрок увернулся от удара монстра"
    elif res == "parry": msg = "Вы парировали удар монстра"
    elif res == "miss": msg = "Монстр промахнулся"

    if res not in ["dodge", "parry", "miss"]:
        msg += f" на -{dmg} HP. [{player['current_hp']}/{player['max_hp']}]"

    combat_state['log'].append(msg)

    # Проверка смерти игрока
    if player['current_hp'] <= 0:
        combat_state['status'] = 'defeat'
        combat_state['winner'] = 'monster'
        combat_state['log'].append("Вы проиграли...")

    combat_state['turn'] += 1
    return combat_state

def monster_to_dict(monster_obj):
    """Преобразование модели Monster в словарь для состояния боя"""
    return {
        'name': monster_obj.name,
        'level': monster_obj.level,
        'hp': monster_obj.hp,
        'strength': monster_obj.strength,
        'agility': monster_obj.agility,
        'intuition': monster_obj.intuition,
        'endurance': monster_obj.endurance,
        'damage_min': monster_obj.damage_min,
        'damage_max': monster_obj.damage_max,
        'crit_chance': monster_obj.crit_chance,
        'dodge_chance': monster_obj.dodge_chance,
        'armor': monster_obj.armor,
        'xp_reward': monster_obj.xp_reward,
        'coin_reward': monster_obj.coin_reward
    }

def handle_npc_turn(monster):
    """AI монстра: выбор атаки и защиты"""
    attack_zone = random.randint(1, 4)
    # Выбор 2 уникальных зон для защиты
    defense_zones = random.sample(range(1, 5), 2)
    return attack_zone, defense_zones

def handle_flee(combat_state):
    """Попытка сбежать из боя"""
    # Шанс побега 50%
    if random.random() < 0.5:
        combat_state['status'] = 'fled'
        combat_state['log'].append("Вы успешно сбежали из боя!")
        return True
    else:
        combat_state['log'].append("Вам не удалось сбежать!")
        return False

def finish_battle(combat_obj, player_profile):
    """Завершение боя и выдача наград"""
    state = combat_obj.state
    if state['status'] == 'victory':
        xp = state['monster'].get('xp_reward', 10)
        gold = state['monster'].get('coin_reward', 5)

        player_profile.gain_experience(xp)
        player_profile.coins += gold
        player_profile.current_hp = state['player']['current_hp']
        player_profile.save()

        # Лог транзакции
        CurrencyTransaction.objects.create(
            player=player_profile,
            currency_type='coins',
            amount=gold,
            transaction_type='reward',
            balance_after=player_profile.coins,
            description=f"Награда за победу над {state['monster']['name']}"
        )

        return f"Победа! Получено {xp} опыта и {gold} монет."
    elif state['status'] == 'defeat':
        player_profile.current_hp = 1 # Оставляем 1 HP после поражения
        player_profile.save()
        return "Поражение. Вы были тяжело ранены."

    return "Бой завершен."
