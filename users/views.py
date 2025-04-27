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
        if status_code == 200:
            user_id = response["data"].get("id")
            print(f"FastAPI Response: {response} and status_code: {status_code}")
        else:
            print(f"Ошибка при логине: {response} status_code: {status_code}")
            messages.error(request, f"Ошибка при логине: {response} status_code: {status_code}")

        user = authenticate(request, username=username, password=password)
        print(22, user)
        if user:
            print(3)
            login(request, user)
            return redirect_dashboard(user, user_id)
        else:
            # user = User.objects.create(username=username)
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password(password)  
                user.save()
            login(request, user)
            return redirect_dashboard(user, user_id)
 
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
        return redirect('teacher-home', user_id=user_id)
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
    assignment_data = {}
    teacher_id = None
    teacher_first_name = None
    teacher_last_name = None
    teacher_middle_name = None
    print(7)
    try:                        
        print(f"assignment from fastapi: {last_accepted_assignment}")
        
        if is_accepted:
            # Получаем данные о преподавателе, если у студента есть научрук
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

def choose_teacher(request, user_id): 
    print(f'user_id = {user_id}')
    user_info, status_code_info = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)

    if status_code_info != 200:
        messages.error(request, "Не удалось получить информацию о студенте")
        return redirect('student-home', user_id=user_id)
    
    student_data = user_info.get("data", {})
    print(f'student data: {student_data}')
    assignment_subordinate = student_data.get("assignment_subordinate", [])
    has_pending_assignment = any(not a["is_reviewed"] for a in assignment_subordinate)
    role = student_data.get("role", None)
    
    create_assignment_data = {}
  
    if request.method == 'POST':
        teacher_id = request.POST.get("teacher_id")
        message = request.POST.get("message")

        create_assignment_data = {
            "student": {
                "user_id": user_id
            },
            "teacher": {
                "user_id": teacher_id
            },
            "text": message
        }
        create_assignmenent, status_code_asgn = fastapi_request("student/create-assignment", method="POST", data=create_assignment_data)
        if create_assignmenent.get("msg") == "success" and status_code_asgn == 201:
            return redirect('students-assignments', user_id=user_id)    
        else:
            messages.error(request, f"error creating assignment: {create_assignmenent}")
            return redirect('choose-teacher', user_id=user_id)
    
    all_teachers, status_code_teachers = fastapi_request("user/all-teachers", method="GET", data=None)
    teachers = []
    if status_code_teachers == 200:
        teachers = [
            {"teacher_id": user.get("id"),
            "last_name": user.get("last_name"),
            "first_name": user.get("first_name"),
            "middle_name": user.get("middle_name"),
            "email": user.get("email")} for user in all_teachers.get("values")]
    context = {'teachers':teachers, 'user_id':user_id, 'chosen_teacher': assignment_subordinate, 'has_pending_assignment': has_pending_assignment, 'role': role, 'data': student_data}
    return render(request, 'users/choose_teacher.html', context=context)

def assignment_statuses(request, user_id):
    user_info, status = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
    if status != 200:
        messages.error(request, "Ошибка при получении заявок")
        return redirect("student-home", user_id=user_id)
    student_data = user_info.get("data", {})
    role = student_data.get("role", None)
    assignments = user_info.get("data", {}).get("assignment_subordinate", [])

    for assignment in assignments:
        teacher_id = assignment.get("teacher_id")
        if teacher_id:
            teacher_info, teacher_status = fastapi_request(f"user/{teacher_id}/info", method="GET", use_query_params=True)
            if teacher_status == 200:
                teacher_data = teacher_info.get("data", {})
                assignment["teacher"] = {
                    "first_name": teacher_data.get("first_name", ""),
                    "last_name": teacher_data.get("last_name", ""),
                    "middle_name": teacher_data.get("middle_name", "")
                }
    context = {"assignments": assignments, 'data': student_data, 'role': role, 'user_id': user_id}
    return render(request, 'users/assignments_list.html', context=context)
 

# ===============================================================================================================================
# teacher page views

