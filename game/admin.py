# admin.py
from django.contrib import admin
from django import forms
from .models import PriceSettings, ExchangeRates, Transaction, Monster, PlayerProfile, InventoryItem, Item, ShopItem, Combat

class InventoryItemInline(admin.TabularInline):
    model = InventoryItem
    extra = 1

class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'user', 'coins', 'silver', 'gold']
    search_fields = ['name', 'user__username']
    inlines = [InventoryItemInline]
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'name', 'level', 'sublevel', 'free_stats', 'classification', 'current_location')
        }),
        ('Currencies', {
            'fields': ('coins', 'silver', 'silver_dust', 'gold', 'gold_dust', 'marks', 'varangian_stones', 'magic_coins', 'valknut_tokens', 'ref_coins')
        }),
        ('Stats (Base)', {
            'fields': ('strength_base', 'agility_base', 'intuition_base', 'endurance_base', 'intelligence_base', 'wisdom_base', 'spirit_base')
        }),
        ('HP/MP', {
            'fields': ('current_hp', 'max_hp', 'current_mp', 'max_mp', 'hp_regen_rate', 'mp_regen_rate')
        }),
    )

admin.site.register(PlayerProfile, PlayerProfileAdmin)
admin.site.register(Item)
admin.site.register(InventoryItem)
admin.site.register(ShopItem)
admin.site.register(Combat)

class MonsterAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'hp', 'xp_reward', 'coin_reward']
    list_filter = ['level']
    search_fields = ['name']

admin.site.register(Monster, MonsterAdmin)

class PriceSettingsAdmin(admin.ModelAdmin):
    list_display = ['resource_type', 'min_price', 'max_price', 'average_price', 'updated_at']
    list_editable = ['min_price', 'max_price']
    readonly_fields = ['average_price', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        # Автоматический пересчет средней цены при сохранении
        transactions = Transaction.objects.filter(resource_type=obj.resource_type)
        if transactions.exists():
            total_price = sum(t.price for t in transactions)
            obj.average_price = total_price / transactions.count()
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
        
        # Обновляем среднюю цену для данного типа ресурса
        try:
            price_settings = PriceSettings.objects.get(resource_type=obj.resource_type)
            transactions = Transaction.objects.filter(resource_type=obj.resource_type)
            if transactions.exists():
                total_price = sum(t.price for t in transactions)
                price_settings.average_price = total_price / transactions.count()
                price_settings.save()
        except PriceSettings.DoesNotExist:
            pass

admin.site.register(PriceSettings, PriceSettingsAdmin)
admin.site.register(ExchangeRates, ExchangeRatesAdmin)
admin.site.register(Transaction, TransactionAdmin)