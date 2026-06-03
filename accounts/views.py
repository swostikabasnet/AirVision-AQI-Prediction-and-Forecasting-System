from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
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
            if user.is_admin:
                return redirect('admin_dashboard')
            else:
                return redirect('user_dashboard')
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')



# ─────────────────────────────────────────────
#  Profile
# ─────────────────────────────────────────────

@login_required
def profile_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        user = request.user

        if username:
            user.username = username
        if email is not None:
            user.email = email

        if password1 or password2:
            if password1 != password2:
                messages.error(request, "Passwords do not match")
                return redirect('profile')
            if len(password1) < 6:
                messages.error(request, "Password must be at least 6 characters")
                return redirect('profile')
            user.password = make_password(password1)

        user.save()
        messages.success(request, "Profile updated successfully")
        return redirect('profile')

    last_prediction = Prediction.objects.filter(user=request.user).order_by('-created_at').first()
    return render(request, 'profile.html', {
        'last_prediction': last_prediction,
    })
