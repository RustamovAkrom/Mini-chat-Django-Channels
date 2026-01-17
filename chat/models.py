from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    bio = models.CharField(max_length=150, blank=True)
    online = models.BooleanField(default=False)

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
    is_read = models.BooleanField(default=False)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text[:20]
