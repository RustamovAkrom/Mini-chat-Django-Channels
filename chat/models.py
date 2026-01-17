from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    bio = models.CharField(max_length=150, blank=True)
    online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.user.username
    

class Chat(models.Model):

    CHAT_TYPE = (
        ("private", "Private"),
        ("group", "Group"),
    )

    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=CHAT_TYPE)

    participants = models.ManyToManyField(User, related_name="chats")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or str(self.id)
    
class Message(models.Model):

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)


    text = models.TextField()

    audio = models.FileField(upload_to="voices/", null=True, blank=True)
    file = models.FileField(upload_to="files/", null=True, blank=True)

    reply_to = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text[:20]


class ChatMember(models.Model):

    ROLE_CHOICES = (
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("member", "Member"),
    )

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="member")

    class Meta:
        unique_together = ("chat", "user")
        

class PinnedMessage(models.Model):
    chat = models.OneToOneField(Chat, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)


class Reaction(models.Model):

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    emoji = models.CharField(max_length=10)

    class Meta:
        unique_together = ("message", "user", "emoji")
