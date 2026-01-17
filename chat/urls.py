from django.urls import path
from . import views

urlpatterns = [

    path("", views.index),

    path("login/", views.login_view),
    path("register/", views.register_view),
    path("logout/", views.logout_view),

    path("start/<str:username>/", views.start_private_chat),

    path("create-group/", views.create_group),

    path("chat/<int:chat_id>/", views.chat_room),
    path("chat/<int:chat_id>/add-user/", views.add_user_to_group),
    path("profile/avatar/", views.upload_avatar),
    path("chat/<int:chat_id>/kick/<int:user_id>/", views.kick_user),

path("upload-file/<int:chat_id>/", views.upload_file),
path("upload-voice/<int:chat_id>/", views.upload_voice),
path("react/<int:msg_id>/<str:emoji>/", views.react_message),

path("message/delete/<int:msg_id>/", views.delete_message),
path("message/edit/<int:msg_id>/", views.edit_message),

]  
