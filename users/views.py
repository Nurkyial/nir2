from django.shortcuts import render, get_object_or_404
from .models import UserProfile, Group
from base.models import File, ResearchWork, Submission, Topic, Assignment, Semester, TopicSubmission
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from .form import UploadFileForm, UserCreationForm
from datetime import date
from .utils import SemesterUtils
from django.http import JsonResponse, Http404
from .fastapi_client import fastapi_request

def loginPage(request):
    page = 'login'
    print(1)
    
    if request.method == 'POST':
        print(2)
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
 
        data = {"username": username, "password": password}

        print("Отправляем в FastAPI:", data)
        response, status_code = fastapi_request('auth/login', method='POST', data=data, use_query_params=True)
        user_id = response["data"].get("id")
        print(f"FastAPI Response: {response} and status_code: {status_code}")

        user = authenticate(request, username=username, password=password)
        print(22, user)
        if user:
            print(3)
            login(request, user)
            return redirect_dashboard(user, user_id)
        else:
            user = User.objects.create(username=username)
            user.set_password(password)  
            user.save()
    
        messages.error(request, "Неверные учетные данные")
 
    context = {"page":page}
    return render(request, 'users/login.html', context=context)


def redirect_dashboard(user, user_id):
    print(f"username в джанго: {user.username}")
    response, status_code = fastapi_request(f"user/{user_id}/info", method="GET")
    print(f"status code: {status_code} and {"data" not in response}")

    if status_code != 200 or "data" not in response:
        print("Ошибка получения пользователя")
        return redirect("login")
    
    user_role = response["data"].get("role")
    print(f'user role: {user_role}')
    print(4)
    if not user_role:
        messages.error("Ошибка: профиль пользователя не найден.")
        return redirect('login')
    if user_role.lower() == 'student':
        print(5)
        return redirect('student-home', user_id=user_id)
    elif user_role.lower() == 'teacher':
        print(6)
        return redirect('teacher-home', teacher_id=user_id)
    else:
        messages.error('Unknown user')
        return redirect('login')

def logoutUser(request):
    logout(request)
    return redirect('login')
    
# Student page views
@login_required
def student_home(request, user_id):
    print("=== Student Home View Started ===")
    response, status_code = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
    data = response.get("data", {})
    role = data.get("role", None)
    assignment_subordinate = data.get("assignment_subordinate", []) # список всех отпрвленных заявок
    last_accepted_assignment = data.get("last_accepted_assignment_subordinate", {})

    if last_accepted_assignment:
        assignment_id = last_accepted_assignment.get("id", None)
        is_accepted = last_accepted_assignment.get("is_accepted", None)
        is_reviewed = last_accepted_assignment.get("is_reviewed", None)
        teacher_id = last_accepted_assignment.get("teacher_id", None)
        status = last_accepted_assignment.get("status", None)
    else:
        assignment_id = None
        is_accepted = None
        is_reviewed = None
        teacher_id = None
        status = None

    research_works = []
    submission_values = []

    print(7)
    try:                        
        print(f"assignment from fastapi: {last_accepted_assignment}")
        
        if is_accepted:
            # Получаем данные о преподавателе
            assignment_response, assignment_status_code = fastapi_request(f"assignment/{assignment_id}", method="GET", use_query_params=True)
            assignment_data = assignment_response.get("data", {})
            teacher = assignment_data.get("teacher", {})
            teacher_id = teacher.get("teacher_id", None)
            teacher_first_name = teacher.get("first_name", None)
            teacher_last_name = teacher.get("last_name", None)
            teacher_middle_name = teacher.get("middle_name", None)

            print(f"Teacher info: {teacher}")

            # Если нучный руководитель назначен, загружаем исследования и отправленные задания
            if teacher:
                submission_response, submission_status_code = fastapi_request(f"assignment/{assignment_id}/submissions", method="GET", use_query_params=True)
                if submission_status_code == 200:
                    submission_values = submission_response.get("values", [])
                    research_works = ResearchWork.objects.all()
                else:
                    messages.error(request, "Пока еще нет submission")

            else:
                print('teacher has not accepted yet')
        else:
            print("No valid assignment data found in FastAPI response.")

    except Exception as e:
        print(f"Error fetching assignment data: {e}")

    context = {
        'data': data,
        'role': role,
        'research_works': research_works, 
        'semester': "Unknown", 
        'user_id': user_id,
        'teacher_id': teacher_id,
        'teacher_first_name': teacher_first_name,
        'teacher_last_name': teacher_last_name,
        'teacher_middle_name': teacher_middle_name,
        'submission_values': submission_values,
        'assignment_data': assignment_data,
        'assignment_subordinate': assignment_subordinate,
        'is_accepted': is_accepted,
        }
    
    return render(request, 'users/student_home.html', context)


