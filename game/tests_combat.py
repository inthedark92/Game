from django.test import TestCase
from django.contrib.auth import get_user_model
from game.models import PlayerProfile, Monster
from game.combat_logic import start_battle, handle_player_turn

User = get_user_model()

class CombatLogicTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.profile = PlayerProfile.objects.create(user=self.user, name='Tester', level=1)

        # Create monsters
        Monster.objects.create(name='Lvl 1 Mob', level=1, hp=50,
                              damage_min=1, damage_max=5, strength=3, agility=3)
        Monster.objects.create(name='Lvl 2 Mob', level=2, hp=100)

    def test_start_battle_level_match(self):
        # Should pick Lvl 1 Mob
        state = start_battle(self.profile)
        self.assertEqual(state['monster']['name'], 'Lvl 1 Mob')
        self.assertEqual(state['monster']['level'], 1)

    def test_turn_with_defense_zones(self):
        state = start_battle(self.profile)
        # 4 zones now, 2 defense zones
        new_state = handle_player_turn(state, attack_zone=1, defense_zones=[1, 2])
        self.assertEqual(new_state['turn'], 2)
        self.assertIn('status', new_state)

    def test_block_mechanic(self):
        from game.combat_logic import calculate_damage
        attacker_stats = {'damage_min': 10, 'damage_max': 10, 'strength': 3, 'crit_chance': 0}
        defender_stats = {'armor': 0, 'dodge_chance': 0, 'parry': 0}

        # Test hit
        dmg, res, _ = calculate_damage(attacker_stats, defender_stats, attack_zone=1, defense_zones=[2, 3])
        self.assertEqual(res, 'hit')
        self.assertEqual(dmg, 10)

        # Test block
        dmg, res, _ = calculate_damage(attacker_stats, defender_stats, attack_zone=1, defense_zones=[1, 2])
        self.assertEqual(res, 'block')
        self.assertEqual(dmg, 0)
