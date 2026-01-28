from game.models import Monster

monsters_data = [
    {
        'name': 'Бродячий пес',
        'level': 0,
        'hp': 30,
        'strength': 2,
        'agility': 2,
        'intuition': 2,
        'endurance': 3,
        'damage_min': 1,
        'damage_max': 3,
        'crit_chance': 5,
        'dodge_chance': 5,
        'armor': 0,
        'xp_reward': 15,
        'coin_reward': 1
    },
    {
        'name': 'Серый волк',
        'level': 1,
        'hp': 60,
        'strength': 4,
        'agility': 4,
        'intuition': 3,
        'endurance': 5,
        'damage_min': 3,
        'damage_max': 7,
        'crit_chance': 10,
        'dodge_chance': 10,
        'armor': 1,
        'xp_reward': 30,
        'coin_reward': 2
    },
    {
        'name': 'Разбойник',
        'level': 2,
        'hp': 120,
        'strength': 6,
        'agility': 5,
        'intuition': 5,
        'endurance': 8,
        'damage_min': 5,
        'damage_max': 12,
        'crit_chance': 15,
        'dodge_chance': 12,
        'armor': 3,
        'xp_reward': 60,
        'coin_reward': 5
    },
    {
        'name': 'Огр-наемник',
        'level': 3,
        'hp': 250,
        'strength': 10,
        'agility': 3,
        'intuition': 2,
        'endurance': 15,
        'damage_min': 10,
        'damage_max': 25,
        'crit_chance': 5,
        'dodge_chance': 0,
        'armor': 5,
        'xp_reward': 150,
        'coin_reward': 15
    },
    {
        'name': 'Теневой ассасин',
        'level': 4,
        'hp': 200,
        'strength': 8,
        'agility': 15,
        'intuition': 15,
        'endurance': 10,
        'damage_min': 15,
        'damage_max': 20,
        'crit_chance': 30,
        'dodge_chance': 30,
        'armor': 2,
        'xp_reward': 300,
        'coin_reward': 30
    },
    {
        'name': 'Железный голем',
        'level': 5,
        'hp': 600,
        'strength': 20,
        'agility': 1,
        'intuition': 1,
        'endurance': 30,
        'damage_min': 30,
        'damage_max': 50,
        'crit_chance': 0,
        'dodge_chance': 0,
        'armor': 20,
        'xp_reward': 1000,
        'coin_reward': 100
    }
]

for data in monsters_data:
    Monster.objects.get_or_create(name=data['name'], level=data['level'], defaults=data)

print(f"Successfully seeded {len(monsters_data)} monsters.")