@login_required
def teacher_home(request, user_id):
    print("=== Teacher Home View Started ===")
    print(f"teacher_id = {user_id}")
    teacher_info, teacher_status = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)

    if teacher_status != 200:
        messages.error(request, "Ошибка получения информации о преподователе") 
        return redirect('login')
    
    data = teacher_info.get("data", {})
    assignments = data.get("assignment_supervisor", [])
    student_requests_num = len([asgn for asgn in assignments if asgn["is_accepted"] is None])
    active_assignments, active_assignments_status = fastapi_request(f"teacher/list-students", method="GET", data={"teacher_id": user_id}, use_query_params=True)
    if active_assignments_status != 200:
        messages.error(request, "Ошибка при получении списка студентов")
        return redirect("teacher-home", user_id=user_id)
    students = active_assignments.get("values", [])
    role = teacher_info.get("data", {}).get("role", None)
    context = {'role': role, 'user_id': user_id, 'student_requests_num': student_requests_num, 'students': students, 'data': data}
    
    return render(request, 'users/teacher_home.html', context=context)


def review_assignment(request, user_id):
    teacher_info, teacher_status = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
    if teacher_status != 200:
        messages.error(request, "Ошибка получения информации о преподавателе")
        return redirect('login')
    
    data = teacher_info.get("data", {})
    role = data.get("role", None)   
    assignments = data.get("assignment_supervisor", [])

    # Добавляем инфу о студентах в заявки
    for assignment in assignments:
        student_id = assignment.get("student_id")
        if student_id:
            student_info, student_status = fastapi_request(f"user/{student_id}/info", method="GET", use_query_params=True)
            if student_status == 200:
                student_data = student_info.get("data", {})
                assignment["student"] = {
                    "first_name": student_data.get("first_name", ""),
                    "last_name": student_data.get("last_name", ""),
                    "middle_name": student_data.get("middle_name", ""),
                    "group": student_data.get("group", "")
                }

    if request.method == 'POST':
        print(9)
        action = request.POST.get('action')
        print(f'action = {action}')
        assignment_id = request.POST.get('assignment_id')
        print(f'assignment id from form = {assignment_id}')
        try:
            action_data = {
                "teacher": {"user_id": user_id},
                "assignment_id": assignment_id
            }
            if action == 'accept':
                response, status = fastapi_request('teacher/accept-assignment', method='PATCH', data=action_data, use_query_params=False)
                if status == 200:
                    messages.info(request, "Assignment успешно создан")
                else:
                    messages.error(request, "Ошибка приянтия assignment")
            elif action == 'decline':
                response, status = fastapi_request('teacher/decline-assignment', method='PATCH', data=action_data, use_query_params=False)
                if status == 200:
                    messages.info(request, "Assignment успешно отклонен")
                else:
                    messages.error(request, "Ошибка отклонения assignment")
            return redirect('review-assignment', user_id=user_id)
        except:
            messages.error(request, "Ошибка обработки assignment")
            return redirect('review-assignment', user_id=user_id)
    context = {'role': role, 'user_id': user_id, 'data': data, 'assignments': assignments}
    return render(request, 'users/review_assignment.html', context=context)

def create_submission(request, user_id): # функция которая создает работу для студетов
    research_works = {
        'Диплом': 1,
        'НИР': 2,
        'УИР': 3,
        'Зимняя практика': 4,
        'Летняя практика': 5
    } # пока что так, когда появится ручка, нужно ее заменить

    teacher_info, teacher_status = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
    if teacher_status != 200:
        messages.error(request, "Ошибка получения информации о преподавателе")
        return redirect('login')
    data = teacher_info.get("data", {})
    role = data.get("role", None)
    list_students, list_students_status = fastapi_request(f"teacher/list-students", method="GET", data={"teacher_id":user_id}, use_query_params=True)
    if list_students_status != 200:
        messages.error(request, "Ошибка получения списка студентов")
        return redirect('teacher-home', user_id)
    students = list_students.get("values", [])

    if request.method == 'POST':
        assignment_id = request.POST.get('assignment_id')
        researchwork_id = request.POST.get('researchwork_id')
        submission_title = request.POST.get('submission_title')

        try:
            submission_data = {
                'assignment_id': assignment_id,
                'researchwork_id': researchwork_id,
                'submission_title': submission_title
            }
            
            response, status = fastapi_request(f'teacher/create-submission', method='POST', data=submission_data, use_query_params=True)

            if status == 200:
                    messages.info(request, "Submission успешно создан")
            else:
                messages.error(request, "Ошибка создания Submission")
        except Exception as e:
            print(f"Ошибка при создании submission: {e}")
            messages.error(request, 'Ошибка обработки создания submission')
            return redirect('teacher-home', user_id)
        
    context = {
        'role': role,
        'data': data,
        'user_id': user_id,
        'research_works': research_works,
        'students': students
    }
    return render(request, 'users/create_submission.html', context=context)

