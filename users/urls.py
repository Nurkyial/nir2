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
    path('submission-topics/<int:user_id>/<int:submission_id>/', views.submission_topics, name='submission-topics'),
    path('choose-teacher/<int:user_id>/', views.choose_teacher, name='choose-teacher'),
    path('edit-profile/<int:user_id>/', views.edit_profile, name='edit-profile'),
    path('student/<int:user_id>/assignments/', views.assignment_statuses, name="student-assignments"),
    path('review-assignment/<int:user_id>/', views.review_assignment, name='review-assignment'),
    path('create-submission/<int:user_id>/', views.create_submission, name='create-submission'),
    path('review-submissions/<int:user_id>/', views.review_submissions, name='review-submissions'),
    path('review-student-submission/<int:user_id>/<int:student_id>/<int:assignment_id>/', views.review_student_submission, name='review-student-submission'),
    path('review-topics/<int:user_id>/<int:submission_id>', views.review_topics, name='review-topics'),
    path('download-file/<int:file_id>/', views.download_file, name='download-file'),
    path('delete-file/<int:user_id>/<int:file_id>/', views.delete_file, name='delete-file'),
    path('show-statistics/<int:user_id>/', views.show_statistics, name='show-statistics'),
    path('export-statistics-excel/<int:user_id>/', views.export_statistics_excel, name='export-statistics-excel'),
    path('edit-work/<int:user_id>/<int:submission_id>/<int:student_id>/<int:assignment_id>/edit/', views.edit_work, name='edit-work'),

]
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)

