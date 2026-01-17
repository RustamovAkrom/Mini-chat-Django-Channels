import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message, Chat


class ChatConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return
        
        self.room_group_name = "global_chat"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]

        msg = await self.save_message(message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": msg.text,
                "username": self.user.get_username()
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "username": event["username"]
        }))

    @database_sync_to_async
    def save_message(self, text):

        chat, _ = Chat.objects.get_or_create(name="global")

        return Message.objects.create(
            chat=chat,
            sender=self.user,
            text=text
        )
    
    # async def disconnect(self, close_code):
    #     await self.channel_layer.group_discard(
    #         self.room_group_name,
    #         self.channel_name
    #     )

