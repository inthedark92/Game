from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password

User = get_user_model()

class Location(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    image = models.ImageField(upload_to='locations/', null=True, blank=True)

    def __str__(self):
        return self.name

class Alliance(models.Model):
    ALLIANCE_CHOICES = [
        ('fire', 'Огонь'),
        ('water', 'Вода'),
        ('air', 'Воздух'),
        ('earth', 'Земля'),
        ('dark', 'Тьма'),
        ('light', 'Свет'),
    ]
    
    name = models.CharField(max_length=20, choices=ALLIANCE_CHOICES, unique=True)
    description = models.TextField()
    icon = models.ImageField(upload_to='alliances/')
    bonus_description = models.TextField()

    def __str__(self):
        return self.get_name_display()

class PlayerProfile(models.Model):
    CLASSIFICATION_CHOICES = [
        ('warrior', 'Воин'),
        ('mage', 'Маг'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    level = models.IntegerField(default=0)
    sublevel = models.IntegerField(default=0)
    free_stats = models.IntegerField(default=0)
    classification = models.CharField(max_length=10, choices=CLASSIFICATION_CHOICES)
    last_online = models.DateTimeField(auto_now=True)
    
    # Базовые характеристики
    strength_base = models.IntegerField(default=3)
    agility_base = models.IntegerField(default=3)
    intuition_base = models.IntegerField(default=3)
    endurance_base = models.IntegerField(default=3)
    intelligence_base = models.IntegerField(default=0)
    wisdom_base = models.IntegerField(default=0)
    spirit_base = models.IntegerField(default=0)
    
    # Модифицированные характеристики
    strength_mod = models.IntegerField(default=0)
    agility_mod = models.IntegerField(default=0)
    intuition_mod = models.IntegerField(default=0)
    endurance_mod = models.IntegerField(default=0)
    intelligence_mod = models.IntegerField(default=0)
    wisdom_mod = models.IntegerField(default=0)
    spirit_mod = models.IntegerField(default=0)
    
    # ХП/МП
    current_hp = models.IntegerField(default=0)
    max_hp = models.IntegerField(default=0)
    current_mp = models.IntegerField(default=0)
    max_mp = models.IntegerField(default=0)
    hp_regen_rate = models.IntegerField(default=1)
    mp_regen_rate = models.IntegerField(default=1)
    
    # Опыт
    experience = models.IntegerField(default=0)
    experience_to_next_level = models.IntegerField(default=1000)
    
    # Валюта
    coins = models.IntegerField(default=0)
    silver = models.IntegerField(default=0)
    silver_dust = models.IntegerField(default=0)
    gold = models.IntegerField(default=0)
    gold_dust = models.IntegerField(default=0)
    marks = models.IntegerField(default=0)
    varangian_stones = models.IntegerField(default=0)
    magic_coins = models.IntegerField(default=0)
    valknut_tokens = models.IntegerField(default=0)
    ref_coins = models.IntegerField(default=0)

    # Боевые бонусы
    phys_damage_min = models.IntegerField(default=0)
    phys_damage_max = models.IntegerField(default=0)
    crit_chance = models.IntegerField(default=0)
    dodge_chance = models.IntegerField(default=0)
    shield_block = models.IntegerField(default=0)
    parry = models.IntegerField(default=0)
    counterattack = models.IntegerField(default=0)
    armor_penetration = models.IntegerField(default=0)
    phys_absorption_percent = models.IntegerField(default=0)
    anti_crit_chance = models.FloatField(default=0)
    anti_dodge_chance = models.FloatField(default=0)
    foresight_chance = models.FloatField(default=0)
    damage_power_percent = models.IntegerField(default=0)
    crit_power = models.FloatField(default=0)
    crit_absorption_percent = models.IntegerField(default=0)

    # Магические бонусы
    magic_power = models.IntegerField(default=0)
    magic_power_fire = models.IntegerField(default=0)
    magic_power_air = models.IntegerField(default=0)
    magic_power_water = models.IntegerField(default=0)
    magic_power_earth = models.IntegerField(default=0)
    magic_power_light = models.IntegerField(default=0)
    magic_power_dark = models.IntegerField(default=0)
    magic_resist_penetration = models.IntegerField(default=0)
    magic_absorption_percent = models.IntegerField(default=0)

    # Магическая защита
    resist_fire = models.IntegerField(default=0)
    resist_air = models.IntegerField(default=0)
    resist_water = models.IntegerField(default=0)
    resist_earth = models.IntegerField(default=0)
    resist_light = models.IntegerField(default=0)
    resist_dark = models.IntegerField(default=0)

    # Физическая защита
    armor_head = models.IntegerField(default=0)
    armor_body = models.IntegerField(default=0)
    armor_waist = models.IntegerField(default=0)
    armor_legs = models.IntegerField(default=0)
    damage_resistance = models.IntegerField(default=0)
    
    # Локация
    current_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)

    # Инвентарь
    base_inventory_slots = models.IntegerField(default=500)  # Базовые слоты
    bonus_inventory_slots = models.IntegerField(default=0)   # Бонусные слоты за уровень

    # Константы
    MAX_COINS = 10000000
    MAX_SILVER = 100000
    MAX_SILVER_DUST = 100000
    MAX_GOLD = 100000
    MAX_GOLD_DUST = 100000
    
    TRANSACTION_FEE_RATES = {
        'player_to_player': 0.03,
        'resource_sale': 0.03,
        'commission_shop': 0.04,
        'bank': 0.05,   
    }
    
    RESOURCE_RATES = {
        'silver': 0.1,
        'silver_dust': 0.15,
        'gold': 0.2,
        'gold_dust': 0.25,
    }

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.pk:
            self.strength_base = 3
            self.agility_base = 3
            self.intuition_base = 3
            self.endurance_base = 3
        
        self.max_hp = self.calculate_max_hp()
        self.max_mp = self.calculate_max_mp()
        
        if self.current_hp == 0 or self.current_hp > self.max_hp:
            self.current_hp = self.max_hp
        if self.current_mp == 0 or self.current_mp > self.max_mp:
            self.current_mp = self.max_mp
            
        super().save(*args, **kwargs)

    def clean(self):
        currency_fields = [
            'coins', 'silver', 'silver_dust', 'gold', 'gold_dust',
            'marks', 'varangian_stones', 'magic_coins', 'valknut_tokens', 'ref_coins'
        ]
        for field in currency_fields:
            if getattr(self, field) < 0:
                raise ValidationError(f"{field} не может быть отрицательным")

    # Методы характеристик
    def get_total_strength(self):
        return self.strength_base + self.strength_mod
    
    def get_total_agility(self):
        return self.agility_base + self.agility_mod
    
    def get_total_intuition(self):
        return self.intuition_base + self.intuition_mod
    
    def get_total_endurance(self):
        return self.endurance_base + self.endurance_mod
    
    def get_total_intelligence(self):
        return self.intelligence_base + self.intelligence_mod
    
    def get_total_wisdom(self):
        return self.wisdom_base + self.wisdom_mod
    
    def get_total_spirit(self):
        return self.spirit_base + self.spirit_mod

    def calculate_max_hp(self):
        return (self.get_total_endurance() * 12)
    
    def calculate_max_mp(self):
        return (self.get_total_intelligence() * 40)

    def gain_experience(self, amount):
        self.experience += amount
        while self.experience >= self.experience_to_next_level:
            self.level_up()
        self.save()
    
    def level_up(self):
        self.experience -= self.experience_to_next_level
        self.level += 1
        self.sublevel = 0
        self.endurance_base += 1
        self.free_stats += 3
        self.experience_to_next_level = int(self.experience_to_next_level * 1.2)
        self.current_hp = self.max_hp
        self.current_mp = self.max_mp
        self.update_inventory_slots()
        self.save()

    def sublevel_up(self):
        if self.sublevel < 4:
            self.sublevel += 1
            self.free_stats += 1
            self.save()
            return True
        return False
    
    def distribute_stat(self, stat_name):
        if self.free_stats <= 0:
            return False
            
        base_stat = f"{stat_name}_base"
        if hasattr(self, base_stat):
            setattr(self, base_stat, getattr(self, base_stat) + 1)
            self.free_stats -= 1
            self.save()
            return True
        return False
    
    def get_total_inventory_slots(self):
        """Общее количество слотов инвентаря"""
        return self.base_inventory_slots + self.bonus_inventory_slots
    
    def update_inventory_slots(self):
        """Обновляет бонусные слоты в зависимости от уровня"""
        # +20 слотов за каждый уровень после 1-го
        new_bonus_slots = (self.level - 1) * 20
        if new_bonus_slots != self.bonus_inventory_slots:
            self.bonus_inventory_slots = max(0, new_bonus_slots)
            self.save()

    # Методы для работы с валютой
    def has_enough_currency(self, currency_type, amount):
        return getattr(self, currency_type, 0) >= amount

    def add_currency(self, currency_type, amount, description='', related_object=None):
        if currency_type not in ['coins', 'silver', 'silver_dust', 'gold', 'gold_dust']:
            return False
            
        max_attr = f"MAX_{currency_type.upper()}"
        max_value = getattr(self, max_attr, float('inf'))
        current = getattr(self, currency_type)
        new_value = current + amount
        
        if new_value > max_value:
            return False
            
        setattr(self, currency_type, new_value)
        self.save()
        
        if description or related_object:
            self._log_transaction(currency_type, amount, 'add', description, related_object)
        return True
    
    def subtract_currency(self, currency_type, amount, description='', related_object=None):
        if currency_type not in ['coins', 'silver', 'silver_dust', 'gold', 'gold_dust']:
            return False
            
        current = getattr(self, currency_type)
        if current < amount:
            return False
            
        setattr(self, currency_type, current - amount)
        self.save()
        
        if description or related_object:
            self._log_transaction(currency_type, amount, 'subtract', description, related_object)
        return True
    
    def transfer_to_player(self, target_profile, currency_type, amount, description=''):
        if currency_type not in ['coins', 'silver', 'silver_dust', 'gold', 'gold_dust']:
            return False, "Эта валюта не может быть передана"
            
        if currency_type == 'coins':
            fee = int(amount * self.TRANSACTION_FEE_RATES['player_to_player'])
            total_amount = amount + fee
            
            if not self.has_enough_currency(currency_type, total_amount):
                return False, "Недостаточно монет с учетом комиссии"
                
            if not self.subtract_currency(currency_type, amount, f"Перевод игроку {target_profile.name}"):
                return False, "Ошибка при списании средств"
                
            if fee > 0 and not self.subtract_currency('coins', fee, f"Комиссия за перевод монет"):
                self.add_currency(currency_type, amount, "Отмена перевода - ошибка комиссии")
                return False, "Ошибка при списании комиссии"
                
            target_profile.add_currency(currency_type, amount, f"Получено от {self.name}")
            
            self._log_transaction(currency_type, amount, 'transfer', f"Перевод игроку {target_profile.name}", target_profile)
            
            if fee > 0:
                self._log_transaction('coins', fee, 'fee', f"Комиссия за перевод {currency_type} игроку {target_profile.name}")
        else:
            resource_value = int(amount * self.RESOURCE_RATES[currency_type])
            fee = int(resource_value * self.TRANSACTION_FEE_RATES['resource_sale'])
            total_cost = resource_value + fee
            
            if not self.has_enough_currency(currency_type, amount):
                return False, f"Недостаточно {currency_type}"
                
            if not self.has_enough_currency('coins', fee):
                return False, "Недостаточно монет для оплаты комиссии"
                
            if not self.subtract_currency(currency_type, amount, f"Перевод {currency_type} игроку {target_profile.name}"):
                return False, f"Ошибка при списании {currency_type}"
                
            if not self.subtract_currency('coins', fee, f"Комиссия за перевод {currency_type}"):
                self.add_currency(currency_type, amount, "Отмена перевода - ошибка комиссии")
                return False, "Ошибка при списании комиссии"
                
            target_profile.add_currency(currency_type, amount, f"Получено от {self.name}")
            
            self._log_transaction(currency_type, amount, 'transfer', f"Перевод {currency_type} игроку {target_profile.name}", target_profile)
            self._log_transaction('coins', fee, 'fee', f"Комиссия за перевод {currency_type} игроку {target_profile.name}")
            
        return True, "Перевод успешно выполнен"
    
    def _log_transaction(self, currency_type, amount, transaction_type, description='', related_object=None):
        balance_after = getattr(self, currency_type)
        
        transaction = CurrencyTransaction.objects.create(
            player=self,
            currency_type=currency_type,
            amount=amount,
            transaction_type=transaction_type,
            balance_after=balance_after,
            description=description
        )
        
        if related_object:
            transaction.related_object_id = related_object.id
            transaction.related_content_type = ContentType.objects.get_for_model(related_object)
            transaction.save()
        
        return transaction

    def get_wallet_summary(self):
        return {
            'coins': self.coins,
            'silver': self.silver,
            'silver_dust': self.silver_dust,
            'gold': self.gold,
            'gold_dust': self.gold_dust,
            'marks': self.marks,
            'varangian_stones': self.varangian_stones,
            'magic_coins': self.magic_coins,
            'valknut_tokens': self.valknut_tokens,
            'ref_coins': self.ref_coins,
        }

    def get_combat_stats(self):
        return {
            'phys_damage_min': self.phys_damage_min,
            'phys_damage_max': self.phys_damage_max,
            'crit_chance': self.crit_chance,
            'dodge_chance': self.dodge_chance,
            'shield_block': self.shield_block,
            'parry': self.parry,
            'counterattack': self.counterattack,
            'armor_penetration': self.armor_penetration,
            'phys_absorption_percent': self.phys_absorption_percent,
            'anti_crit_chance': self.anti_crit_chance,
            'anti_dodge_chance': self.anti_dodge_chance,
            'foresight_chance': self.foresight_chance,
            'damage_power_percent': self.damage_power_percent,
            'crit_power': self.crit_power,
            'crit_absorption_percent': self.crit_absorption_percent,
            'armor_head': self.armor_head,
            'armor_body': self.armor_body,
            'armor_waist': self.armor_waist,
            'armor_legs': self.armor_legs,
            'damage_resistance': self.damage_resistance
        }

    def get_magic_stats(self):
        return {
            'magic_power': self.magic_power,
            'magic_power_fire': self.magic_power_fire,
            'magic_power_air': self.magic_power_air,
            'magic_power_water': self.magic_power_water,
            'magic_power_earth': self.magic_power_earth,
            'magic_power_light': self.magic_power_light,
            'magic_power_dark': self.magic_power_dark,
            'magic_resist_penetration': self.magic_resist_penetration,
            'magic_absorption_percent': self.magic_absorption_percent,
            'resist_fire': self.resist_fire,
            'resist_air': self.resist_air,
            'resist_water': self.resist_water,
            'resist_earth': self.resist_earth,
            'resist_light': self.resist_light,
            'resist_dark': self.resist_dark
        }

class PlayerClan(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    alliance = models.ForeignKey(Alliance, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    banner = models.ImageField(upload_to='clans/banners/', null=True, blank=True)
    level = models.IntegerField(default=1)
    reputation = models.IntegerField(default=0)
    min_level_to_join = models.IntegerField(default=7)
    is_recruiting = models.BooleanField(default=True)

class ModeratorClan(models.Model):
    name = models.CharField(max_length=50, unique=True, default='Совет Девяти')
    description = models.TextField(default='Официальный клан модераторов игры')
    created_at = models.DateTimeField(auto_now_add=True)
    secret_code = models.CharField(max_length=100, unique=True)

class ClanMember(models.Model):
    RANK_CHOICES = [
        ('member', 'Член'),
        ('leader', 'Глава'),
    ]
    
    clan = models.ForeignKey(PlayerClan, on_delete=models.CASCADE, related_name='members')
    player = models.OneToOneField(PlayerProfile, on_delete=models.CASCADE)
    rank = models.CharField(max_length=20, choices=RANK_CHOICES, default='member')
    join_date = models.DateTimeField(auto_now_add=True)
    contribution = models.IntegerField(default=0)

class ModeratorClanMember(models.Model):
    RANK_CHOICES = [
        ('moderator', 'Модератор'),
        ('inspector', 'Отдел проверок'),
        ('leader', 'Глава Клана'),
        ('gm', 'GM'),
    ]
    
    clan = models.ForeignKey(ModeratorClan, on_delete=models.CASCADE, related_name='members')
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rank = models.CharField(max_length=20, choices=RANK_CHOICES)
    join_date = models.DateTimeField(auto_now_add=True)
    permissions = models.JSONField(default=dict)

class PlayerVerificationRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На проверке'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    ]
    
    player = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name='verification_requests')
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    request_date = models.DateTimeField(auto_now_add=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_verifications')
    process_date = models.DateTimeField(null=True, blank=True)
    inspector_notes = models.TextField(blank=True)
    verification_code = models.CharField(max_length=50, unique=True)

class ClanJoinRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('approved', 'Принято'),
        ('rejected', 'Отклонено'),
    ]
    
    player = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name='clan_join_requests')
    clan = models.ForeignKey(PlayerClan, on_delete=models.CASCADE, related_name='join_requests')
    verification_request = models.OneToOneField(PlayerVerificationRequest, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    request_date = models.DateTimeField(auto_now_add=True)
    decision_date = models.DateTimeField(null=True, blank=True)
    decided_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

class Item(models.Model):
    ITEM_TYPES = [
        ('weapon', 'Оружие'),
        ('armor', 'Броня'),
        ('jewelry', 'Украшения'),
        ('potion', 'Зелья'),
        ('scroll', 'Свитки'),
        ('misc', 'Разное'),
    ]
    
    WEAPON_SUBTYPES = [
        ('sword', 'Мечи'),
        ('axe', 'Топоры'),
        ('dagger', 'Кинжалы'),
        ('mace', 'Дубины'),
        ('staff', 'Посохи'),
    ]
    
    ARMOR_SUBTYPES = [
        ('helmet', 'Шлемы'),
        ('chest', 'Нагрудники'),
        ('pants', 'Штаны'),
        ('short', 'Рубашка'),
        ('gloves', 'Перчатки'),
        ('bracers', 'Наручи'),
        ('boots', 'Ботинки'),
        ('belt', 'Пояса'),
        ('shield', 'Щиты'),
    ]
    
    JEWELRY_SUBTYPES = [
        ('necklace', 'Ожерелья'),
        ('earring', 'Серьги'),
        ('ring', 'Кольца'),
        ('bracelet', 'Браслеты'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    type = models.CharField(max_length=10, choices=ITEM_TYPES)
    subtype = models.CharField(max_length=10)
    image = models.ImageField(upload_to='items/', null=True, blank=True)
    is_stackable = models.BooleanField(default=False)
    max_stack = models.IntegerField(default=1)
    base_price = models.IntegerField(default=0)
    
    # Бонусы характеристик
    bonus_strength = models.IntegerField(default=0)
    bonus_agility = models.IntegerField(default=0)
    bonus_intuition = models.IntegerField(default=0)
    bonus_endurance = models.IntegerField(default=0)
    bonus_intelligence = models.IntegerField(default=0)
    bonus_wisdom = models.IntegerField(default=0)
    bonus_spirit = models.IntegerField(default=0)
    
    # Боевые бонусы
    bonus_phys_damage_min = models.IntegerField(default=0)
    bonus_phys_damage_max = models.IntegerField(default=0)
    bonus_crit_chance = models.IntegerField(default=0)
    bonus_dodge_chance = models.IntegerField(default=0)
    bonus_shield_block = models.IntegerField(default=0)
    bonus_parry = models.IntegerField(default=0)
    bonus_counterattack = models.IntegerField(default=0)
    bonus_armor_penetration = models.IntegerField(default=0)
    bonus_phys_absorption_percent = models.IntegerField(default=0)
    
    # Магические бонусы
    bonus_magic_power = models.IntegerField(default=0)
    bonus_magic_power_fire = models.IntegerField(default=0)
    bonus_magic_power_air = models.IntegerField(default=0)
    bonus_magic_power_water = models.IntegerField(default=0)
    bonus_magic_power_earth = models.IntegerField(default=0)
    bonus_magic_power_light = models.IntegerField(default=0)
    bonus_magic_power_dark = models.IntegerField(default=0)
    bonus_magic_resist_penetration = models.IntegerField(default=0)

    # Магическая защита
    bonus_resist_fire = models.IntegerField(default=0)
    bonus_resist_air = models.IntegerField(default=0)
    bonus_resist_water = models.IntegerField(default=0)
    bonus_resist_earth = models.IntegerField(default=0)
    bonus_resist_light = models.IntegerField(default=0)
    bonus_resist_dark = models.IntegerField(default=0)

    # Физическая защита
    bonus_armor_head = models.IntegerField(default=0)
    bonus_armor_body = models.IntegerField(default=0)
    bonus_armor_waist = models.IntegerField(default=0)
    bonus_armor_legs = models.IntegerField(default=0)
    bonus_damage_resistance = models.IntegerField(default=0)
    
    # Требования
    require_level = models.IntegerField(default=0)
    require_strength = models.IntegerField(default=0)
    require_agility = models.IntegerField(default=0)
    require_intuition = models.IntegerField(default=0)
    require_endurance = models.IntegerField(default=0)
    require_intelligence = models.IntegerField(default=0)
    require_wisdom = models.IntegerField(default=0)
    require_spirit = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class TavernItem(models.Model):
    CATEGORY_CHOICES = [
        ('first-course', 'Первые блюда'),
        ('second-course', 'Вторые блюда'),
        ('salads', 'Салаты'),
        ('drinks', 'Напитки'),
        ('desserts', 'Десерты'),
        ('other', 'Разное'),
    ]
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    image = models.ImageField(upload_to='tavern_items/')
    price = models.IntegerField(default=0)
    hp_restore = models.IntegerField(default=0)
    mp_restore = models.IntegerField(default=0)
    max_per_purchase = models.IntegerField(default=10)
    stock = models.IntegerField(default=100)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @property
    def in_stock(self):
        return self.stock > 0

class InventoryItem(models.Model):
    owner = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name='inventory_items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    inventory_position = models.IntegerField(default=0)  # Позиция в инвентаре (0-499)
    current_durability = models.IntegerField(default=100)
    max_durability = models.IntegerField(default=100)
    is_equipped = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['inventory_position']
    
    def __str__(self):
        return f"{self.owner.name} - {self.item.name} (x{self.quantity})"
    
    def can_equip(self):
        """Можно ли надеть предмет"""
        return self.item.type in ['weapon', 'armor', 'jewelry']
    
    def get_equipment_slot(self):
        """Возвращает слот экипировки для этого предмета"""
        item_type = self.item.type
        item_subtype = self.item.subtype
        
        if item_type == 'weapon':
            return 'weapon'
        elif item_type == 'armor':
            return item_subtype  # 'helmet', 'chest', 'gloves', etc.
        elif item_type == 'jewelry':
            return item_subtype  # 'ring', 'necklace', etc.
        return None

class ShopItem(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    price_money = models.IntegerField(default=0)
    price_silver = models.IntegerField(default=0)
    price_gold = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    stock = models.IntegerField(default=-1)
    accepts_commission = models.BooleanField(default=True)

class ChatRoom(models.Model):
    ROOM_TYPES = [
        ('world', 'Мир'),
        ('location', 'Локация'),
        ('private', 'Приват'),
        ('trade', 'Торг'),
        ('groupchat', 'Группа'),
        ('group', 'Подземный мир'),
        ('clan', 'Клан'),
        ('alliance', 'Альянс'),
    ]
    
    name = models.CharField(max_length=50)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('name', 'room_type')

class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    sender_name = models.CharField(max_length=50)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [models.Index(fields=['room', 'timestamp'])]

class AdminAccount(models.Model):
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.password)

class CurrencyTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('add', 'Пополнение'),
        ('subtract', 'Списание'),
        ('transfer', 'Перевод'),
        ('reward', 'Награда'),
        ('purchase', 'Покупка'),
        ('sale', 'Продажа'),
        ('fee', 'Комиссия'),
        ('bank_deposit', 'Банк: внесение'),
        ('bank_withdraw', 'Банк: снятие'),
        ('exchange_out', 'Обмен: отдано'),
        ('exchange_in', 'Обмен: получено'),
    ]
    
    player = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name='transactions')
    currency_type = models.CharField(max_length=20)
    amount = models.IntegerField()
    transaction_type = models.CharField(max_length=15, choices=TRANSACTION_TYPES)
    balance_after = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['player', 'timestamp']),
            models.Index(fields=['currency_type', 'transaction_type']),
        ]
    
    def __str__(self):
        return f"{self.player.name}: {self.get_transaction_type_display()} {self.amount} {self.currency_type}"




class PriceSettings(models.Model):
    RESOURCE_TYPES = [
        ('coins', 'Монеты'),
        ('gold', 'Золото'),
        ('silver', 'Серебро'),
        ('dust', 'Пыль'),
        ('stamps', 'Марки'),
    ]
    
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES, unique=True)
    min_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    average_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

