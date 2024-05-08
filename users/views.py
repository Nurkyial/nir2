from django.shortcuts import render, get_object_or_404
from .models import UserProfile, Group
from base.models import File, ResearchWork, Submission, Topic, Assignment
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
import datetime

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
    

def student_home(request, pk):
    student = get_object_or_404(UserProfile, user__id=pk)
    research_works = ResearchWork.objects.all()
    semester = ['1', '2', '3', '4', '5', '6', '7', '8']
    submissions = Submission.objects.filter(assignment__student=student)
    context = {'research_works':research_works, 'semester':semester, 'student':student, 'submissions': submissions}
    
    if request.method == 'POST':  
        research_work_id = request.POST.get('research_work_id')  
        semester = request.POST.get('semester')
        if research_work_id and semester:
            research_work = ResearchWork.objects.get(id=research_work_id)
            assignment = Assignment.objects.get(student=student)
            
            Submission.objects.create(
                assignment = assignment,
                semester = semester,
                research_work = research_work
            )
            messages.success(request, 'Submission successfully created')

            return redirect('student-home', pk=pk)
        else:
             messages.success(request, 'Invalid submission')
        
    return render(request, 'users/student_home.html', context)

def research_work_detail(request, rw_id, semester):
    research_work = get_object_or_404(ResearchWork, pk=rw_id)
    submissions = Submission.objects.filter(research_work=research_work, semester=semester)
    topics = Topic.objects.filter(research_work=research_work)
    context =   {'research_work': research_work, 'submissions':submissions, 'topics': topics }
    return render(request, 'users/topics.html', context=context)


def upload_page(request, rw_id, topic_id):
    research_work = get_object_or_404(ResearchWork, pk=rw_id)
    topic =  get_object_or_404(Topic, pk=topic_id)
    context = {'research_work':research_work, 'topic':topic}
    return render(request, 'users/upload_file.html', context)


def upload_file(request, rw_id, topic_id):
    if request.method == 'POST':
        request_file = request.FILES.get('document') if 'document' in request.FILES else None
        if request_file: 
            fs = FileSystemStorage()
            filename = fs.save(request_file.name, request_file)
            fileurl = fs.url(filename)
            context = {'fileurl':fileurl}
            
            filedata = File.objects.create(
                topic=topic_id,
                filename = request_file.name,
                created_at = fs.get_created_time(filename)
            )  
            return render(request, 'users/upload_file.html', context)
    return render(request, 'users/upload_file.html')



    
