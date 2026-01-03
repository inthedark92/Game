from django.db import models, transaction
from django.contrib.auth.models import User
from decimal import Decimal
from django.db.models.signals import post_migrate
from django.dispatch import receiver


class CharacterProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    name = models.CharField(max_length=50, default='Новый Игрок')
    level = models.PositiveIntegerField(default=1)
    experience = models.BigIntegerField(default=0)
    experience_to_next_level = models.BigIntegerField(default=20)

    # Классификация будет вычисляться автоматически
    _classification = models.CharField(max_length=30, db_column='classification', editable=False)
    clan = models.CharField(max_length=50, blank=True, null=True)

    @property
    def classification(self):
        """Автоматически определяет класс на основе характеристик"""
        if not hasattr(self, 'stats'):
            return 'warrior'  # Значение по умолчанию
            
        stats = self.stats
        # Если интеллект и мудрость значительно выше других характеристик - маг
        if (stats.total_intelligence() + stats.total_wisdom()) > \
           (stats.total_strength() + stats.total_agility() + stats.total_endurance() + 10):
            return 'mage'
        return 'warrior'

    @classification.setter
    def classification(self, value):
        """Запрещаем прямое изменение классификации"""
        raise AttributeError("Classification is determined automatically based on stats")

    def __str__(self):
        return f"{self.name} (ур. {self.level})"

    def recalculate_all_modifiers(self):
        """Пересчитывает все модификаторы персонажа без ограничений"""
        if not hasattr(self, 'stats') or not hasattr(self, 'combat_stats') or not hasattr(self, 'magic_stats') or not hasattr(self, 'resources'):
            return

        stats = self.stats
        combat = self.combat_stats
        magic = self.magic_stats
        resources = self.resources

        # Получаем базовые характеристики
        strength = stats.total_strength()
        agility = stats.total_agility()
        intuition = stats.total_intuition()
        endurance = stats.total_endurance()
        intelligence = stats.total_intelligence()
        wisdom = stats.total_wisdom()
        spirit = stats.total_spirit()

        # Боевые модификаторы БЕЗ ограничений
        combat.phys_damage_min = max(1, strength)
        combat.phys_damage_max = max(2, strength + 2)
        combat.crit_chance = 8.0 * strength  # Без ограничения 100%
        combat.anticrit_chance = 7.66 * agility
        combat.dodge_chance = 8.0 * agility
        combat.antidodge_chance = 7.66 * intuition
        combat.damage_resistance = f"0d{max(1, endurance // 3)}"

        # Дополнительные боевые модификаторы
        combat.damage_power_percent = strength * 2.5
        combat.crit_damage_power_percent = strength * 1.5 + agility * 1.0
        combat.shield_block = endurance * 1.2
        combat.parry = agility * 1.5
        combat.counterattack = intuition * 1.8
        combat.foresight = intuition * 2.0
        combat.armor_penetration = strength * 0.8
        combat.phys_absorption_percent = endurance * 0.5
        combat.crit_absorption_percent = endurance * 0.3 + agility * 0.2

        # Сбрасываем значения брони
        for part in ['head', 'body', 'waist', 'legs']:
            setattr(combat, f'armor_{part}', '0d0')

        combat.save()

        # Магические модификаторы (только для магов)
        if self.classification == 'mage':
            magic.magic_power = intelligence * 3.0 + wisdom * 2.0
            magic.magic_resistance = wisdom * 2.5 + spirit * 1.5
            magic.magic_absorption_percent = wisdom * 0.8
            magic.magic_resist_penetration = intelligence * 1.2
        else:
            # Для воинов магические характеристики минимальны
            magic.magic_power = 0.0
            magic.magic_resistance = wisdom * 0.5  # Небольшая естественная сопротивляемость
            magic.magic_absorption_percent = 0.0
            magic.magic_resist_penetration = 0.0

        # Сбрасываем остальные магические показатели
        for element in ['fire', 'air', 'water', 'earth', 'light', 'dark']:
            setattr(magic, f'magic_power_{element}', 0.0)
            setattr(magic, f'resist_{element}', 0.0)

        magic.save()

        # Пересчитываем ресурсы
        resources.recalculate()


