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
from datetime import datetime
from urllib.parse import quote
import json

FASTAPI_URL = settings.FASTAPI_BASE_URL
def registerPage(request):
    if request.method == 'POST':
        form_data = {
            "username": request.POST.get("username").lower(),
            "password": request.POST.get("password"),
            "middle_name": request.POST.get("middle_name"),
            "group_id": 0,
            "first_name": request.POST.get("first_name"),
            "last_name": request.POST.get("last_name"),
            "email": request.POST.get("email"),
            "role": request.POST.get("role","Student")
        }

        response, status_code = fastapi_request('auth/register', method='POST', data=form_data)

        if status_code == 201:
            user_data = response.get("data")
            username = user_data.get("username")
            user_id = user_data.get("id")

            # создаем фиктивного пользователя в джанго
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_unusable_password()
                user.save()
            
            login(request, user)
            response = render(request, 'users/redirect_with_cookie.html', context={'user_id': user_id})
            response.set_cookie("user_id", user_id, httponly=True, samesite='Lax')
            return response
    
        else:
            error_string = response.get("error", "")
            try:
                # извлекаем JSON из текста ошибки (после ":")
                if ":" in error_string:
                    json_part = error_string.split(":", 1)[1].strip()
                    error_data = json.loads(json_part)
                else:
                    error_data = {}

                detail = error_data.get("detail")
                if isinstance(detail, list):
                    for item in detail:
                        loc = item.get("loc", [])
                        msg = item.get("msg", "Ошибка")
                        if "password" in loc and item.get("type") == "string_too_short":
                            messages.error(request, "Пароль должен содержать не менее 8 символов.")
                else:
                    messages.error(request, "Ошибка при регистрации.")
            except Exception as e:
                print("Error parsing error detail:", e)
                messages.error(request, "Ошибка при регистрации.")
    return render(request, 'users/register.html')

def loginPage(request):
    page = 'login'
    
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
 
        data = {"username": username, "password": password}
        print("Отправляем в FastAPI:", data)
        response, status_code = fastapi_request('auth/login', method='POST', data=data)

        if status_code == 200:
            user_data = response.get("data", {})
            user_id = user_data.get("id")

            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_unusable_password() 
                user.save()

            login(request, user)
            response = render(request, 'users/redirect_with_cookie.html', context={'user_id': user_id})
            response.set_cookie("user_id", user_id, httponly=True, samesite='Lax')
            return response
        else:
            messages.error(request, f"Ошибка при логине")
 
    context = {"page":page}
    return render(request, 'users/login.html', context=context)

@login_required
def dashboard_redirect_view(request):
    print('зашел в функцию dashboard_redirect_view')
    user_id = request.COOKIES.get("user_id")
    if not user_id:
        return redirect('login')
    
    return redirect_dashboard(request.user, user_id)


def redirect_dashboard(user, user_id):
    print(f"username в джанго: {user.username}")

    response_user_info_cache_key = f'user_{user_id}_info'
    status_code_user_info_cache_key = f'user_{user_id}_info_status_code'
    response = cache.get(response_user_info_cache_key)
    status_code = cache.get(status_code_user_info_cache_key)

    if not response:
        response, status_code = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
        cache.set(response_user_info_cache_key, response, 60*60)
        cache.set(status_code_user_info_cache_key, status_code, 60*60)

    if status_code != 200 or "data" not in response:
        print("Ошибка получения пользователя")
        return redirect("login")
    
    user_role = response["data"].get("role")
    print(f'user role: {user_role}')

    if user_role.lower() == 'student':
        return redirect('student-home')
    elif user_role.lower() == 'teacher':
        return redirect('teacher-home')
    else:
        messages.error('Unknown user')
        return redirect('login')
    

def logoutUser(request):
    response = redirect('login')
    response.delete_cookie("user_id")
    logout(request)
    return response
    