def student_create_assignment():
    pass

def research_work_detail(request, rw_id, subm_id):
    research_work = get_object_or_404(ResearchWork, pk=rw_id)
    # submissions = Submission.objects.filter(research_work=research_work, semester=semester)
    submissions = Submission.objects.filter(assignment__student=request.user.userprofile)
    submission = get_object_or_404(Submission, pk=subm_id)
    topics = Topic.objects.filter(research_work=research_work)
    context =   {'research_work': research_work, 'submissions':submissions, 'topics': topics, 'submission_id':submission.id }
    return render(request, 'users/topics.html', context=context)


def upload_page(request, rw_id, topic_id, subm_id):
    try:
        research_work = get_object_or_404(ResearchWork, pk=rw_id)
    except Http404:
        print(f"ResearchWork with id={rw_id} not found.")
        raise

    try:
        topic =  get_object_or_404(Topic, pk=topic_id)
    except Http404:
        print(f"Topic with id={topic_id} not found.")
        raise

    try:
        submission = get_object_or_404(Submission, pk=subm_id)
    except Http404:
        print(f"Submission with id={subm_id} not found.")
        raise
    try:
        topic_submission = get_object_or_404(TopicSubmission, topic=topic, submission=submission)
    except Http404:
        print(f"TopicSubmission with topic_id={topic_id} and submission_id={subm_id} not found.")
        raise

    form = UploadFileForm()  # This ensures the form is available if needed
    file_list = File.objects.filter(topic_submission=topic_submission).order_by('-upload_date')
    print(ResearchWork.objects.filter(pk=1).exists())
    context = {'research_work':research_work, 'topic':topic, 'submission':submission, 'form': form, 'file_list': file_list}
    return render(request, 'users/upload_file.html', context)


def upload_file(request, subm_id, topic_id):
    submission = get_object_or_404(Submission, pk=subm_id)
    topic = get_object_or_404(Topic, pk=topic_id)

    try:
        topic_submission = get_object_or_404(TopicSubmission, topic=topic, submission=submission)
    except Http404:
        print(f"TopicSubmission with topic_id={topic_id} and submission_id={subm_id} not found.")
        raise

    form = UploadFileForm()
    file_list = File.objects.filter(topic_submission=topic_submission).order_by('-upload_date')
    context = {'submission':submission, 'topic':topic, 'form': form, 'file_list':file_list}
    
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid(): 
            file_instance = form.save(commit=False)
            file_instance.topic_submission = topic_submission
            # file_instance.submission = submission
            file_instance.save()
            file_list = File.objects.filter(topic_submission=topic_submission).order_by('-upload_date')
            context.update({'file_list':file_list})
            messages.success(request, 'File succesfully uploaded')
            # return render(request, 'users/upload_file.html', context=context)
            return redirect('upload-file', subm_id=submission.id, topic_id=topic.id)
        else:
            messages.error(request, 'No file was uploaded')
            form = UploadFileForm()
    return render(request, 'users/upload_file.html', context=context)

def choose_teacher(request, student_id): # для полноценного функционала ручка не готова
    teachers_response, _ = fastapi_request("user/all-teachers", method="POST", data=None)
    # teachers = [user.get("user_id") for user in teachers_response.get("values") if user.get("role") == "teacher"] # здесь нужно поменять на список из словарей по данным учителей
    teachers = [10]
    if request.method == 'POST':
        teacher_id = request.POST.get("teacher_id")
        message = request.POST.get("message")
        is_teacher_chosen, _ = fastapi_request("teacher/browse_assignments", method="GET", data={"teacher_id":teacher_id})
        if is_teacher_chosen["values"].get("is_accepted") or is_teacher_chosen["values"].get("is_reviewed"):
            messages.error(request, "The teacher is alredy chosen, you can\'t choose them twice or your request is on the review")
            return redirect('choose-teacher', student_id=student_id)
        else:
            if teacher_id and message:
                data = {"student_id":student_id, "teacher_id":teacher_id, "text":message}
                assignment, status_code = fastapi_request("student/create-assignment", method="POST", data=data, use_query_params=True)
            else:
                messages.error(request, 'You need to fill all the required spaces')
    
    chosen_teachers, _ = fastapi_request("teacher/browse_assignments", method="GET", data={"teacher_id":student_id}) # здесь должен быть список всех учителей, которые были выбраны и отправлены запросы студентом
    # teacher_id потом должен быть заменен на student_id
    context = {'teachers':teachers, 'student':student_id, 'chosen_teachers':chosen_teachers}
    return render(request, 'users/choose_teacher.html', context=context)

    
