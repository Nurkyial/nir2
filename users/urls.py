from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('login/', views.loginPage, name='login'),
    path('student/<str:pk>/', views.student_home, name='student-home'),
    path('research-work/<int:rw_id>/<str:semester>', views.research_work_detail, name='research-work-detail'),
    path('topics/<int:rw_id>/<int:topic_id>', views.upload_page, name='upload-page'),
    path('upload-file/<int:rw_id>/<int:topic_id>', views.upload_file, name='upload-file')
]
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)

