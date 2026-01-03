# admin.py
from django.contrib import admin
from django import forms
from .models import PriceSettings, ExchangeRates, Transaction

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