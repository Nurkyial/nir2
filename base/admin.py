from django.contrib import admin
from .models import Assignment, Submission, File, Topic, ResearchWork, TopicSubmission, Semester

# Register your models here.
class FileAdmin(admin.ModelAdmin):
    list_display = ['filename', 'topic_submission', 'upload_date', 'is_accepted', 'is_reviewed']
admin.site.register(Assignment)
admin.site.register(Submission)
admin.site.register(File, FileAdmin)
admin.site.register(Topic)
admin.site.register(ResearchWork)
admin.site.register(Semester)
admin.site.register(TopicSubmission)

