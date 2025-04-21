import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import GroupMessage, Group, GroupCall

class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.group_name = f'group_{self.group_id}'
        self.user = self.scope['user']

        # Check if user is member of the group
        if isinstance(self.user, AnonymousUser) or not await self.is_group_member():
            await self.close()
            return

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

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        if message.strip():
            # Save message to database
            group_message = await self.create_group_message(message)
            
            # Send message to group
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender': self.user.username,
                    'timestamp': group_message.timestamp.strftime('%H:%M'),
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def is_group_member(self):
        return Group.objects.filter(
            id=self.group_id,
            members=self.user
        ).exists()

    @database_sync_to_async
    def create_group_message(self, content):
        group = Group.objects.get(id=self.group_id)
        return GroupMessage.objects.create(
            group=group,
            sender=self.user,
            content=content
        )

class GroupCallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.call_id = self.scope['url_route']['kwargs']['call_id']
        self.call_name = f'call_{self.call_id}'
        self.user = self.scope['user']

        # Check if user is member of the group
        if isinstance(self.user, AnonymousUser) or not await self.is_call_participant():
            await self.close()
            return

        await self.channel_layer.group_add(
            self.call_name,
            self.channel_name
        )
        await self.accept()

        # Notify others that user joined
        await self.channel_layer.group_send(
            self.call_name,
            {
                'type': 'call_notification',
                'message': f'{self.user.username} joined the call',
                'user_id': self.user.id,
                'action': 'join',
            }
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_send(
            self.call_name,
            {
                'type': 'call_notification',
                'message': f'{self.user.username} left the call',
                'user_id': self.user.id,
                'action': 'leave',
            }
        )
        await self.channel_layer.group_discard(
            self.call_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'signal':
            await self.channel_layer.group_send(
                self.call_name,
                {
                    'type': 'call_signal',
                    'sender_id': self.user.id,
                    'signal': data['signal'],
                    'target': data.get('target'),
                }
            )

    async def call_signal(self, event):
        if event['target'] and event['target'] != self.user.id:
            return

        await self.send(text_data=json.dumps({
            'action': 'signal',
            'sender_id': event['sender_id'],
            'signal': event['signal'],
        }))

    async def call_notification(self, event):
        await self.send(text_data=json.dumps({
            'action': 'notification',
            'message': event['message'],
            'user_id': event['user_id'],
            'action_type': event['action'],
        }))

    @database_sync_to_async
    def is_call_participant(self):
        return GroupCall.objects.filter(
            id=self.call_id,
            group__members=self.user
        ).exists()