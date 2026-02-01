from django.contrib import admin
from .models import (
    PriceSettings, ExchangeRates, Transaction, Monster, PlayerProfile,
    InventoryItem, Item, ShopItem, Combat, TavernItem, ChatRoom, ChatMessage,
    Alliance, PlayerClan, ClanMember, CurrencyTransaction
)

class InventoryItemInline(admin.TabularInline):
    model = InventoryItem
    fields = ['item', 'is_equipped', 'equipped_slot', 'quantity', 'durability_current', 'durability_max']
    extra = 1

class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'user', 'coins', 'silver', 'gold']
    search_fields = ['name', 'user__username']
    inlines = [InventoryItemInline]
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'name', 'level', 'sublevel', 'free_stats', 'classification')
        }),
        ('Currencies', {
            'fields': ('coins', 'silver', 'silver_dust', 'gold', 'gold_dust', 'marks', 'varangian_stones', 'magic_coins', 'valknut_tokens', 'ref_coins')
        }),
        ('Stats (Base)', {
            'fields': ('strength_base', 'agility_base', 'intuition_base', 'endurance_base', 'intelligence_base', 'wisdom_base', 'spirit_base')
        }),
        ('HP/MP', {
            'fields': ('current_hp', 'max_hp', 'current_mp', 'max_mp', 'hp_regen_rate', 'mp_regen_rate', 'last_resource_update')
        }),
    )

class MonsterAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'hp', 'xp_reward_min', 'xp_reward_max', 'coin_reward']
    list_filter = ['level']
    search_fields = ['name']

class ItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'subtype', 'is_quest', 'require_level', 'base_price']
    list_filter = ['type', 'subtype', 'is_quest', 'require_level']
    search_fields = ['name']

class ShopItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'item', 'price_money', 'price_silver', 'price_gold', 'is_available', 'stock']
    list_filter = ['is_available']
    search_fields = ['item__name']

class TavernItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'hp_restore', 'mp_restore', 'stock', 'is_available']
    list_filter = ['category', 'is_available']
    search_fields = ['name']

class PriceSettingsAdmin(admin.ModelAdmin):
    list_display = ['resource_type', 'min_price', 'max_price', 'average_price', 'updated_at']
    list_editable = ['min_price', 'max_price']
    readonly_fields = ['average_price', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        from django.db.models import Avg
        transactions = Transaction.objects.filter(resource_type=obj.resource_type)
        if transactions.exists():
            obj.average_price = transactions.aggregate(Avg('price'))['price__avg'] or 0
        super().save_model(request, obj, form, change)

class ExchangeRatesAdmin(admin.ModelAdmin):
    list_display = ['resource_type', 'rate', 'updated_at']
    list_editable = ['rate']

class TransactionAdmin(admin.ModelAdmin):
    list_display = ['resource_type', 'amount', 'price', 'total', 'transaction_type', 'created_at']
    list_filter = ['resource_type', 'transaction_type', 'created_at']
    readonly_fields = ['created_at']
    
    def save_model(self, request, obj, form, change):
        obj.total = obj.amount * obj.price
        super().save_model(request, obj, form, change)
        
        from django.db.models import Avg
        try:
            price_settings = PriceSettings.objects.get(resource_type=obj.resource_type)
            transactions = Transaction.objects.filter(resource_type=obj.resource_type)
            if transactions.exists():
                price_settings.average_price = transactions.aggregate(Avg('price'))['price__avg'] or 0
                price_settings.save()
        except PriceSettings.DoesNotExist:
            pass

class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['owner', 'item', 'is_equipped', 'equipped_slot', 'quantity']
    list_filter = ['is_equipped', 'equipped_slot']
    search_fields = ['owner__name', 'item__name']

# Register models
admin.site.register(PlayerProfile, PlayerProfileAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(InventoryItem, InventoryItemAdmin)
admin.site.register(ShopItem, ShopItemAdmin)
admin.site.register(Combat)
admin.site.register(TavernItem, TavernItemAdmin)
admin.site.register(ChatRoom)
admin.site.register(ChatMessage)
admin.site.register(Alliance)
admin.site.register(PlayerClan)
admin.site.register(ClanMember)
admin.site.register(CurrencyTransaction)
admin.site.register(Monster, MonsterAdmin)
admin.site.register(PriceSettings, PriceSettingsAdmin)
admin.site.register(ExchangeRates, ExchangeRatesAdmin)
admin.site.register(Transaction, TransactionAdmin)
