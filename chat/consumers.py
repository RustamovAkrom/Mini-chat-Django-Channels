import json
from django.utils import timezone

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import Message, Chat


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.user = self.scope["user"]
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]

        if self.user.is_anonymous:
            await self.close()
            return

        # SECURITY: check membership
        is_member = await self.is_chat_member()

        if not is_member:
            await self.close()
            return

        self.room_group_name = f"chat_{self.chat_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # set online
        await self.set_online(True)

    async def disconnect(self, close_code):

        await self.set_online(False)

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):

        data = json.loads(text_data)

        reply_id = data.get("reply_to")

        # TYPING EVENT
        if data.get("typing"):

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_message",
                    "username": self.user.username
                }
            )

            return

        # MESSAGE EVENT
        message = data.get("message")

        if not message:
            return

        msg = await self.save_message(message, reply_id)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "msg_id": msg.id,
                "username": self.user.username,
                "message": msg.text,
                "time": msg.timestamp.strftime("%H:%M"),
            }
        )

    async def chat_message(self, event):
        await self.mark_read(event["msg_id"])
        await self.send_unread_count()

        await self.send(text_data=json.dumps({
            "id": event["msg_id"],
            "username": event["username"],
            "message": event["message"],
            "edited": False
        }))

    async def typing_message(self, event):

        await self.send(text_data=json.dumps({
            "typing": True,
            "username": event["username"]
        }))

    # =========================
    # DATABASE METHODS
    # =========================

    @database_sync_to_async
    def save_message(self, text, reply_id=None):

        chat = Chat.objects.get(id=self.chat_id)

        reply_msg = None
        if reply_id:
            reply_msg = Message.objects.get(id=reply_id)

        return Message.objects.create(
            chat=chat,
            sender=self.user,
            text=text,
            reply_to=reply_msg,
        )

    @database_sync_to_async
    def set_online(self, status):

        profile = self.user.profile
        profile.online = status

        if not status:
            profile.last_seen = timezone.now()

        profile.save()

    @database_sync_to_async
    def mark_read(self, msg_id):

        msg = Message.objects.get(id=msg_id)
        msg.is_read = True
        msg.save()

    @database_sync_to_async
    def is_chat_member(self):

        chat = Chat.objects.get(id=self.chat_id)

        return self.user in chat.participants.all()

    @database_sync_to_async
    def mark_chat_read(self):

        Message.objects.filter(
            chat_id=self.chat_id,
            is_read=False
        ).exclude(sender=self.user).update(is_read=True)


    @database_sync_to_async
    def get_unread_count(self):

        return Message.objects.filter(
            chat_id=self.chat_id,
            is_read=False
        ).exclude(sender=self.user).count()


    async def send_unread_count(self):

        count = await self.get_unread_count()

        await self.send(text_data=json.dumps({
            "unread_count": count
        }))
