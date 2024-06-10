from django.shortcuts import render, get_object_or_404
from .models import UserProfile, Group
from base.models import File, ResearchWork, Submission, Topic, Assignment
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from .form import UploadFileForm, ChooseTeacherForm

# Create your views here.
def loginPage(request):
    page = 'login'
    
    if request.user.is_authenticated:
        # return redirect('student-home', pk=request.user.userprofile.pk)
        return redirect_dashboard(request.user)
    
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
            # return redirect('student-home', pk=request.user.userprofile.pk)
            return redirect_dashboard(user)
        else:
            messages.error(request, "username or password does not exist")
            
    
    context = {'page':page}
    return render(request, 'users/login_register.html', context=context)

def redirect_dashboard(user):
    user_profile = get_object_or_404(UserProfile, user=user)
    if user_profile.role == 'student':
        return redirect('student-home', pk=user_profile.pk)
    elif user_profile.role == 'teacher':
        return redirect('teacher-home', teacher_id=user_profile.pk)
    else:
        messages.error('Unknown user')
        return redirect('login')

def logoutUser(request):
    logout(request)
    return redirect('login')
    
def home(request):
    if request.user.is_authenticated:
        return redirect('student-home', pk=request.user.userprofile.pk)
    return redirect('login')

# Student page views
@login_required
def student_home(request, pk):
    if request.user.is_authenticated:
        student = get_object_or_404(UserProfile, user__id=pk)
        teacher = UserProfile.objects.get(role='teacher', user__id='2')
        print(teacher)
        research_works = ResearchWork.objects.all()
        semester = ['1', '2', '3', '4', '5', '6', '7', '8']
        submissions = Submission.objects.filter(assignment__student=student)
        context = {'research_works':research_works, 'semester':semester, 'student':student, 'submissions': submissions}
        
        if request.method == 'POST':  
            research_work_id = request.POST.get('research_work_id')  
            semester = request.POST.get('semester')
            if research_work_id and semester:
                research_work = ResearchWork.objects.get(id=research_work_id)
                assignment = Assignment.objects.get(student=student, teacher=teacher)
                
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
    else:
        page = 'login'
        context = {'page':page}
        return render(request, 'users/login_register.html', context=context)

def research_work_detail(request, rw_id, semester, subm_id):
    research_work = get_object_or_404(ResearchWork, pk=rw_id)
    # submissions = Submission.objects.filter(research_work=research_work, semester=semester)
    submissions = Submission.objects.filter(assignment__student=request.user.userprofile)
    submission = get_object_or_404(Submission, pk=subm_id)
    topics = Topic.objects.filter(research_work=research_work)
    context =   {'research_work': research_work, 'submissions':submissions, 'topics': topics, 'submission_id':submission.id }
    return render(request, 'users/topics.html', context=context)


def upload_page(request, rw_id, topic_id, subm_id):
    research_work = get_object_or_404(ResearchWork, pk=rw_id)
    topic =  get_object_or_404(Topic, pk=topic_id)
    submission = get_object_or_404(Submission, pk=subm_id)
    form = UploadFileForm()  # This ensures the form is available if needed
    file_list = File.objects.filter(submission=submission, topic=topic).order_by('-upload_date')
    context = {'research_work':research_work, 'topic':topic, 'submission':submission, 'form': form, 'file_list': file_list  }
    return render(request, 'users/upload_file.html', context)


def upload_file(request, subm_id, topic_id):
    submission = get_object_or_404(Submission, pk=subm_id)
    topic = get_object_or_404(Topic, pk=topic_id)
    form = UploadFileForm()
    file_list = File.objects.filter(submission=submission, topic=topic).order_by('-upload_date')
    context = {'submission':submission, 'topic':topic, 'form': form, 'file_list':file_list}
    # print("Files loaded:", file_list.count())
    
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid(): 
            file_instance = form.save(commit=False)
            file_instance.topic = topic
            file_instance.submission = submission
            file_instance.save()
            file_list = File.objects.filter(submission=submission, topic=topic).order_by('-upload_date')
            context.update({'file_list':file_list})
            messages.success(request, 'File succesfully uploaded')
            # return render(request, 'users/upload_file.html', context=context)
            return redirect('upload-file', subm_id=submission.id, topic_id=topic.id)
        else:
            messages.error(request, 'No file was uploaded')
            form = UploadFileForm()
    return render(request, 'users/upload_file.html', context=context)

def choose_teacher(request, student_id):
    teachers = UserProfile.objects.filter(role='teacher')
    student = get_object_or_404(UserProfile, pk=student_id, role='student')
    
    if request.method == 'POST':
        teacher_id = request.POST.get("teacher_id")
        message = request.POST.get("message")
        if teacher_id and message:
            teacher = get_object_or_404(UserProfile, pk=teacher_id, role='teacher')
            assignments = Assignment.objects.filter(teacher=teacher)
            
            if assignments.exists():
                for assignment in assignments:
                    if assignment.is_accepted or not assignment.is_reviewed:
                        messages.error(request, 'The teacher is alredy chosen, you can\'t choose them twice')    
                        return redirect('choose-teacher', student_id=student.id)
            
            Assignment.objects.create(student=student, teacher=teacher, text=message)
        else:
            messages.error(request, 'Something went wrong')
            # print('It did not work')
    
    chosen_teachers = Assignment.objects.filter(student=student).order_by('-created_at')
    context = {'teachers':teachers, 'student':student, 'chosen_teachers':chosen_teachers}
    return render(request, 'users/choose_teacher.html', context=context)



     
# teacher page views
@login_required
def teacher_home(request, teacher_id ):
    if request.user.is_authenticated:
        teacher = get_object_or_404(UserProfile, pk=teacher_id, role='teacher')
        assignments = Assignment.objects.filter(teacher=teacher)
        context = {'teacher':teacher, 'assignments':assignments}
        if request.method == 'POST':
            action = request.POST.get('action')
            assignment_id = request.POST.get('assignment_id')
            
            try:
                assignment = Assignment.objects.get(pk=assignment_id, teacher=teacher)
                if action == 'accept':
                    assignment.is_accepted = True
                    assignment.is_reviewed = True
                    messages.success(request, 'Request accepted')
                elif action == 'reject':
                    assignment.is_accepted = False
                    assignment.is_reviewed = True
                    # assignment.delete()
                    messages.success(request, 'Request rejected')
                assignment.save()
                    
            except Assignment.DoesNotExist:
                messages.error(request, "Assignment does not exist")
            
            return redirect('teacher-home', teacher_id=teacher_id)
                    
        return render(request, 'users/teacher_home.html', context=context)
    else:
        messages.error(request, 'Invalid user')
        return redirect('login')
    
@login_required
def student_work_detail(request, as_id):
    if request.user.is_authenticated:
        assignment = get_object_or_404(Assignment, pk=as_id)
        
        if assignment.teacher != request.user.userprofile:
            messages.error(request, 'You do not have permission to view this page.')
            return redirect('teacher-home', teacher_id=request.user.userprofile.pk)
        
        submissions = assignment.submission_set.all()
        context = {'submissions':submissions, 'assignment':assignment}
        return render(request, 'users/students_work.html', context=context)
    
    else:
        messages.error(request, 'Invalid user')
        return redirect('login')
    
def student_work_topics(request, sub_id):
    pass