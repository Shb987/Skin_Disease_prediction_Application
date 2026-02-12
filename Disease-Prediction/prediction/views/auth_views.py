from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User


# --------------------------
# AUTH VIEWS
# --------------------------

def register_view(request): 
    if request.method == "POST":
        username = request.POST.get("username").strip()
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirmPassword")

        if not username or not password:
            messages.error(request, "Please fill in all required fields.")
            return render(request, "register.html")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, "register.html")

        User.objects.create_user(username=username, password=password)
        messages.success(request, "Registration successful! You can now log in.")
        return redirect("login")

    return render(request, "register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("login")



