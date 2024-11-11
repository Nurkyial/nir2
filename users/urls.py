from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('login/', views.loginPage, name='login'),
    path('logout/', views.logoutUser, name='logout'),
    path('home/', views.home, name='home'),
    path('student/<str:pk>/', views.student_home, name='student-home'),
    path('teacher/<str:teacher_id>/', views.teacher_home, name='teacher-home'),
    path('research-work/<int:rw_id>/<str:semester>/<int:subm_id>/', views.research_work_detail, name='research-work-detail'),
    path('topics/<int:rw_id>/<int:topic_id>/<int:subm_id>/', views.upload_page, name='upload-page'),
    path('upload-file/<int:subm_id>/<int:topic_id>/', views.upload_file, name='upload-file'),
    path('choose-teacher/<int:student_id>/', views.choose_teacher, name='choose-teacher'),
    path('student-work-detail/<int:as_id>/', views.student_work_detail, name='student-work-detail'),
    path('submission-topics/<int:sub_id>/', views.submission_topics, name='submission-topics'),
    path('topics-files/<int:sub_id>/<int:topic_id>/', views.topics_files, name='topics-files'),
    path('admin-home/<str:admin_id>/', views.admin_home, name='admin-home'),
    path('admin-students-work/<str:as_id>/', views.admin_students_work, name='admin-students-work'),
    path('admin-submission-details/<str:sub_id>/', views.admin_submission_details, name='admin-submission-details'),
    path('add-user/', views.add_user, name='add-user'),
    path('student/<str:pk>/chat/', views.chat, name='chat'),
]
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)

