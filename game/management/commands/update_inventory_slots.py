# management/commands/update_inventory_slots.py
from django.core.management.base import BaseCommand
from game.models import PlayerProfile

class Command(BaseCommand):
    help = 'Update inventory slots for existing players'
    
    def handle(self, *args, **options):
        players = PlayerProfile.objects.all()
        for player in players:
            player.update_inventory_slots()
            self.stdout.write(f'Updated {player.name}: level {player.level}, slots {player.get_total_inventory_slots()}')