class CharacterStats(models.Model):
    character = models.OneToOneField(CharacterProfile, on_delete=models.CASCADE, related_name='stats')

    strength_base = models.PositiveIntegerField(default=3)
    strength_mod = models.IntegerField(default=0)

    agility_base = models.PositiveIntegerField(default=3)
    agility_mod = models.IntegerField(default=0)

    intuition_base = models.PositiveIntegerField(default=3)
    intuition_mod = models.IntegerField(default=0)

    endurance_base = models.PositiveIntegerField(default=3)
    endurance_mod = models.IntegerField(default=0)

    intelligence_base = models.PositiveIntegerField(default=0)
    intelligence_mod = models.IntegerField(default=0)

    wisdom_base = models.PositiveIntegerField(default=0)
    wisdom_mod = models.IntegerField(default=0)

    spirit_base = models.PositiveIntegerField(default=0)
    spirit_mod = models.IntegerField(default=0)

    def total_strength(self):
        return max(0, self.strength_base + self.strength_mod)

    def total_agility(self):
        return max(0, self.agility_base + self.agility_mod)

    def total_intuition(self):
        return max(0, self.intuition_base + self.intuition_mod)

    def total_endurance(self):
        return max(0, self.endurance_base + self.endurance_mod)

    def total_intelligence(self):
        return max(0, self.intelligence_base + self.intelligence_mod)

    def total_wisdom(self):
        return max(0, self.wisdom_base + self.wisdom_mod)

    def total_spirit(self):
        return max(0, self.spirit_base + self.spirit_mod)

    def __str__(self):
        return f"Статы {self.character.name}"


class CharacterResources(models.Model):
    character = models.OneToOneField(CharacterProfile, on_delete=models.CASCADE, related_name='resources')

    current_hp = models.PositiveIntegerField(default=0)
    max_hp = models.PositiveIntegerField(default=0)

    current_mp = models.PositiveIntegerField(default=0)
    max_mp = models.PositiveIntegerField(default=0)

    hp_regen_percent = models.FloatField(default=50.0)
    mp_regen_percent = models.FloatField(default=0.0)

    def recalculate(self):
        stats = self.character.stats
        total_endurance = stats.total_endurance()
        
        # Рассчитываем максимальное HP
        self.max_hp = max(1, total_endurance * 12)
        self.current_hp = min(self.current_hp, self.max_hp)

        # Рассчитываем максимальное MP в зависимости от класса
        if self.character.classification == 'mage':
            total_intelligence = stats.total_intelligence()
            total_wisdom = stats.total_wisdom()
            self.max_mp = max(0, (total_intelligence * 20) + (total_wisdom * 15))
        else:
            self.max_mp = 0
        
        self.current_mp = min(self.current_mp, self.max_mp)
        
        # Регенерация
        if self.character.classification == 'mage':
            self.mp_regen_percent = stats.total_wisdom() * 2.5
        else:
            self.mp_regen_percent = 0.0
            
        self.hp_regen_percent = stats.total_endurance() * 1.8
        
        self.save()

    def __str__(self):
        return f"Ресурсы {self.character.name}"



class CharacterCombatStats(models.Model):
    character = models.OneToOneField(CharacterProfile, on_delete=models.CASCADE, related_name='combat_stats')

    phys_damage_min = models.PositiveIntegerField(default=3)
    phys_damage_max = models.PositiveIntegerField(default=5)
    damage_power_percent = models.FloatField(default=0.0)
    crit_damage_power_percent = models.FloatField(default=0.0)

    crit_chance = models.FloatField(default=0.0)
    anticrit_chance = models.FloatField(default=0.0)
    dodge_chance = models.FloatField(default=0.0)
    antidodge_chance = models.FloatField(default=0.0)

    shield_block = models.FloatField(default=0.0)
    parry = models.FloatField(default=0.0)
    counterattack = models.FloatField(default=0.0)

    foresight = models.FloatField(default=0.0)
    armor_penetration = models.FloatField(default=0.0)

    armor_head = models.CharField(max_length=10, default='0d0')
    armor_body = models.CharField(max_length=10, default='0d0')
    armor_waist = models.CharField(max_length=10, default='0d0')
    armor_legs = models.CharField(max_length=10, default='0d0')
    damage_resistance = models.CharField(max_length=10, default='0d1')

    phys_absorption_percent = models.FloatField(default=0.0)
    crit_absorption_percent = models.FloatField(default=0.0)

    def __str__(self):
        return f"Боевые модификаторы {self.character.name}"