# Student page views
@login_required
def student_home(request):
    user_id = request.COOKIES.get("user_id")
    print(f'user_id = {user_id}')
    if not user_id:
        # messages.error(request, 'Ошибка получения user_id из куки')
        print('Ошибка получения user_id из куки')
        return redirect('login')
    
    print("=== Student Home View Started ===")
    response_user_info_cache_key = f'user_{user_id}_info'
    status_code_user_info_cache_key = f'user_{user_id}_info_status_code'
    response = cache.get(response_user_info_cache_key)
    status_code = cache.get(status_code_user_info_cache_key)
    if not response:
        response, status_code = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
        cache.set(response_user_info_cache_key, response, 60*60)
        cache.set(status_code_user_info_cache_key, status_code, 60*60)

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

    print(f'data for student context = {data}')
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

@login_required
def submission_topics(request, submission_id):
    user_id = request.COOKIES.get("user_id")
    if not user_id:
        messages.error(request, 'Ошибка получения user_id из куки')
        return redirect('login')
    
    response_user_info_cache_key = f'user_{user_id}_info'
    status_code_user_info_cache_key = f'user_{user_id}_info_status_code'
    response = cache.get(response_user_info_cache_key)
    status_code = cache.get(status_code_user_info_cache_key)
    if not response:
        response, status_code = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
        cache.set(response_user_info_cache_key, response, 60*60)
        cache.set(status_code_user_info_cache_key, status_code, 60*60)

    if status_code != 200:
        messages.error(request, "Ошибка получения информации о студенте")
        return redirect('login')
    data = response.get("data", {})
    role = data.get("role", None)

    if request.method == 'POST':
        print("224")
        file = request.FILES.get('file')
        submission_topic_id = request.POST.get('submission_topic_id')
        print(file, submission_topic_id)

        if not file or not submission_topic_id:
            print("229")
            print('Файл или submission_topic_id не переданы')
            return redirect('submission-topics', submission_id=submission_id)
        
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
        return redirect('submission-topics', submission_id=submission_id)

    topics_data, status = fastapi_request(f"submission/{submission_id}/topics", method="GET", use_query_params=True)
    topics = topics_data.get("values", [])
    for topic in topics:
        for comment in topic.get("comments", []):
            try:
                # Добавляем поддержку ISO с микросекундами
                comment["created_at"] = datetime.fromisoformat(comment["created_at"])
            except Exception as e:
                print(f"Ошибка обработки даты комментария: {e}")
    if status != 200:
        messages.error(request, "Ошибка получения информации о топиках работы")
        return  redirect('submission-topics', submission_id=submission_id)
    submission, submission_status = fastapi_request(f"submission/{submission_id}")
    if submission_status != 200:
        messages.error(request, "Ошибка получения информации о работах студента")
        return  redirect('submission-topics', submission_id=submission_id)

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

@login_required
def delete_file(request, file_id):
    user_id = request.COOKIES.get("user_id")
    if not user_id:
        messages.error(request, 'Ошибка получения user_id из куки')
        return redirect('login')
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

    return redirect('submission-topics', submission_id=submission_id)

@login_required
def choose_teacher(request): 
    print("---------------choose teacher view started------------------")
    user_id = request.COOKIES.get("user_id")
    if not user_id:
        messages.error(request, 'Ошибка получения user_id из куки')
        return redirect('login')
    print(f'user_id = {user_id}')
    response_user_info_cache_key = f'user_{user_id}_info'
    status_code_user_info_cache_key = f'user_{user_id}_info_status_code'
    response = cache.get(response_user_info_cache_key)
    status_code = cache.get(status_code_user_info_cache_key)
    if not response:
        response, status_code = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
        cache.set(response_user_info_cache_key, response, 60*60)
        cache.set(status_code_user_info_cache_key, status_code, 60*60)

    if status_code != 200:
        messages.error(request, "Не удалось получить информацию о студенте")
        return redirect('student-home')
    
    student_data = response.get("data", {})
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
            # обновление кеша после пост запроса
            # response, status_code = fastapi_request(f"user/{user_id}/info", method='GET', use_query_params=True)
            # cache.set(response_user_info_cache_key, response, 60*60)
            # cache.set(status_code_user_info_cache_key, status_code, 60*60)
            cache.delete(f"user_{user_id}_info")
            cache.delete(f"user_{user_id}_info_status_code")
            cache.delete(f"user_{teacher_id}_info")
            cache.delete(f"user_{teacher_id}_info_status_code")
            return redirect('student-assignments')    
        else:
            messages.error(request, f"error creating assignment: {create_assignmenent}")
            return redirect('choose-teacher')
    
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

