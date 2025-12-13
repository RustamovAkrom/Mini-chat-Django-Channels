# 📚 Django Chat App – Документация

## 1️⃣ Требуемые модули

| Модуль                             | Зачем нужен                                           | Команда установки                 |
| ---------------------------------- | ----------------------------------------------------- | --------------------------------- |
| **django**                         | Основной фреймворк для backend                        | `pip install django`              |
| **channels**                       | Добавляет поддержку WebSocket и real-time             | `pip install channels`            |
| **channels-redis** *(опционально)* | Для масштабирования WebSocket через Redis             | `pip install channels-redis`      |
| **daphne**                         | ASGI сервер для запуска Django с WebSocket            | `pip install daphne`              |
| **djangorestframework**            | Для создания REST API (пользователи, чаты, сообщения) | `pip install djangorestframework` |

---

## 2️⃣ Структура проекта

```
config/             # основной проект Django
├─ asgi.py          # ASGI приложение, для WebSocket
├─ settings.py      # настройки проекта
├─ urls.py          # маршрутизация HTTP
chat/               # приложение chat
├─ models.py        # модели пользователей, чатов, сообщений
├─ consumers.py     # WebSocket consumer
├─ routing.py       # WebSocket роутинг
├─ views.py         # HTTP views / API views
├─ serializers.py   # DRF сериализаторы
├─ urls.py          # маршруты chat
templates/
└─ chat/index.html  # фронтенд для теста чата
manage.py
```

---

## 3️⃣ Настройка `settings.py`

```python
INSTALLED_APPS = [
    "daphne",          # Обязательно первым
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
    "rest_framework",  # DRF для API
    "chat",
]

ASGI_APPLICATION = "config.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
        # Для production заменить на Redis
        # "BACKEND": "channels_redis.core.RedisChannelLayer",
        # "CONFIG": {"hosts": [("127.0.0.1", 6379)]},
    }
}

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
```

**Объяснение:**

* `daphne` – нужен, чтобы Django мог обслуживать WebSocket
* `channels` – интегрирует WebSocket в Django
* `CHANNEL_LAYERS` – внутренний слой для обмена сообщениями между consumer’ами
* `rest_framework` – создаёт REST API для пользователей, чатов и сообщений

---

## 4️⃣ ASGI и WebSocket

**config/asgi.py**

```python
import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import chat.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(chat.routing.websocket_urlpatterns)
    ),
})
```

**Объяснение:**

* `ProtocolTypeRouter` – переключает протоколы (HTTP / WebSocket)
* `AuthMiddlewareStack` – позволяет получать `request.user` в consumer
* `URLRouter` – маршрутизация WebSocket по URL

---

## 5️⃣ WebSocket маршрутизация

**chat/routing.py**

```python
from django.urls import re_path
from .consumers import ChatConsumer

websocket_urlpatterns = [
    re_path(r"ws/chat/$", ChatConsumer.as_asgi()),
]
```

**Объяснение:**

* Любой WebSocket, подключающийся на `/ws/chat/`, попадёт в `ChatConsumer`

---

## 6️⃣ Consumer (реальный чат)

**chat/consumers.py**

```python
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "global_chat"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat_message", "message": message}
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({"message": event["message"]}))
```

**Объяснение:**

* `connect` – подписка на группу `global_chat`
* `receive` – принимает сообщения от клиента
* `chat_message` – рассылает сообщения всем в группе

---

## 7️⃣ Модели и REST API

**chat/models.py**

```python
from django.db import models
from django.contrib.auth.models import User

class Chat(models.Model):
    name = models.CharField(max_length=100)
    participants = models.ManyToManyField(User, related_name="chats")

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
```

**chat/serializers.py**

```python
from rest_framework import serializers
from .models import Chat, Message
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]

class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Message
        fields = ["id", "user", "text", "timestamp"]

class ChatSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    class Meta:
        model = Chat
        fields = ["id", "name", "messages"]
```

**chat/views.py (DRF ViewSets)**

```python
from rest_framework import viewsets
from .models import Chat, Message
from .serializers import ChatSerializer, MessageSerializer

class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
```

**chat/urls.py**

```python
from django.urls import path
from rest_framework import routers
from .views import ChatViewSet, MessageViewSet

router = routers.DefaultRouter()
router.register(r"chats", ChatViewSet)
router.register(r"messages", MessageViewSet)

urlpatterns = router.urls
```

---

## 8️⃣ Тестовый фронтенд (HTML)

**templates/chat/index.html**

```html
<input id="messageInput" type="text" placeholder="Type message">
<button onclick="sendMessage()">Send</button>
<ul id="chatLog"></ul>

<script>
const socket = new WebSocket("ws://127.0.0.1:8000/ws/chat/");
socket.onmessage = e => {
    const data = JSON.parse(e.data);
    const li = document.createElement("li");
    li.textContent = data.message;
    document.getElementById("chatLog").appendChild(li);
};
function sendMessage() {
    const input = document.getElementById("messageInput");
    socket.send(JSON.stringify({message: input.value}));
    input.value = "";
}
</script>
```

**Объяснение:**

* Пока фронтенд на Django (простая HTML-страница)
* Сообщения уходят через WebSocket → всем подключённым клиентам

---

## 9️⃣ Запуск

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

* **WS работает через Daphne**
* **REST API работает через DRF**
* В будущем можно подключить React/Next.js **к этим же API и WebSocket**
