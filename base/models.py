from django.db import models
from users.models import UserProfile

# Create your models here.
class Assignment(models.Model):
    student = models.ForeignKey(UserProfile, related_name='student_assignment', on_delete=models.CASCADE)
    teacher = models.ForeignKey(UserProfile, related_name='teacher_assignment', on_delete=models.CASCADE)
    is_accepted = models.BooleanField(default=False) # charfield
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    def __str__(self):
        return f"Assignment for {self.student.user.username} with {self.teacher.user.username}"
    
    
class Submission(models.Model):
    topic = models.CharField(max_length=40)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Submission for {self.assignment.student.user.username}"


class File(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    filename = models.FileField(upload_to='submissions/', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Submitted file for {self.submission.topic}"
    

class Comment(models.Model):
    file_comment = models.OneToOneField(File, on_delete=models.CASCADE, related_name='comment')
    text = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comment for {self.file_comment.filename}"

class UserChatM2m(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    chat = models.ForeignKey("Chat", on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
class Chat(models.Model):
    assignment = models.OneToOneField(Assignment, on_delete=models.CASCADE, related_name='chat') #many to many with user
    created_at = models.DateTimeField(auto_now_add=True)
    
    
class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='sender')
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"message from sender {self.sender.user.username}: '{self.text[:50]}"
    
    
    
    
     
    
    