@login_required
def assignment_statuses(request):
    user_id = request.COOKIES.get("user_id")
    if not user_id:
        messages.error(request, 'Ошибка получения user_id из куки')
        return redirect('login')
    
    response_user_info_cache_key = f'user_{user_id}_info'
    status_code_user_info_cache_key = f'user_{user_id}_info_status_code'
    response = cache.get(response_user_info_cache_key)
    status_code = cache.get(status_code_user_info_cache_key)
    if not response:
        response, status_code = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
        cache.set(response_user_info_cache_key, response, 60*60)
        cache.set(status_code_user_info_cache_key, status_code, 60*60)

    if status_code != 200:
        messages.error(request, "Ошибка при получении заявок")
        return redirect("student-home")
    student_data = response.get("data", {})
    role = student_data.get("role", None)
    assignments = response.get("data", {}).get("assignment_subordinate", [])

    for assignment in assignments:
        teacher_id = assignment.get("teacher_id")
        if teacher_id:
            response_user_info_cache_key = f'user_{teacher_id}_info'
            status_code_user_info_cache_key = f'user_{teacher_id}_info_status_code'
            teacher_info = cache.get(response_user_info_cache_key)
            teacher_status = cache.get(status_code_user_info_cache_key)
            if not teacher_info:
                teacher_info, teacher_status = fastapi_request(f"user/{teacher_id}/info", method="GET", use_query_params=True)
                cache.set(response_user_info_cache_key, teacher_info, 60*60)
                cache.set(status_code_user_info_cache_key, teacher_status, 60*60)

            if teacher_status == 200:
                teacher_data = teacher_info.get("data", {})
                assignment["teacher"] = {
                    "first_name": teacher_data.get("first_name", ""),
                    "last_name": teacher_data.get("last_name", ""),
                    "middle_name": teacher_data.get("middle_name", "")
                }
    print(f'assigmnents statuses = {assignments}')
    context = {"assignments": assignments, 'data': student_data, 'role': role, 'user_id': user_id}
    return render(request, 'users/assignment_statuses.html', context=context)
 
@login_required
def my_works(request):
    user_id = request.COOKIES.get("user_id")
    if not user_id:
        messages.error(request, 'Ошибка получения user_id из куки')
        return redirect('login')
    
    response_user_info_cache_key = f'user_{user_id}_info'
    status_code_user_info_cache_key = f'user_{user_id}_info_status_code'
    response = cache.get(response_user_info_cache_key)
    status_code = cache.get(status_code_user_info_cache_key)
    if not response:
        response, status_code = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
        cache.set(response_user_info_cache_key, response, 60*60)
        cache.set(status_code_user_info_cache_key, status_code, 60*60)

    data = response.get("data", {})
    role = data.get("role", None)
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
    
    teacher_id = teacher_first_name = teacher_last_name = teacher_middle_name = None
    submission_values = []

    if is_accepted and assignment_id:
        try:
            assignment_response, assignment_status_code = fastapi_request(
                f"assignment/{assignment_id}", method="GET", use_query_params=True
            )
            assignment_data = assignment_response.get("data", {})
            teacher = assignment_data.get("teacher", {})
            teacher_id = teacher.get("teacher_id")
            teacher_first_name = teacher.get("first_name")
            teacher_last_name = teacher.get("last_name")
            teacher_middle_name = teacher.get("middle_name")

            submission_response, submission_status_code = fastapi_request(
                f"assignment/{assignment_id}/submissions", method="GET", use_query_params=True
            )
            if submission_status_code == 200:
                submission_values = submission_response.get("values", [])

        except Exception as e:
            print(f"Ошибка при получении работ: {e}")

    context = {
        'data': data,
        'user_id': user_id,
        'role': role,
        'submission_values': submission_values,
        'teacher_id': teacher_id,
        'teacher_first_name': teacher_first_name,
        'teacher_last_name': teacher_last_name,
        'teacher_middle_name': teacher_middle_name,
        'is_accepted': is_accepted,
    }

    return render(request, 'users/my_works.html', context=context)

