from django.shortcuts import render, get_object_or_404
from .models import UserProfile, Group
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect

# Create your views here.
def loginPage(request):
    page = 'login'
    
    if request.user.is_authenticated:
        return redirect('student-home', pk=request.user.userprofile.pk)
    
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'User does not exist')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('student-home', pk=request.user.userprofile.pk)
        else:
            messages.error(request, "username or password does not exist")
            
    
    context = {'page':page}
    return render(request, 'users/login_register.html', context=context)


def logoutUser(request):
    logout(request)
    return redirect('login')
    
    
def registerPage(request):
    form = UserCreationForm()
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('student-home', pk=request.user.userprofile.pk)
        else:
            messages.error(request, 'An error occured during registration')
    context = {'form':form}
    return render(request, 'users/login_register.html', context)

def student_home(request, pk):
    student = get_object_or_404(UserProfile, user__id=pk)
    context = {'student':student}
    return render(request, 'users/student_home.html', context)
    