class CharacterMagicStats(models.Model):
    character = models.OneToOneField(CharacterProfile, on_delete=models.CASCADE, related_name='magic_stats')

    magic_power = models.FloatField(default=0.0)
    magic_power_fire = models.FloatField(default=0.0)
    magic_power_air = models.FloatField(default=0.0)
    magic_power_water = models.FloatField(default=0.0)
    magic_power_earth = models.FloatField(default=0.0)
    magic_power_light = models.FloatField(default=0.0)
    magic_power_dark = models.FloatField(default=0.0)

    magic_resistance = models.FloatField(default=0.0)
    resist_fire = models.FloatField(default=0.0)
    resist_air = models.FloatField(default=0.0)
    resist_water = models.FloatField(default=0.0)
    resist_earth = models.FloatField(default=0.0)
    resist_light = models.FloatField(default=0.0)
    resist_dark = models.FloatField(default=0.0)

    magic_absorption_percent = models.FloatField(default=0.0)
    magic_resist_penetration = models.FloatField(default=0.0)

    def __str__(self):
        return f"Магические модификаторы {self.character.name}"


class PlayerLocation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    current_location = models.CharField(max_length=50, default='market')
    current_zone = models.CharField(max_length=50, blank=True, null=True)
    last_online = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.current_location}"

    class Meta:
        verbose_name = "Локация игрока"
        verbose_name_plural = "Локации игроков"


class CharacterWallet(models.Model):
    character = models.OneToOneField(CharacterProfile, on_delete=models.CASCADE, related_name='wallet')

    coins = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'), verbose_name="Монеты (кр.)")
    silver = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'), verbose_name="Серебро (гр.)")
    silver_dust = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'), verbose_name="Серебряная пыль (гр.)")
    gold = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'), verbose_name="Золото (гр.)")
    gold_dust = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'), verbose_name="Золотая пыль (гр.)")

    marks = models.PositiveIntegerField(default=0, verbose_name="Марки (шт.)")
    varangian_stones = models.PositiveIntegerField(default=0, verbose_name="Варяжские Камни (шт.)")
    magic_coins = models.PositiveIntegerField(default=0, verbose_name="Волшебные Монеты (шт.)")

    valknut_tokens = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'), verbose_name="Жетоны Валькнут (шт.)")
    ref_coins = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'), verbose_name="Монеты Наставника (шт.)")

    class Meta:
        verbose_name = "Кошелёк персонажа"
        verbose_name_plural = "Кошельки персонажей"

    def __str__(self):
        return f"Кошелёк {self.character.name}"

    def add_currency(self, currency_field: str, amount: Decimal, description: str = ''):
        """
        Добавить указанную сумму валюты.
        Проверяет, что поле существует и сумма положительная.
        """
        if not hasattr(self, currency_field):
            raise ValueError(f"Поле валюты {currency_field} не существует")
            
        if amount <= 0:
            raise ValueError("Сумма для добавления должна быть положительной")

        with transaction.atomic():
            current = getattr(self, currency_field)
            setattr(self, currency_field, current + amount)
            self.save(update_fields=[currency_field])
            CharacterWalletTransaction.objects.create(
                wallet=self,
                currency=currency_field,
                amount=amount,
                description=description,
            )

    def spend_currency(self, currency_field: str, amount: Decimal, description: str = ''):
        """
        Списать указанную сумму валюты, если достаточно средств.
        Проверяет, что поле существует и сумма положительная.
        """
        if not hasattr(self, currency_field):
            raise ValueError(f"Поле валюты {currency_field} не существует")
            
        if amount <= 0:
            raise ValueError("Сумма для списания должна быть положительной")

        with transaction.atomic():
            current = getattr(self, currency_field)
            if current < amount:
                raise ValueError("Недостаточно средств")
            setattr(self, currency_field, current - amount)
            self.save(update_fields=[currency_field])
            CharacterWalletTransaction.objects.create(
                wallet=self,
                currency=currency_field,
                amount=-amount,
                description=description,
            )