# ===============================================================================================================================
# teacher page views
@login_required
def teacher_home(request):
    user_id = request.COOKIES.get("user_id")
    if not user_id:
        messages.error(request, 'Ошибка получения user_id из куки')
        return redirect('login')
    print("=== Teacher Home View Started ===")
    print(f"teacher_id = {user_id}")
    response_user_info_cache_key = f'user_{user_id}_info'
    status_code_user_info_cache_key = f'user_{user_id}_info_status_code'
    response = cache.get(response_user_info_cache_key)
    status_code = cache.get(status_code_user_info_cache_key)
    if not response:
        response, status_code = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
        cache.set(response_user_info_cache_key, response, 60*60)
        cache.set(status_code_user_info_cache_key, status_code, 60*60)

    if status_code != 200:
        messages.error(request, "Ошибка получения информации о преподователе") 
        return redirect('login')
    
    data = response.get("data", {})
    role = data.get("role", None)
    print(f'teacher role = {role}')
    assignments = data.get("assignment_supervisor", [])
    student_requests_num = len([asgn for asgn in assignments if asgn["is_accepted"] is None])
    active_assignments, active_assignments_status = fastapi_request(f"teacher/list-students", method="GET", data={"teacher_id": user_id}, use_query_params=True)
    if active_assignments_status != 200:
        messages.error(request, "Ошибка при получении списка студентов")
        return redirect("teacher-home")
    students = active_assignments.get("values", [])
    
    context = {'role': role, 'user_id': user_id, 'student_requests_num': student_requests_num, 'students': students, 'data': data}
    
    return render(request, 'users/teacher_home.html', context=context)

