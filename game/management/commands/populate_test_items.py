from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from game.models import PlayerProfile, Item, InventoryItem

class Command(BaseCommand):
    help = 'Populate test items for players'
    
    def handle(self, *args, **options):
        self.stdout.write('Starting to populate test items...')
        
        # Создаем тестовые предметы если их нет
        test_items_data = [
            {
                'name': 'Стальной меч',
                'type': 'weapon',
                'subtype': 'sword',
                'description': 'Простой стальной меч',
                'bonus_strength': 2,
                'bonus_phys_damage_min': 5,
                'bonus_phys_damage_max': 10,
                'require_level': 1
            },
            {
                'name': 'Кожаный доспех',
                'type': 'armor', 
                'subtype': 'chest',
                'description': 'Кожаный нагрудник',
                'bonus_endurance': 1,
                'bonus_armor_body': 3,
                'require_level': 1
            },
            {
                'name': 'Малое зелье здоровья',
                'type': 'potion',
                'subtype': 'battle',
                'description': 'Восстанавливает 50 HP',
                'is_stackable': True,
                'max_stack': 10,
                'require_level': 0
            },
            {
                'name': 'Деревянный щит',
                'type': 'armor',
                'subtype': 'shield', 
                'description': 'Простой деревянный щит',
                'bonus_endurance': 1,
                'bonus_shield_block': 5,
                'require_level': 1
            },
            {
                'name': 'Кожаные перчатки',
                'type': 'armor',
                'subtype': 'gloves',
                'description': 'Кожаные перчатки',
                'bonus_agility': 1,
                'require_level': 1
            },
            {
                'name': 'Железный шлем',
                'type': 'armor',
                'subtype': 'helmet',
                'description': 'Простой железный шлем',
                'bonus_endurance': 1,
                'bonus_armor_head': 2,
                'require_level': 1
            }
        ]
        
        created_count = 0
        for item_data in test_items_data:
            item, created = Item.objects.get_or_create(
                name=item_data['name'],
                defaults=item_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Создан предмет: {item.name}'))
                created_count += 1
            else:
                self.stdout.write(f'✓ Предмет уже существует: {item.name}')
        
        # Добавляем предметы всем игрокам
        players = PlayerProfile.objects.all()
        if not players:
            self.stdout.write(self.style.WARNING('⚠ Нет игроков для добавления предметов'))
            return
            
        for player in players:
            self.stdout.write(f'Добавляем предметы игроку: {player.name}')
            
            # Очищаем старые предметы (опционально)
            InventoryItem.objects.filter(owner=player).delete()
            
            # Добавляем предметы в позиции 0, 1, 2, 3, 4, 5
            items_to_add = [
                ('Стальной меч', 0),
                ('Кожаный доспех', 1),
                ('Малое зелье здоровья', 2),
                ('Деревянный щит', 3),
                ('Кожаные перчатки', 4),
                ('Железный шлем', 5)
            ]
            
            for item_name, position in items_to_add:
                try:
                    item_obj = Item.objects.get(name=item_name)
                    inv_item = InventoryItem.objects.create(
                        owner=player,
                        item=item_obj,
                        inventory_position=position,
                        quantity=3 if item_obj.is_stackable else 1,
                        current_durability=100,
                        max_durability=100
                    )
                    self.stdout.write(f'  ✓ Добавлен: {item_obj.name} в позицию {position}')
                except Item.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'  ✗ Предмет "{item_name}" не найден'))
        
        self.stdout.write(self.style.SUCCESS(
            f'✅ Готово! Создано {created_count} предметов, добавлены предметы {players.count()} игрокам'
        ))