class CharacterWalletTransaction(models.Model):
    wallet = models.ForeignKey(CharacterWallet, on_delete=models.CASCADE, related_name='transactions')
    currency = models.CharField(max_length=30, verbose_name="Валюта")
    amount = models.DecimalField(max_digits=20, decimal_places=2, verbose_name="Сумма")
    description = models.CharField(max_length=255, blank=True, verbose_name="Описание операции")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата операции")

    class Meta:
        verbose_name = "Транзакция кошелька"
        verbose_name_plural = "Транзакции кошельков"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.wallet.character.name}: {self.currency} {self.amount} at {self.created_at}"



class ItemSubType(models.Model):
    code = models.CharField(max_length=50, unique=True)  # 'sword', 'axe', 'body', 'pants'
    name = models.CharField(max_length=100)  # "Меч", "Топор", "Тело", "Штаны"
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Тип предмета"
        verbose_name_plural = "Типы предметов"

    def __str__(self):
        return self.name




PREDEFINED_SUBTYPES = [
    # Оружие
    {'type_code': 'weapon', 'code': 'sword', 'name': 'Меч'},
    {'type_code': 'weapon', 'code': 'axe', 'name': 'Топор'},
    {'type_code': 'weapon', 'code': 'dagger', 'name': 'Кинжал'},
    {'type_code': 'weapon', 'code': 'mace', 'name': 'Дубина'},
    {'type_code': 'weapon', 'code': 'club', 'name': 'Булава'},
    {'type_code': 'weapon', 'code': 'staff', 'name': 'Посох'},
    
    # Броня
    {'type_code': 'armor', 'code': 'helmet', 'name': 'Шлем'},
    {'type_code': 'armor', 'code': 'chest', 'name': 'Нагрудник'},
    {'type_code': 'armor', 'code': 'shirt', 'name': 'Рубашка'},
    {'type_code': 'armor', 'code': 'legs', 'name': 'Поножи'},
    {'type_code': 'armor', 'code': 'pants', 'name': 'Штаны'},
    {'type_code': 'armor', 'code': 'bracer', 'name': 'Наручи'},
    {'type_code': 'armor', 'code': 'gloves', 'name': 'Перчатки'},
    {'type_code': 'armor', 'code': 'belt', 'name': 'Пояс'},
    {'type_code': 'armor', 'code': 'boots', 'name': 'Ботинки'},
    {'type_code': 'armor', 'code': 'shield', 'name': 'Щит'},
    
    # Украшения
    {'type_code': 'jewelry', 'code': 'necklace', 'name': 'Ожерелье'},
    {'type_code': 'jewelry', 'code': 'amulet', 'name': 'Амулет'},
    {'type_code': 'jewelry', 'code': 'earring', 'name': 'Серьга'},
    {'type_code': 'jewelry', 'code': 'bracelet', 'name': 'Браслет'},
    {'type_code': 'jewelry', 'code': 'ring', 'name': 'Кольцо'},
    
    # Прочее
    {'type_code': 'other', 'code': 'potion', 'name': 'Зелье'},
    {'type_code': 'other', 'code': 'elixir', 'name': 'Эликсир'},
    {'type_code': 'other', 'code': 'gift', 'name': 'Подарок'},
    {'type_code': 'other', 'code': 'misc', 'name': 'Разное'},
]

@receiver(post_migrate)
def create_initial_data(sender, **kwargs):
    """Создает начальные подтипы после миграций."""
    if sender.name == 'accounts':
        with transaction.atomic():
            for subtype_data in PREDEFINED_SUBTYPES:
                ItemSubType.objects.get_or_create(
                    code=subtype_data['code'],
                    defaults={'name': subtype_data['name']}
                ) 


class EquipmentSlot(models.Model):
    code = models.CharField(max_length=50, unique=True)  # 'main_hand', 'head', 'body', etc.
    name = models.CharField(max_length=100)  # "Правая рука", "Голова", "Тело"

    def __str__(self):
        return self.name


