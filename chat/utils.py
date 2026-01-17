from .models import Chat

def get_or_create_private_chat(user1, user2):
    chats = Chat.objects.filter(type="private", participants=user1).filter(participants=user2)

    if chats.exists():
        return chats.first()
    
    chat = Chat.objects.create(type="private")
    chat.participants.add(user1, user2)

    return chat

