from django.contrib import admin
from .models import Assignment, Submission, File, Comment, Chat, Message

# Register your models here.

admin.site.register(Assignment)
admin.site.register(Submission)
admin.site.register(File)
admin.site.register(Comment)
admin.site.register(Chat)
admin.site.register(Message)
