from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Chat, Message, ChatMember, PinnedMessage, Reaction
from .utils import get_or_create_private_chat
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


@login_required
def index(request):

    chats = request.user.chats.all()

    q = request.GET.get("q")

    users = []
    groups = []

    if q:
        users = User.objects.filter(username__icontains=q).exclude(id=request.user.id)
        groups = Chat.objects.filter(type="group", name__icontains=q)

    return render(request, "chat/index.html", {
        "chats": chats,
        "users": users,
        "groups": groups
    })

@login_required
def upload_avatar(request):

    if request.method == "POST":

        avatar = request.FILES.get("avatar")

        if not avatar:
            return redirect("/profile/avatar/")

        profile = request.user.profile
        profile.avatar = avatar
        profile.save()

        return redirect("/")

    return render(request, "chat/avatar.html")



@login_required
def start_private_chat(request, username):

    try:
        other_user = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect("/")

    chat = get_or_create_private_chat(request.user, other_user)

    return redirect(f"/chat/{chat.id}/")


@login_required
def create_group(request):

    if request.method == "POST":

        name = request.POST["name"]

        chat = Chat.objects.create(
            name=name,
            type="group"
        )

        chat.participants.add(request.user)

        ChatMember.objects.create(
            chat=chat,
            user=request.user,
            role="owner"
        )

        return redirect(f"/chat/{chat.id}/")

    return render(request, "chat/create_group.html")


@login_required
def chat_room(request, chat_id):

    chat = Chat.objects.get(id=chat_id)

    if request.user not in chat.participants.all():
        return redirect("/")

    messages = chat.messages.all().order_by("timestamp")

    members = ChatMember.objects.filter(chat=chat)

    return render(request, "chat/chat.html", {
        "chat": chat,
        "messages": messages,
        "members": members
    })


def login_view(request):

    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect("/")

    return render(request, "chat/login.html")


def register_view(request):

    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]

        User.objects.create_user(username=username, password=password)

        return redirect("/login/")

    return render(request, "chat/register.html")


def logout_view(request):

    logout(request)
    return redirect("/login/")


@login_required
def add_user_to_group(request, chat_id):

    chat = Chat.objects.get(id=chat_id)

    # защита
    if request.user not in chat.participants.all():
        return redirect("/")

    if chat.type != "group":
        return redirect("/")

    if request.method == "POST":

        username = request.POST["username"]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return redirect(f"/chat/{chat_id}/")

        # не добавляем дубликат
        if user in chat.participants.all():
            return redirect(f"/chat/{chat_id}/")

        chat.participants.add(user)

        # создаём запись в ChatMember (если ещё нет)
        ChatMember.objects.get_or_create(chat=chat, user=user, defaults={"role": "member"})

        # системное сообщение: кто добавил и кого добавили
        Message.objects.create(
            chat=chat,
            sender=request.user,
            text=f"{user.username} joined the group"
        )

    return redirect(f"/chat/{chat_id}/")


@login_required
def kick_user(request, chat_id, user_id):

    chat = Chat.objects.get(id=chat_id)

    me = ChatMember.objects.get(chat=chat, user=request.user)

    if me.role not in ["owner", "admin"]:
        return redirect(f"/chat/{chat_id}/")

    user = User.objects.get(id=user_id)

    chat.participants.remove(user)

    ChatMember.objects.filter(chat=chat, user=user).delete()

    Message.objects.create(
        chat=chat,
        sender=request.user,
        text=f"{user.username} was removed from group"
    )

    return redirect(f"/chat/{chat_id}/")


@login_required
def delete_message(request, msg_id):

    msg = Message.objects.get(id=msg_id)

    if msg.sender != request.user:
        return redirect("/")

    msg.is_deleted = True
    msg.save()

    return redirect(request.META.get("HTTP_REFERER"))


@login_required
def edit_message(request, msg_id):

    msg = Message.objects.get(id=msg_id)

    if msg.sender != request.user:
        return redirect("/")

    if request.method == "POST":
        msg.text = request.POST["text"]
        msg.save()

    return redirect(request.META.get("HTTP_REFERER"))


@login_required
def pin_message(request, msg_id):

    msg = Message.objects.get(id=msg_id)

    PinnedMessage.objects.update_or_create(
        chat=msg.chat,
        defaults={"message": msg}
    )

    return redirect(f"/chat/{msg.chat.id}/")


@login_required
def upload_file(request, chat_id):

    if request.method == "POST" and request.FILES.get("file"):

        file = request.FILES["file"]
        chat = Chat.objects.get(id=chat_id)

        msg = Message.objects.create(
            chat=chat,
            sender=request.user,
            file=file
        )

        # SEND WS EVENT
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"chat_{chat_id}",
            {
                "type": "chat_message",
                "msg_id": msg.id,
                "username": request.user.username,
                "message": f"📎 File: {file.name}",
            }
        )

    return redirect(f"/chat/{chat_id}/")


@login_required
def upload_voice(request, chat_id):

    if request.method == "POST" and request.FILES.get("audio"):

        audio = request.FILES["audio"]
        chat = Chat.objects.get(id=chat_id)

        msg = Message.objects.create(
            chat=chat,
            sender=request.user,
            audio=audio
        )

        # SEND WS EVENT
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"chat_{chat_id}",
            {
                "type": "chat_message",
                "msg_id": msg.id,
                "username": request.user.username,
                "message": "🎤 Voice message",
            }
        )

    return redirect(f"/chat/{chat_id}/")


@login_required
def react_message(request, msg_id, emoji):

    msg = Message.objects.get(id=msg_id)

    Reaction.objects.get_or_create(
        message=msg,
        user=request.user,
        emoji=emoji
    )

    return redirect(f"/chat/{msg.chat.id}/")
