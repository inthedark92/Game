import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, ChatMessage
from django.contrib.auth.models import User

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        username = self.scope['user'].username if self.scope['user'].is_authenticated else 'Anonymous'

        # Save to DB
        await self.save_message(username, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username']
        }))

    @database_sync_to_async
    def save_message(self, username, message):
        room, _ = ChatRoom.objects.get_or_create(name=self.room_name, defaults={'room_type': 'world'})
        user = User.objects.filter(username=username).first()
        ChatMessage.objects.create(room=room, user=user, sender_name=username, message=message)

class CombatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.combat_id = self.scope['url_route']['kwargs']['combat_id']
        self.group_name = f'combat_{self.combat_id}'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def combat_update(self, event):
        await self.send(text_data=json.dumps(event['state']))
