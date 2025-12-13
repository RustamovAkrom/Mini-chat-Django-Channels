from django.urls import path
from rest_framework import routers
from .views import ChatViewSet, MessageViewSet

from . import views


router = routers.DefaultRouter()
router.register(r"chats", ChatViewSet)
router.register(r"messages", MessageViewSet)

urlpatterns = [path("", views.index, name="index")]
urlpatterns += router.urls
