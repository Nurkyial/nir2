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
from django.http import JsonResponse, Http404, HttpResponse, StreamingHttpResponse
from .fastapi_client import fastapi_request
import requests
from django.utils.encoding import smart_str
from urllib.parse import quote
from django.conf import settings
from django.core.cache import cache
import pandas as pd
from urllib.parse import quote


FASTAPI_URL = settings.FASTAPI_BASE_URL

def loginPage(request):
    page = 'login'
    print(1)
    
    if request.method == 'POST':
        print(2)
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
 
        data = {"username": username, "password": password}

        print("Отправляем в FastAPI:", data)
        response, status_code = fastapi_request('auth/login', method='POST', data=data, use_query_params=False)
        if status_code == 200:
            user_id = response["data"].get("id")
            print(f'user_id = {user_id}')
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
    response = redirect_dashboard(user, user_id)

    response.set_cookie("user_session_jwt", get_jwt())

    return response

def get_jwt():
    return ""

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
    
    print(8)
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

def submission_topics(request, user_id, submission_id):
    student_info, student_status = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
    if student_status != 200:
        messages.error(request, "Ошибка получения информации о студенте")
        return redirect('login')
    data = student_info.get("data", {})
    role = data.get("role", None)

    if request.method == 'POST':
        print("224")
        file = request.FILES.get('file')
        submission_topic_id = request.POST.get('submission_topic_id')
        print(file, submission_topic_id)

        if not file or not submission_topic_id:
            print("229")
            print('Файл или submission_topic_id не переданы')
            return redirect('submission-topics', user_id=user_id, submission_id=submission_id)
        
        try:
            print("234")
            files = {'file': (file.name, file.read(), file.content_type)}
            # files = {'file': file}
            params = {'submission_topic_id': submission_topic_id}
            response, status_code = fastapi_request('user/upload', method='POST', data=params, files=files, use_query_params=True)
            # url = f"{FASTAPI_URL}/student/upload"

            # response = requests.post(url, params=params, files=files)

            if status_code == 200:
                print("Файл успешно загружен")
            else:
                print(f'Ошибка загрузки файла: {response}')
                
            print("246", response)
        except Exception as e:
            print(f'Ошибка загрузки: {str(e)}')

        print("249")
        return redirect('submission-topics', user_id=user_id, submission_id=submission_id)

    topics_data, status = fastapi_request(f"submission/{submission_id}/topics", method="GET", use_query_params=True)
    topics = topics_data.get("values", [])
    if status != 200:
        messages.error(request, "Ошибка получения информации о топиках работы")
        return  redirect('submission-topics', user_id=user_id, submission_id=submission_id)
    submission, submission_status = fastapi_request(f"submission/{submission_id}")
    if submission_status != 200:
        messages.error(request, "Ошибка получения информации о работах студента")
        return  redirect('submission-topics', user_id=user_id, submission_id=submission_id)

    submission_data = submission.get("data", {})
    context = {
        'role': role,
        'data': data,
        'user_id': user_id,
        'topics': topics,
        'submission_data': submission_data,
        'submission_id': submission_id
    }

    return render(request, 'users/submission_topics.html', context=context)

