from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('login/', views.loginPage, name='login'),
    path('logout/', views.logoutUser, name='logout'),
    path('student/<int:user_id>/', views.student_home, name='student-home'),
    path('teacher/<int:user_id>/', views.teacher_home, name='teacher-home'),
    path('research-work/<int:rw_id>/<int:subm_id>/', views.research_work_detail, name='research-work-detail'),
    path('topics/<int:rw_id>/<int:topic_id>/<int:subm_id>/', views.upload_page, name='upload-page'),
    path('upload-file/<int:subm_id>/<int:topic_id>/', views.upload_file, name='upload-file'),
    path('choose-teacher/<int:user_id>/', views.choose_teacher, name='choose-teacher'),
    path('student-work-detail/<int:as_id>/', views.student_work_detail, name='student-work-detail'),
    path('submission-topics/<int:sub_id>/', views.submission_topics, name='submission-topics'),
    path('topics-files/<int:sub_id>/<int:topic_id>/', views.topics_files, name='topics-files'),
    path('edit-profile/<int:user_id>/', views.edit_profile, name='edit-profile'),
    path('student/<int:user_id>/assignments/', views.assignment_statuses, name="student-assignments"),
    path('review-assignment/<int:user_id>/', views.review_assignment, name='review-assignment'),
    path('create-submission/<int:user_id>/', views.create_submission, name='create-submission')
]
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)

