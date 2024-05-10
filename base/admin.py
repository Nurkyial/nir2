from django.contrib import admin
from .models import Assignment, Submission, File, Comment, Chat, Message, Topic, ResearchWork

# Register your models here.
class FileAdmin(admin.ModelAdmin):
    list_display = ['filename', 'topic', 'submission', 'upload_date']
admin.site.register(Assignment)
admin.site.register(Submission)
admin.site.register(File, FileAdmin)
admin.site.register(Comment)
admin.site.register(Chat)
admin.site.register(Message)
admin.site.register(Topic)
admin.site.register(ResearchWork)