def download_file(request, file_id):
    print(f'file_id = {file_id}')
    try:
        # url = f"http://89.150.34.163:8000/api/v1/student/download/{file_id}"
        # response = requests.get(url)
        response, status_code = fastapi_request(f'user/download/{file_id}', method='GET', data={'file_id': file_id})
        if status_code != 200:
            raise Http404("Файл не найден")

        json_data = response
        print(f'json_data: {json_data}')
        download_url = json_data.get("download_url")    
        original_filename = json_data.get("original_filename", f"file_{file_id}")
        print(f'filename: {original_filename}')

        if not download_url:
            raise Http404("Ссылка на скачивание отсутствует")

        file_response = requests.get(download_url, stream=True)
        if file_response.status_code != 200:
            raise Http404("Ошибка при скачивании файла")
        
        content_type = file_response.headers.get("Content-Type", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        filename_ascii = smart_str(original_filename)
        filename_utf8 = quote(original_filename)

        response = StreamingHttpResponse(
            streaming_content=file_response.iter_content(chunk_size=8192),
            content_type=content_type
        )
        response['Content-Disposition'] = (
            f'attachment; filename="{filename_ascii}"; '
            f"filename*=UTF-8''{filename_utf8}"
        )

        return response

    except Exception as e:
        print(f"Ошибка при скачивании: {e}")
        raise Http404("Ошибка при скачивании файла")

def delete_file(request, user_id, file_id):
    submission_id = request.GET.get('submission_id')
    try:
        response, status_code = fastapi_request('user/remove-file', 'DELETE', data = {'file_id': file_id}, use_query_params=True)
        print(f"response from deleting file: {response} and status code: {status_code}")
        if status_code == 200:
            print(f"Файл с id = {file_id} успешно удален")
        else:
            print(f"Ошибка при удалении файла")
    except Exception as e:
        print(f"Ошибка при удалении файла")

    return redirect('submission-topics', user_id=user_id, submission_id=submission_id)
        
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
            return redirect('student-assignments', user_id=user_id)    
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
        'ВКР': 1,
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
                "group_id": request.POST.get("group_id", 0),
                "about_me": request.POST.get("about_me")
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
  

def show_statistics(request, user_id):

    students_without_teacher = []
    teacher_info, teacher_status = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
    response_data = teacher_info.get("data", {})
    role = teacher_info.get("data").get("role", None) 
    print(f"user_id in statistics = {user_id} and role = {role}")
    research_works = {
        1: 'ВКР',
        2: 'НИР',
        3: 'УИР',
        4: 'Зимняя практика',
        5: 'Летняя практика'
    } # пока что так, когда появится ручка, нужно ее заменить

    
    all_students = cache.get("all_students")
    if not all_students:
        response, status_code = fastapi_request('user/all-students', method='GET')
        all_students = response.get('values', [])
        cache.set("all_students", all_students, 60*30)
    # student_name, teacher_name, group, research_work, name_of_work, semester, topics (arrows), teacher_comment
    data = cache.get(f"statistics_user_{user_id}")
    if not data:
        data = []
        

        for student in all_students:
            student_first_name = student.get("first_name", "")
            student_last_name = student.get("last_name", "")
            student_middle_name = student.get("middle_name", "")
            if student.get("group") is None:
                student_group_name = "Группа не указана"
            else:
                student_group_name = student.get("group").get("group_name", "")
            assignment_subordinate = student.get("last_accepted_assignment_subordinate")
            if not assignment_subordinate:
                students_without_teacher.append({
                    "student_full_name": f"{student_last_name} {student_first_name} {student_middle_name}"
                })
                continue # если у студента нет препода, то пропускаем

            assignment_id = student.get("last_accepted_assignment_subordinate").get("id")
            assignment_cache_key = f"assignment_{assignment_id}"
            assignment_info = cache.get(assignment_cache_key)
            if not assignment_info:
                assignment_info, assignment_status = fastapi_request(f'assignment/{assignment_id}', method='GET', use_query_params=True)
                cache.set(assignment_cache_key, assignment_info, 60*30)

            teacher_first_name = assignment_info.get("data", {}).get("teacher").get("first_name", "")
            teacher_last_name = assignment_info.get("data", {}).get("teacher").get("last_name", "")
            teacher_middle_name = assignment_info.get("data", {}).get("teacher").get("middle_name", "")
            
            for submission in assignment_info.get("data", {}).get("submissions"):
                submission_id = submission.get("id")
                submission_title =  submission.get("submission_title")
                researchwork_id = submission.get("researchwork_id")
                semester = submission.get("semester")

                topics_cache_key = f"submission_topics_{submission_id}"
                topics = cache.get(topics_cache_key)
                if not topics:
                    topics, topics_status = fastapi_request(f'submission/{submission_id}/topics')
                    cache.set(topics_cache_key, topics, 60*30)
                topics_values = topics.get("values", [])
                
                topic_data_list = []
                for topic in topics_values:
                    topic_name = topic.get("topic").get("name")
                    topic_status = topic.get("is_accepted")
                    status_readable = (
                        "Принято" if topic_status is True else
                        "Отклонено" if topic_status is False else
                        "На рассмотрении"
                    )
                    comments = topic.get("comments", [])
                    last_comment = comments[-1]["comment"] if comments else ""

                    topic_data_list.append({
                        "name": topic_name,
                        "status": status_readable,
                        "comment": last_comment
                    })
                
                data.append({
                    "student_full_name": f"{student_last_name} {student_first_name} {student_middle_name}", 
                    "teacher_full_name": f"{teacher_last_name} {teacher_first_name} {teacher_middle_name}",
                    "student_group_name": student_group_name,
                    "researchwork_name": research_works.get(researchwork_id, "Нет типа работы"),
                    "submission_title": submission_title,
                    "semester": semester,
                    "topics_values": topic_data_list
                })
        cache.set(f'statistics_user_{user_id}', data, 60*10)
    
    field = request.GET.get("field", "").strip().lower()
    query = request.GET.get("query", "").strip().lower()

    if field and query:
        def matches(info):
            if field == "student":
                value = info.get("student_full_name", "").lower()
            elif field == "teacher":
                value = info.get("teacher_full_name", "").lower()
            elif field == "group":
                value = info.get("student_group_name", "").lower()
            elif field == "research":
                value = info.get("researchwork_name", "").lower()
            elif field == "semester":
                value = str(info.get("semester", "")).lower()
            return query in value

        data = list(filter(matches, data))
    
    context = {"statistics": data, "students_without_teacher": students_without_teacher, "user_id":user_id, "role": role, "data": response_data}
    return render(request, 'users/show_statistics.html', context=context)

def export_statistics_excel(request, user_id):
    # забираем анные из кеша
    data = cache.get(f"statistics_user_{user_id}")

    if not data:
        return HttpResponse("Нет данных для экспорта. Обновите страницу и попробуйте снова", status=400)
    
    field = request.GET.get("field", "").strip().lower()
    query = request.GET.get("query", "").strip().lower()

    if field and query:
        def matches(info):
            if field == "student":
                value = info.get("student_full_name", "").lower()
            elif field == "teacher":
                value = info.get("teacher_full_name", "").lower()
            elif field == "group":
                value = info.get("student_group_name", "").lower()
            elif field == "research":
                value = info.get("researchwork_name", "").lower()
            elif field == "semester":
                value = str(info.get("semester", "")).lower()
            else:
                return False
            return query in value
        data = list(filter(matches, data))
        
    rows = []
    for item in data:
        row = {
            "ФИО студента": item["student_full_name"],
            "ФИО руководителя": item["teacher_full_name"],
            "Группа": item["student_group_name"],
            "Тип работы": item["researchwork_name"],
            "Тема работы": item["submission_title"],
            "Семестр": item["semester"]
        }

        for topic in item["topics_values"]:
            row[topic["name"]] = topic["status"]
        rows.append(row)
    
    df = pd.DataFrame(rows)
    filename = 'статистика.xlsx'
    encoded_filename = quote(filename)
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    
    response['Content-Disposition'] = f'attachment; filename=export.xlsx; filename*=UTF-8\'\'{encoded_filename}'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Статистика")
    
    return response

                
                





