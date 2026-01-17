from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

def index(requests):
    if not requests.user.is_authenticated:
        return redirect("login")
    return render(requests, "chat/index.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect("/")
        
    return render(request, "chat/login.html")
    

def register_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        User.objects.create_user(username=username, password=password)
        return redirect("login")
    
    return render(request, "chat/register.html")


def logout_view(request):
    logout(request)
    return redirect("login")
