import random
from django.utils import timezone
from .npc_templates import MONSTER_TEMPLATES
from .models import PlayerProfile, InventoryItem, Combat, CurrencyTransaction

ZONES = {
    1: "Голова",
    2: "Грудь",
    3: "Живот",
    4: "Пояс",
    5: "Ноги"
}

# Маппинг блоков защиты (один выбор покрывает 3 зоны)
BLOCK_SETS = {
    1: [1, 2, 3], # блок головы, груди и живота
    2: [2, 3, 4], # блок груди, живота и пояса
    3: [3, 4, 5], # блок живота, пояса и ног
    4: [4, 5, 1], # блок пояса, ног и головы
    5: [5, 1, 2]  # блок ног, головы и груди
}

def start_battle(player_profile):
    """Инициализация боя с монстром"""
    monster_template = random.choice(MONSTER_TEMPLATES)

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

def calculate_damage(attacker_stats, defender_stats, attack_zone, defense_block_id):
    """Расчет результата одного удара"""
    # attack_zone: 1..5
    # defense_block_id: 1..5 (выбор блока)

    damage = 0
    result_type = "hit" # hit, crit, dodge, block, parry, miss

    # Получаем список заблокированных зон
    blocked_zones = BLOCK_SETS.get(defense_block_id, [])

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

    if result_type == "block":
        # В OldBK блок полностью поглощает урон или значительно снижает.
        # Упростим: блок снижает урон на 75%
        damage *= 0.25

    # Вычитаем броню
    armor_keys = {1: 'armor_head', 2: 'armor_body', 3: 'armor_body', 4: 'armor_waist', 5: 'armor_legs'}
    armor = defender_stats.get(armor_keys.get(attack_zone, 'armor'), 0)
    damage = max(1, damage - armor)

    return int(damage), result_type, ""

def handle_player_turn(combat_state, attack_zone, defense_block_id):
    """Обработка хода игрока"""
    player = combat_state['player']
    monster = combat_state['monster']

    # AI монстра для этого хода
    npc_attack_zone, npc_defense_block_id = handle_npc_turn(monster)

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
            defense_block_id=npc_defense_block_id
        )
        monster['current_hp'] = max(0, monster['current_hp'] - dmg)

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
        defense_block_id=defense_block_id
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

def handle_npc_turn(monster):
    """AI монстра: выбор атаки и защиты"""
    attack_zone = random.randint(1, 5)
    defense_block_id = random.randint(1, 5)
    return attack_zone, defense_block_id

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
