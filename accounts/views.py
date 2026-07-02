from django.shortcuts import get_object_or_404, render, redirect, reverse
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from accounts.forms import RegisterForm
from accounts.models import CustomUser, Prediction

User = get_user_model()




# ─────────────────────────────────────────────
#  Auth views
# ─────────────────────────────────────────────

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_admin = False
            user.save()
            if request.user.is_authenticated and (request.user.is_admin or request.user.is_superuser):
                messages.success(request, "User created successfully.")
                return redirect(reverse('admin_dashboard') + '?section=users')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_admin or user.is_superuser:
                return redirect('admin_dashboard')
            else:
                return redirect('user_dashboard')
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')



# ─────────────────────────────────────────────
# Edit  Profile (user dashboard)
# ─────────────────────────────────────────────

@login_required
def edit_profile(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        user = request.user

        if username:
            user.username = username

        if password1 or password2:
            if password1 != password2:
                messages.error(request, "Passwords do not match")
                return redirect('user_dashboard')
            if len(password1) < 8:
                messages.error(request, "Password must be at least 8 characters")
                return redirect('user_dashboard')
            user.set_password(password1)

        user.save()
        update_session_auth_hash(request, user) # Update session to prevent logout after password change
        messages.success(request, "Profile updated successfully")
        return redirect('user_dashboard')
    