class ExchangeRates(models.Model):
    RESOURCE_TYPES = [
        ('coins', 'Монеты'),
        ('silver', 'Серебро'),
        ('silver_dust', 'Серебряная пыль'),
        ('gold', 'Золото'),
        ('gold_dust', 'Золотая пыль'),
        ('stones', 'Камни'),
        ('tokens', 'Жетоны'),
    ]
    
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES, unique=True)
    rate = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('buy', 'Покупка'),
        ('sell', 'Продажа'),
    ]
    
    resource_type = models.CharField(max_length=20)
    amount = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
class Monster(models.Model):
    name = models.CharField(max_length=100)
    level = models.IntegerField(default=0)
    hp = models.IntegerField(default=100)
    strength = models.IntegerField(default=3)
    agility = models.IntegerField(default=3)
    intuition = models.IntegerField(default=3)
    endurance = models.IntegerField(default=3)
    damage_min = models.IntegerField(default=1)
    damage_max = models.IntegerField(default=5)
    crit_chance = models.IntegerField(default=5)
    dodge_chance = models.IntegerField(default=5)
    armor = models.IntegerField(default=0)
    xp_reward = models.IntegerField(default=10)
    coin_reward = models.IntegerField(default=1)
    image = models.ImageField(upload_to='monsters/', null=True, blank=True)

    def __str__(self):
        return f"{self.name} (Lvl {self.level})"

# Добавьте этот класс в конец game/models.py (после существующих моделей)
from uuid import uuid4
from django.conf import settings
from django.db import models
from django.utils import timezone

class Combat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              on_delete=models.SET_NULL, related_name='combats')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    state = models.JSONField(default=dict)  # хранит текущее состояние боя

    def __str__(self):
        return f"Combat {self.id} ({self.owner.username if self.owner else 'Anonymous'})"