@login_required
def review_assignment(request):
    user_id = request.COOKIES.get("user_id")
    if not user_id:
        messages.error(request, 'Ошибка получения user_id из куки')
        return redirect('login')
    
    response_user_info_cache_key = f'user_{user_id}_info'
    status_code_user_info_cache_key = f'user_{user_id}_info_status_code'
    response = cache.get(response_user_info_cache_key)
    status_code = cache.get(status_code_user_info_cache_key)
    if not response:
        response, status_code = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
        cache.set(response_user_info_cache_key, response, 60*60)
        cache.set(status_code_user_info_cache_key, status_code, 60*60)

    if status_code != 200:
        messages.error(request, "Ошибка получения информации о преподавателе")
        return redirect('login')
    
    data = response.get("data", {})
    role = data.get("role", None)   
    assignments = data.get("assignment_supervisor", [])

    # Добавляем инфу о студентах в заявки
    for assignment in assignments:
        student_id = assignment.get("student_id")
        if student_id:
            response_user_info_cache_key = f'user_{student_id}_info'
            status_code_user_info_cache_key = f'user_{student_id}_info_status_code'
            student_info = cache.get(response_user_info_cache_key)
            student_status = cache.get(status_code_user_info_cache_key)
            if not student_info:
                student_info, student_status = fastapi_request(f"user/{student_id}/info", method="GET", use_query_params=True)
                cache.set(response_user_info_cache_key, student_info, 60*60)
                cache.set(status_code_user_info_cache_key, student_status, 60*60)

            if student_status == 200:
                student_data = student_info.get("data", {})
                student_group = student_data.get("group")
                if student_group:
                    group_name = student_group.get("group_name")
                else:
                    group_name = "Группа не указана"
                assignment["student"] = {
                    "first_name": student_data.get("first_name", ""),
                    "last_name": student_data.get("last_name", ""),
                    "middle_name": student_data.get("middle_name", ""),
                    "group": group_name
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
                    messages.info(request, "Заявка успешно принята")
                else:
                    messages.error(request, "Ошибка приянтия заявки")
            elif action == 'decline':
                response, status = fastapi_request('teacher/decline-assignment', method='PATCH', data=action_data, use_query_params=False)
                if status == 200:
                    messages.info(request, "Заявка отклонена")
                else:
                    messages.error(request, "Ошибка отклонения заявки")
            
            cache.delete(f'user_{user_id}_info')
            cache.delete(f'user_{user_id}_info_status_code')

            for assignment in assignments:
                student_id = assignment.get("student_id")
                if student_id:
                    cache.delete(f'user_{student_id}_info')
                    cache.delete(f'user_{student_id}_info_status_code')

            return redirect('review-assignment')
        except:
            messages.error(request, "Ошибка обработки заявки")
            return redirect('review-assignment')
    context = {'role': role, 'user_id': user_id, 'data': data, 'assignments': assignments}
    return render(request, 'users/review_assignment.html', context=context)

@login_required
def create_submission(request): # функция которая создает работу для студетов
    user_id = request.COOKIES.get("user_id")
    if not user_id:
        messages.error(request, 'Ошибка получения user_id из куки')
        return redirect('login')
    
    research_works = {
        'ВКР': 1,
        'НИР': 2,
        'УИР': 3,
        'Зимняя практика': 4,
        'Летняя практика': 5
    } # пока что так, когда появится ручка, нужно ее заменить

    response_user_info_cache_key = f'user_{user_id}_info'
    status_code_user_info_cache_key = f'user_{user_id}_info_status_code'
    response = cache.get(response_user_info_cache_key)
    status_code = cache.get(status_code_user_info_cache_key)
    if not response:
        response, status_code = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
        cache.set(response_user_info_cache_key, response, 60*60)
        cache.set(status_code_user_info_cache_key, status_code, 60*60)

    if status_code != 200:
        messages.error(request, "Ошибка получения информации о преподавателе")
        return redirect('login')
    data = response.get("data", {})
    role = data.get("role", None)
    list_students, list_students_status = fastapi_request(f"teacher/list-students", method="GET", data={"teacher_id":user_id}, use_query_params=True)
    if list_students_status != 200:
        messages.error(request, "Ошибка получения списка студентов")
        return redirect('teacher-home')
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
                    messages.info(request, "Работа успешно создана")
            else:
                messages.error(request, "Ошибка создания работы")
        except Exception as e:
            print(f"Ошибка при создании submission: {e}")
            messages.error(request, 'Ошибка создания работы')
            return redirect('teacher-home')
        
    context = {
        'role': role,
        'data': data,
        'user_id': user_id,
        'research_works': research_works,
        'students': students
    }
    return render(request, 'users/create_submission.html', context=context)

@login_required
def review_submissions(request):
    user_id = request.COOKIES.get("user_id")
    if not user_id:
        messages.error(request, 'Ошибка получения user_id из куки')
        return redirect('login')
    
    response_user_info_cache_key = f'user_{user_id}_info'
    status_code_user_info_cache_key = f'user_{user_id}_info_status_code'
    response = cache.get(response_user_info_cache_key)
    status_code = cache.get(status_code_user_info_cache_key)
    if not response:
        response, status_code = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
        cache.set(response_user_info_cache_key, response, 60*60)
        cache.set(status_code_user_info_cache_key, status_code, 60*60)

    if status_code != 200:
        messages.error(request, "Ошибка получения информации о преподавателе")
        return redirect('login')
    data = response.get("data", {})
    role = data.get("role", None)
    list_students, list_students_status = fastapi_request(f"teacher/list-students", method="GET", data={"teacher_id":user_id}, use_query_params=True)
    if list_students_status != 200:
        messages.error(request, "Ошибка получения списка студентов")
        return redirect('teacher-home')
    students = list_students.get("values", [])
    context = {
        'role': role,
        'data': data,
        'user_id': user_id,
        'students': students
    }
    return render(request, 'users/review_submissions.html', context=context)

@login_required
def review_student_submission(request, student_id, assignment_id):
    user_id = request.COOKIES.get("user_id")
    if not user_id:
        messages.error(request, 'Ошибка получения user_id из куки')
        return redirect('login')
    
    response_user_info_cache_key = f'user_{user_id}_info'
    status_code_user_info_cache_key = f'user_{user_id}_info_status_code'
    response = cache.get(response_user_info_cache_key)
    status_code = cache.get(status_code_user_info_cache_key)
    if not response:
        response, status_code = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
        cache.set(response_user_info_cache_key, response, 60*60)
        cache.set(status_code_user_info_cache_key, status_code, 60*60)

    if status_code != 200:
        messages.error(request, "Ошибка получения информации о преподавателе")
        return redirect('login')
    data = response.get("data", {})
    role = data.get("role", None)
    submissions, submission_status = fastapi_request(f"assignment/{assignment_id}/submissions")
    if submission_status != 200:
        messages.error(request, "Ошибка получения информации о работах студента")
        return redirect('review-submissions')
    submissions_values = submissions.get("values", [])
    research_works = {
        1: 'ВКР',
        2: 'НИР',
        3: 'УИР',
        4: 'Зимняя практика',
        5: 'Летняя практика'
    }
    context = {
        'role': role,
        'data': data,
        'user_id': user_id,
        'submissions_values': submissions_values,
        'student_id': student_id,
        'assignment_id': assignment_id,
        'research_works': research_works
    }
    return render(request, 'users/review_student_submission.html', context=context)

@login_required
def edit_work(request, submission_id, student_id, assignment_id):
    user_id = request.COOKIES.get("user_id")
    if not user_id:
        messages.error(request, 'Ошибка получения user_id из куки')
        return redirect('login')
    title = request.POST.get("submission_title")
    researchwork_id = request.POST.get("researchwork_id")


    payload = {
        "submission_id": int(submission_id),
        "submission_title": title,
        "researchwork_id": int(researchwork_id)
    }
    response, status_code = fastapi_request(f'submission/{submission_id}', method='PATCH', data=payload)

    if status_code == 200:
        messages.success(request, "Работа успешна обновлена")
    else:
        messages.error(request, "Ошибка при обновлении работы")
    return redirect("review-student-submission", student_id=student_id, assignment_id=assignment_id)

@login_required
def review_topics(request, submission_id):
    user_id = request.COOKIES.get("user_id")
    if not user_id:
        messages.error(request, 'Ошибка получения user_id из куки')
        return redirect('login')
    
    response_user_info_cache_key = f'user_{user_id}_info'
    status_code_user_info_cache_key = f'user_{user_id}_info_status_code'
    response = cache.get(response_user_info_cache_key)
    status_code = cache.get(status_code_user_info_cache_key)
    if not response:
        response, status_code = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
        cache.set(response_user_info_cache_key, response, 60*60)
        cache.set(status_code_user_info_cache_key, status_code, 60*60)

    if status_code != 200:
        messages.error(request, "Ошибка получения информации о преподавателе")
        return redirect('login')
    data = response.get("data", {})
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
        
        return redirect('review-topics', submission_id=submission_id)

    topics_data, status = fastapi_request(f"submission/{submission_id}/topics", method="GET", use_query_params=True)
    topics = topics_data.get("values", [])
    for topic in topics:
        for comment in topic.get("comments", []):
            try:
                # Добавляем поддержку ISO с микросекундами
                comment["created_at"] = datetime.fromisoformat(comment["created_at"])
            except Exception as e:
                print(f"Ошибка обработки даты комментария: {e}")
    if status != 200:
        messages.error(request, "Ошибка получения информации о топиках работы")
        return redirect('review-student-submission')
    submission, submission_status = fastapi_request(f"submission/{submission_id}")
    if submission_status != 200:
        messages.error(request, "Ошибка получения информации о работах студента")
        return redirect('review-submissions')

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
def edit_profile(request):
    user_id = request.COOKIES.get("user_id")
    if not user_id:
        messages.error(request, 'Ошибка получения user_id из куки')
        return redirect('login')
    
    response_user_info_cache_key = f'user_{user_id}_info'
    status_code_user_info_cache_key = f'user_{user_id}_info_status_code'
    response = cache.get(response_user_info_cache_key)
    status_code = cache.get(status_code_user_info_cache_key)
    if not response:
        response, status_code = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
        cache.set(response_user_info_cache_key, response, 60*60)
        cache.set(status_code_user_info_cache_key, status_code, 60*60)

    response_data = response.get("data", {})
    role = response_data.get("role", None)  

    groups = cache.get("groups")
    if not groups:
        groups_response, groups_status = fastapi_request('student/list-groups', method='GET')
        groups = groups_response.get("values", [])
        # groups.append({'id': 283, 'group_name': 'М23-534'})
        # groups.append({'id': 284, 'group_name': 'М23-514'})
        # groups.append({'id': 285, 'group_name': 'М23-524'})
        # groups.append({'id': 286, 'group_name': 'М23-504'})
        cache.set("groups", groups, 60*100)

    data = {}
    group_error = None
    group_name_input = ""
    group_id = 0

    if request.method == 'POST':
        group_name_input = request.POST.get("group_name", "").strip()
        print(f"group_name_input = {group_name_input}")
        # print(f"groups = {groups}")
        
        if role and role.lower() == 'student':
            group_match = next((g for g in groups if g["group_name"].strip().lower() == group_name_input.strip().lower()), None)
            print(f'group_match = {group_match}')
            if not group_match:
                group_error = "Такой группы не существует."
            else:
                group_id = group_match["id"]

        if (role and role.lower() == 'teacher') or (role.lower() == 'student' and not group_error):
            updated_data = {
                "email": request.POST.get("email"),
                "first_name": request.POST.get("first_name"),
                "last_name": request.POST.get("last_name"),
                "middle_name": request.POST.get("middle_name"),
                "about_me": request.POST.get("about_me")
            }

            if role.lower() == 'student':
                updated_data["group_id"] = group_id

            data = {
                "target": {
                    "user_id": user_id
                },
                "data": updated_data
            }
            
            set_info_response, set_info_status_code = fastapi_request(f"user/set-info", method="PATCH", data=data)

            if set_info_status_code == 201:
                print(f"Данные пользователя успешно обновлены: {set_info_response}")
                messages.success(request, "Данные пользователя успешно обновлены.")

                updated_response, updated_status_code = fastapi_request(f'user/{user_id}/info', method='GET', use_query_params=True)
                cache.set(response_user_info_cache_key, updated_response, 60*60)
                cache.set(status_code_user_info_cache_key, updated_status_code, 60*60)
                response_data = updated_response.get("data", {})
            else:
                print(f"Ошибка изменения данных пользователя: {set_info_response}")
                messages.error(request, f"Ошибка: {response.get('error', 'Неизвестная ошибка')}")

    print(f'updated data after editing users profile = {response_data}')
    if role and role.lower() == 'student':
        group = response_data.get("group", {})
        if group:
            group_name_input = group.get("group_name")

    context = {
        "data": response_data,
        "role": role,
        "user_id": user_id,
        "groups": groups,
        "group_error":group_error,
        "group_name": group_name_input
    }
    # print(f"context for edit profile: {context}")
    return render(request, "users/edit_profile.html", context=context)
  
@login_required
def show_statistics(request):
    user_id = request.COOKIES.get("user_id")
    if not user_id:
        messages.error(request, 'Ошибка получения user_id из куки')
        return redirect('login')
    
    students_without_teacher = []
    response_user_info_cache_key = f'user_{user_id}_info'
    status_code_user_info_cache_key = f'user_{user_id}_info_status_code'
    response = cache.get(response_user_info_cache_key)
    status_code = cache.get(status_code_user_info_cache_key)
    if not response:
        response, status_code = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
        cache.set(response_user_info_cache_key, response, 60*60)
        cache.set(status_code_user_info_cache_key, status_code, 60*60)

    response_data = response.get("data", {})
    role = response_data.get("role", None) 
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

@login_required
def export_statistics_excel(request):
    user_id = request.COOKIES.get("user_id")
    if not user_id:
        messages.error(request, 'Ошибка получения user_id из куки')
        return redirect('login')
    
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

def mobile_app_view(request):
    user_id = request.COOKIES.get("user_id")
    if not user_id:
        messages.error(request, 'Ошибка получения user_id из куки')
        return redirect('login')
    
    response_user_info_cache_key = f'user_{user_id}_info'
    status_code_user_info_cache_key = f'user_{user_id}_info_status_code'
    response = cache.get(response_user_info_cache_key)
    status_code = cache.get(status_code_user_info_cache_key)
    if not response:
        response, status_code = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
        cache.set(response_user_info_cache_key, response, 60*60)
        cache.set(status_code_user_info_cache_key, status_code, 60*60)

    response_data = response.get("data", {})
    role = response_data.get("role", None)  

    context = {'data': response_data, 'user_id': user_id, 'role': role}
    return render(request, 'users/mobile_app.html', context=context)

@login_required
def notifications(request):
    user_id = request.COOKIES.get("user_id")
    if not user_id:
        return redirect('login')
    
    response_user_info_cache_key = f'user_{user_id}_info'
    status_code_user_info_cache_key = f'user_{user_id}_info_status_code'
    response = cache.get(response_user_info_cache_key)
    status_code = cache.get(status_code_user_info_cache_key)
    if not response:
        response, status_code = fastapi_request(f"user/{user_id}/info", method="GET", use_query_params=True)
        cache.set(response_user_info_cache_key, response, 60*60)
        cache.set(status_code_user_info_cache_key, status_code, 60*60)

    response_data = response.get("data", {})
    role = response_data.get("role", None)  

    notifications_response, status = fastapi_request(f"user/{user_id}/notifications", method="GET", use_query_params=True)
    notifications = []

    if status == 200:
        for notif in notifications_response.get("values", []):
            message = None
            notif_type = notif["type"]
            entities = {e["entity_model"]: e["entity_id"] for e in notif.get("entities", [])}
            topic_name = None
            file_name = None
            submission_id = None
            submission_topic_id = None
            student_full_name = None

            for entity in notif.get("entities", []):
                if entity["entity_model"] == "submission":
                    submission_id = entity["entity_id"]
                elif entity["entity_model"] == "submission_topic":
                    submission_topic_id = entity["entity_id"]

            #Если студент
            if role.lower() == "student" and notif_type in ["submission_accepted", "submission_declined"]:
                if notif_type == "submission_accepted":
                    message = "Преподаватель принял вашу работу."
                elif notif_type == "submission_declined":
                    message = "Преподаватель отклонил вашу работу."
                topic_id = entities.get("submission_topic")
                topic_name = None
                submission_title = None
                created_at = notif["created_at"]
                is_read = notif["is_read"]
                comment = None
                sub_id = entities.get("submission")
                topic_id = entities.get("submission_topic")
                if sub_id and topic_id:
                    topics_resp, topics_status = fastapi_request(f"submission/{sub_id}/topics", method="GET", use_query_params=True)
                    if topics_status == 200:
                        for topic in topics_resp.get("values", []):
                            if topic["id"] == topic_id:
                                topic_name = topic.get("topic", {}).get("name")
                                submission_title = topic["submission"]["submission_title"]
                                if topic["comments"]:
                                    comment = topic["comments"][0]["comment"]
                notifications.append({
                    "id": notif["id"], 
                    "type": notif_type,
                    "message": message,
                    "topic_name": topic_name,
                    "submission_title": submission_title,
                    "comment": comment,
                    "created_at": created_at,
                    "is_read": is_read,
                })

            # Если преподаватель
            elif role.lower() == "teacher":
                if notif_type == "file_added":
                    sub_id = entities.get("submission")
                    topic_name = None
                    submission_title = None
                    file_name = None
                    file_id = entities.get("file")
                    user_profile_id = entities.get("user_profile")
                    # можно использовать submission/{id}/topics чтобы узнать тему
                    if sub_id:
                        topics_resp, topics_status = fastapi_request(f"submission/{sub_id}/topics", method="GET", use_query_params=True)
                        if topics_status == 200:
                            topics = topics_resp.get("values", [])
                            if topics:
                                topic = topics[0]
                                topic_name = topic.get("topic", {}).get("name")
                                submission_title = topic["submission"]["submission_title"]
                                if topic["files"]:
                                    file_name = topic["files"][0]["original_filename"]
                                    student_id = topic.get("submission", {}).get("student_id")
                                    student_full_name = None

                                    if student_id:
                                        student_resp, student_status = fastapi_request(f"user/{student_id}/info", method="GET", use_query_params=True)
                                        if student_status == 200:
                                            sdata = student_resp.get("data", {})
                                            first = sdata.get("first_name", "")
                                            last = sdata.get("last_name", "")
                                            middle = sdata.get("middle_name", "")
                                            student_full_name = f"{last} {first} {middle}".strip()

                    notifications.append({
                        "id": notif["id"],  
                        "created_at": notif["created_at"],
                        "is_read": notif["is_read"],
                        "topic_name": topic_name,
                        "submission_title": submission_title,
                        "type": notif_type,
                        "student_full_name": student_full_name,
                         "file_name": file_name,
                         "message": f"Студент {student_full_name} загрузил файл по теме вашей работы" if student_full_name else None
                    })

    return render(request, 'users/notifications.html', context = {"notifications": notifications, 'user_id': user_id, "data": response_data, "role": role})

