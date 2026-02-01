from django.test import TestCase, Client
from django.contrib.auth.models import User
from game.models import PlayerProfile, Item, ShopItem, InventoryItem, Location
import json

class ShopPurchaseTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')

        self.location = Location.objects.create(name="Test Location", description="Test Description")
        self.profile = PlayerProfile.objects.create(
            user=self.user,
            name="TestPlayer",
            coins=1000,
            silver=1000,
            gold=1000,
            current_location=self.location
        )

        self.item = Item.objects.create(
            name="Test Item",
            description="Test Description",
            type="weapon",
            subtype="sword",
            is_stackable=False,
            base_price=100
        )

        self.shop_item = ShopItem.objects.create(
            item=self.item,
            price_money=100,
            is_available=True
        )

        self.stackable_item = Item.objects.create(
            name="Stackable Item",
            description="Stackable Description",
            type="potion",
            subtype="potion",
            is_stackable=True,
            base_price=50
        )

        self.shop_stackable_item = ShopItem.objects.create(
            item=self.stackable_item,
            price_money=50,
            price_silver=10,
            price_gold=5,
            is_available=True
        )

    def test_purchase_non_stackable(self):
        # Pre-occupy position 0
        InventoryItem.objects.create(owner=self.profile, item=self.item, inventory_position=0)

        response = self.client.post(
            '/api/shop/purchase/',
            data=json.dumps({'shop_item_id': self.shop_item.id, 'quantity': 1}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.coins, 900)

        # Check if item is in inventory and has correct position
        items = InventoryItem.objects.filter(owner=self.profile, item=self.item).order_by('inventory_position')
        self.assertEqual(items.count(), 2)
        self.assertEqual(items[0].inventory_position, 0)
        self.assertEqual(items[1].inventory_position, 1)

    def test_purchase_stackable_new(self):
        # Pre-occupy position 0 with something else
        InventoryItem.objects.create(owner=self.profile, item=self.item, inventory_position=0)

        response = self.client.post(
            '/api/shop/purchase/',
            data=json.dumps({'shop_item_id': self.shop_stackable_item.id, 'quantity': 2}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.coins, 900)
        self.assertEqual(self.profile.silver, 980)
        self.assertEqual(self.profile.gold, 990)

        # Check if item is in inventory and has correct position (should be 1)
        inv_item = InventoryItem.objects.get(owner=self.profile, item=self.stackable_item)
        self.assertEqual(inv_item.quantity, 2)
        self.assertEqual(inv_item.inventory_position, 1)

    def test_purchase_stackable_existing(self):
        # Already have some
        InventoryItem.objects.create(owner=self.profile, item=self.stackable_item, quantity=3, inventory_position=5)

        response = self.client.post(
            '/api/shop/purchase/',
            data=json.dumps({'shop_item_id': self.shop_stackable_item.id, 'quantity': 2}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Check if quantity increased
        inv_item = InventoryItem.objects.get(owner=self.profile, item=self.stackable_item)
        self.assertEqual(inv_item.quantity, 5)
        self.assertEqual(inv_item.inventory_position, 5)

    def test_insufficient_funds(self):
        self.profile.coins = 10
        self.profile.save()

        response = self.client.post(
            '/api/shop/purchase/',
            data=json.dumps({'shop_item_id': self.shop_item.id, 'quantity': 1}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Недостаточно монет', response.json()['error'])

        # Check inventory
        self.assertFalse(InventoryItem.objects.filter(owner=self.profile, item=self.item).exists())

    def test_purchase_multiple_non_stackable(self):
        response = self.client.post(
            '/api/shop/purchase/',
            data=json.dumps({'shop_item_id': self.shop_item.id, 'quantity': 3}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Check if 3 items were added
        items = InventoryItem.objects.filter(owner=self.profile, item=self.item)
        self.assertEqual(items.count(), 3)
        positions = sorted(list(items.values_list('inventory_position', flat=True)))
        self.assertEqual(positions, [0, 1, 2])