class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='items/icons/', null=True, blank=True)

    subtype = models.ForeignKey(ItemSubType, on_delete=models.CASCADE,null=True)
    slot = models.ForeignKey(EquipmentSlot, on_delete=models.SET_NULL, null=True, blank=True)

    require_level = models.PositiveIntegerField(default=0, verbose_name="Требуемый уровень")
    
    # Требования к базовым характеристикам
    require_strength = models.PositiveIntegerField(default=0)
    require_agility = models.PositiveIntegerField(default=0)
    require_intuition = models.PositiveIntegerField(default=0)
    require_endurance = models.PositiveIntegerField(default=0)
    require_intelligence = models.PositiveIntegerField(default=0)
    require_wisdom = models.PositiveIntegerField(default=0)
    require_spirit = models.PositiveIntegerField(default=0)

    # Бонусы к характеристикам (stats)
    bonus_strength = models.IntegerField(default=0)
    bonus_agility = models.IntegerField(default=0)
    bonus_intuition = models.IntegerField(default=0)
    bonus_endurance = models.IntegerField(default=0)
    bonus_intelligence = models.IntegerField(default=0)
    bonus_wisdom = models.IntegerField(default=0)
    bonus_spirit = models.IntegerField(default=0)

    # Бонусы к боевым характеристикам
    bonus_phys_damage_min = models.IntegerField(default=0)
    bonus_phys_damage_max = models.IntegerField(default=0)
    bonus_crit_chance = models.FloatField(default=0.0)
    bonus_dodge_chance = models.FloatField(default=0.0)
    bonus_shield_block = models.FloatField(default=0.0)
    bonus_parry = models.FloatField(default=0.0)
    bonus_counterattack = models.FloatField(default=0.0)
    bonus_armor_penetration = models.FloatField(default=0.0)
    bonus_phys_absorption_percent = models.FloatField(default=0.0)

    # Магические бонусы
    bonus_magic_power = models.FloatField(default=0.0)
    bonus_magic_power_fire = models.FloatField(default=0.0)
    bonus_magic_power_air = models.FloatField(default=0.0)
    bonus_magic_power_water = models.FloatField(default=0.0)
    bonus_magic_power_earth = models.FloatField(default=0.0)
    bonus_magic_power_light = models.FloatField(default=0.0)
    bonus_magic_power_dark = models.FloatField(default=0.0)

    bonus_resist_fire = models.FloatField(default=0.0)
    bonus_resist_air = models.FloatField(default=0.0)
    bonus_resist_water = models.FloatField(default=0.0)
    bonus_resist_earth = models.FloatField(default=0.0)
    bonus_resist_light = models.FloatField(default=0.0)
    bonus_resist_dark = models.FloatField(default=0.0)
    bonus_magic_resist_penetration = models.FloatField(default=0.0)

    # Абсорбция урона
    bonus_magic_absorption_percent = models.FloatField(default=0.0)
    bonus_crit_absorption_percent = models.FloatField(default=0.0)

    durability = models.PositiveIntegerField(default=0, verbose_name="Прочность")
    max_durability = models.PositiveIntegerField(
        verbose_name="Макс. прочность",
        help_text="Максимальное значение прочности для этого предмета",
        default=0
    )
    current_durability = models.PositiveIntegerField(
        verbose_name="Текущая прочность",
        help_text="Текущее значение прочности (для инстансов предметов)",
        blank=True,
        null=True,
        editable=True
    )

    # Цены в разных валютах (из ShopItem)
    price_money = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Цена в монетах')
    price_silver = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Цена в серебре')
    price_silver_dust = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Цена в серебряной пыли')
    price_gold = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Цена в золоте')
    price_gold_dust = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Цена в золотой пыли')
    
    is_active_in_shop = models.BooleanField(default=False, verbose_name='Доступно для продажи в магазине')


    @property
    def durability_display(self):
        """Отображение прочности в формате 'текущая/макс.'"""
        if self.current_durability is not None:
            return f"{self.current_durability}/{self.max_durability}"
        return f"0/{self.max_durability}"

    def save(self, *args, **kwargs):
        # При первом сохранении устанавливаем current_durability равным max_durability
        if self.current_durability is None:
            self.current_durability = self.max_durability
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



    @property
    def price_display(self):
        """Отображение цены в виде строки"""
        prices = []
        if self.price_money > 0:
            prices.append(f"{self.price_money} монет")
        if self.price_silver > 0:
            prices.append(f"{self.price_silver} (гр)серебра")
        if self.price_gold > 0:
            prices.append(f"{self.price_gold} (гр)золота")

        return ", ".join(prices) if prices else "Бесплатно"
    

    
class ShopItem(models.Model):
    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name='shop_item')
    is_active = models.BooleanField(default=True, verbose_name='Активно в магазине')
    
    def __str__(self):
        return f"Магазин: {self.item.name}"
    
    class Meta:
        verbose_name = "Товар магазина"
        verbose_name_plural = "Товары магазина"