def review_submissions(request, user_id):
    teacher_info, teacher_status = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
    if teacher_status != 200:
        messages.error(request, "Ошибка получения информации о преподавателе")
        return redirect('login')
    data = teacher_info.get("data", {})
    role = data.get("role", None)
    list_students, list_students_status = fastapi_request(f"teacher/list-students", method="GET", data={"teacher_id":user_id}, use_query_params=True)
    if list_students_status != 200:
        messages.error(request, "Ошибка получения списка студентов")
        return redirect('teacher-home', user_id)
    students = list_students.get("values", [])
    context = {
        'role': role,
        'data': data,
        'user_id': user_id,
        'students': students
    }
    return render(request, 'users/review_submissions.html', context=context)

def review_student_submission(request, user_id, student_id, assignment_id):
    teacher_info, teacher_status = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
    if teacher_status != 200:
        messages.error(request, "Ошибка получения информации о преподавателе")
        return redirect('login')
    data = teacher_info.get("data", {})
    role = data.get("role", None)
    submissions, submission_status = fastapi_request(f"assignment/{assignment_id}/submissions")
    if submission_status != 200:
        messages.error(request, "Ошибка получения информации о работах студента")
        return redirect('review-submissions', user_id)
    submissions_values = submissions.get("values", [])
    context = {
        'role': role,
        'data': data,
        'user_id': user_id,
        'submissions_values': submissions_values,
        'student_id': student_id
    }
    return render(request, 'users/review_student_submission.html', context=context)

def review_topics(request, user_id, submission_id):
    teacher_info, teacher_status = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
    if teacher_status != 200:
        messages.error(request, "Ошибка получения информации о преподавателе")
        return redirect('login')
    data = teacher_info.get("data", {})
    role = data.get("role", None)

    if request.method == 'POST':
        action = request.POST.get('action')
        submission_topic_id = request.POST.get('submission_topic_id')
        comment = request.POST.get('comment')

        payload = {
            "submission_topic_id": int(submission_topic_id),
            "comment": comment
        }

        if action == 'accept':
            url = 'teacher/accept-submission-topic'
        elif action == 'reject':
            url = 'teacher/decline-submission-topic'
        else:
            url = 'teacher/review-submission-topic'
            payload = payload = {
            "submission_topic_id": int(submission_topic_id)
            }
        
        try:
            response, status = fastapi_request(url, method="PATCH", data=payload, use_query_params=False)
            if status == 200:
                messages.success(request, f"Тема {'принята' if action == 'accept' else 'отклонена'} успешно.")
            else:
                messages.error(request, f"Ошибка при {'принятии' if action == 'accept' else 'отклонении'} темы.")
        except Exception as e:
            messages.error(request, f"Ошибка отправки данные: {str(e)}")
        
        return redirect('review-topics', user_id=user_id, submission_id=submission_id)

    topics_data, status = fastapi_request(f"submission/{submission_id}/topics", method="GET", use_query_params=True)
    topics = topics_data.get("values", [])
    if status != 200:
        messages.error(request, "Ошибка получения информации о топиках работы")
        return redirect('review-student-submission', user_id)
    submission, submission_status = fastapi_request(f"submission/{submission_id}")
    if submission_status != 200:
        messages.error(request, "Ошибка получения информации о работах студента")
        return redirect('review-submissions', user_id)

    submission_data = submission.get("data", {})
    context = {
        'role': role,
        'data': data,
        'user_id': user_id,
        'topics': topics,
        'submission_data': submission_data
    }
    return render(request, 'users/review_topics.html', context=context)

def review_submission_topic(request, topicz_id):
    pass

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
    print(f"edit profile started with role: {role} for user: {response.get("data").get("last_name")}")
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
    print(f"context for edit profile: {context}")
    return render(request, "users/edit_profile.html", context=context)
  

