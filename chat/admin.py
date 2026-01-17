from django.contrib import admin
from .models import Chat, Message, Profile


admin.site.register([Chat, Message, Profile])