# teacher page views
@login_required
def teacher_home(request, teacher_id):
    if request.user.is_authenticated:
        # teacher = get_object_or_404(UserProfile, pk=teacher_id, role='teacher')
        teacher = get_object_or_404(UserProfile, user__id=teacher_id)
        assignments = Assignment.objects.filter(teacher=teacher).exclude(is_reviewed=True, is_accepted=False)
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
    
@login_required
def submission_topics(request, sub_id):
    if request.user.is_authenticated:
        submission = get_object_or_404(Submission, pk=sub_id)
        
        if submission.assignment.teacher != request.user.userprofile:
            messages.error(request, "You do not have permission to view this page.")
            return redirect('teacher-home', teacher_id=request.user.userprofile.pk)
        
        topics = Topic.objects.filter(research_work=submission.research_work)
        context = {'submission':submission, 'topics':topics}
        
        return render(request, 'users/submission_topics.html', context=context)
    
    else:
        messages.error(request, 'Invalid user')
        return redirect('login')
    
@login_required
def topics_files(request, sub_id, topic_id):
    if request.user.is_authenticated:
        submission = get_object_or_404(Submission, pk=sub_id)
        topic = get_object_or_404(Topic, pk=topic_id)
        topic_submission = get_object_or_404(TopicSubmission, topic=topic, submission=submission)
        files = File.objects.filter(topic_submission=topic_submission).order_by('-upload_date')
        # last_uploaded_file = files.first() if files.exists() else None
        last_uploaded_file = files.filter(is_reviewed=False).first()
        if request.method == 'POST':
            file_id = request.POST.get('file_id')
            action = request.POST.get('action')
            comment_text = request.POST.get('comment')
            file_object = get_object_or_404(File, pk=file_id)
            if action == 'Принять':
                file_object.is_accepted = True
                file_object.is_reviewed = True
                file_object.comment = ''
                messages.success(request, 'File accepted')
            elif action == 'Отклонить':
                file_object.is_accepted = False
                file_object.is_reviewed = True
                file_object.comment = comment_text
                messages.success(request, 'File rejected.')
            
            file_object.save()

            files = File.objects.filter(topic_submission=topic_submission).order_by('-upload_date')
            last_uploaded_file = files.filter(is_reviewed=False).first()
            return redirect('topics-files', sub_id=sub_id, topic_id=topic_id)
            
            
        context = {'topic':topic, 'files':files, 'last_uploaded_file':last_uploaded_file}
        return render(request, 'users/topics_files.html', context=context)
    else:
        messages.error(request, 'Invalid user') 
        return redirect('login')


def edit_profile(request, user_id):
    response, status_code = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
    response_data = response.get("data", {})
    role = response_data.get("role", None)
    data = {}

    if request.method == 'POST':
        data = {
            "target": {
                "user_id": user_id
            },
            "data": {
                "email": request.POST.get("email"),
                "first_name": request.POST.get("first_name"),
                "last_name": request.POST.get("last_name"),
                "middle_name": request.POST.get("middle_name"),
                "group_id": request.POST.get("group_id", 0)
            }
        }

        print(f"data from the form: {data}")
        
        set_info_response, set_info_status_code = fastapi_request(f"user/set-info", method="PATCH", data=data, use_query_params=False)

        if set_info_status_code == 201:
            print(f"Данные пользователя успешно обновлены: {set_info_response}")
            messages.success(request, "Данные пользователя успешно обновлены.")
        else:
            print(f"Ошибка изменения данных пользователя: {set_info_response}")
            messages.error(request, f"Ошибка: {response.get('error', 'Неизвестная ошибка')}")

    context = {
        "data": response_data,
        "role": role,
        "user_id": user_id
    }
    return render(request, "users/edit_profile.html", context=context)
  

"""
class LoginResponse(Model):
    username: str
    password: str
    middle_name: str


d = {
    "username": "str",
    "password": "str",
    "middle_name": "str",
}

pd_obj = LoginResponse(**d)
d['username']
pd_obj.username
"""