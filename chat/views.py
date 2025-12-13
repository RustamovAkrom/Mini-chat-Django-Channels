from django.shortcuts import render
from rest_framework import viewsets
from .models import Chat, Message
from .serializers import ChatSerializer, MessageSerializer


def index(requests):
    return render(requests, "chat/index.html")


class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
