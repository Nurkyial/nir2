from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('register/', views.registerPage, name='register'),
    path('login/', views.loginPage, name='login'),
    path('logout/', views.logoutUser, name='logout'),
    path('student/', views.student_home, name='student-home'),
    path('teacher/', views.teacher_home, name='teacher-home'),
    path('submission-topics/<int:submission_id>/', views.submission_topics, name='submission-topics'),
    path('choose-teacher/', views.choose_teacher, name='choose-teacher'),
    path('edit-profile/', views.edit_profile, name='edit-profile'),
    path('student/assignments/', views.assignment_statuses, name="student-assignments"),
    path('review-assignment/', views.review_assignment, name='review-assignment'),
    path('create-submission//', views.create_submission, name='create-submission'),
    path('review-submissions/', views.review_submissions, name='review-submissions'),
    path('review-student-submission/<int:student_id>/<int:assignment_id>/', views.review_student_submission, name='review-student-submission'),
    path('review-topics/<int:submission_id>', views.review_topics, name='review-topics'),
    path('download-file/<int:file_id>/', views.download_file, name='download-file'),
    path('delete-file/<int:file_id>/', views.delete_file, name='delete-file'),
    path('show-statistics/', views.show_statistics, name='show-statistics'),
    path('export-statistics-excel/', views.export_statistics_excel, name='export-statistics-excel'),
    path('edit-work/<int:submission_id>/<int:student_id>/<int:assignment_id>/edit/', views.edit_work, name='edit-work'),
    path('mobile-app/', views.mobile_app_view, name='mobile-app'),
    path('redirect-dashboard/', views.dashboard_redirect_view, name='redirect-dashboard'),
    path('my-works/', views.my_works, name='my-works'),
]
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)

