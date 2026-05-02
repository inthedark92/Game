from rest_framework import serializers
from .models import PlayerProfile, Item, InventoryItem, Combat, ChatMessage, Location
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

class PlayerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    current_location = LocationSerializer(read_only=True)

    class Meta:
        model = PlayerProfile
        fields = '__all__'

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'

class InventoryItemSerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)

    class Meta:
        model = InventoryItem
        fields = '__all__'

class CombatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Combat
        fields = '__all__'

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'sender_name', 'message', 'timestamp', 'is_system']
