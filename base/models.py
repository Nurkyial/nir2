from django.db import models
from users.models import UserProfile

# Create your models here.
class ResearchWork(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    def __str__(self):
        return self.name
    
class Topic(models.Model):
    research_work = models.ForeignKey(ResearchWork, related_name='topics', on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        if self.research_work is None:
            return f"Unassigned - {self.name}"
        return f"{self.research_work.name} - {self.name}"

class Assignment(models.Model):
    student = models.ForeignKey(UserProfile, related_name='student_assignment', on_delete=models.CASCADE)
    teacher = models.ForeignKey(UserProfile, related_name='teacher_assignment', on_delete=models.CASCADE)
    is_accepted = models.BooleanField(default=False) # charfield
    is_reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    text = models.TextField(blank=True)
    
    
    def __str__(self):
        return f"Assignment for {self.student.user.username} with {self.teacher.user.username}"
    
    
class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    SEMESTER_CHOICES = (
        ('1', 'Semester 1'),
        ('2', 'Semester 2'),
        ('3', 'Semester 3'),
        ('4', 'Semester 4'),
        ('5', 'Semester 5'),
        ('6', 'Semester 6'),
        ('7', 'Semester 7'),
        ('8', 'Semester 8'),
    )
    semester = models.CharField(max_length=100, null=True, choices=SEMESTER_CHOICES)
    research_work = models.ForeignKey(ResearchWork, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    
    
    def __str__(self):
        research_work_name = "No Research Work Assigned" if self.research_work is None else self.research_work.name
        return f"{research_work_name} - for student {self.assignment.student.user.username} in semester - {self.semester}"

 


class File(models.Model):
    topic = models.ForeignKey(Topic, related_name='files', on_delete=models.CASCADE, null=True)
    submission = models.ForeignKey(Submission, related_name='files', on_delete=models.CASCADE, null=True)
    filename = models.FileField(upload_to='submissions/', null=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)
    is_reviewed = models.BooleanField(default=False)
    comment = models.TextField(null=True, blank=True) 
    def __str__(self):
        return f"File: {self.filename.name} for Topic: {self.topic.name}"
    

# class Comment(models.Model):
#     file_comment = models.OneToOneField(File, on_delete=models.CASCADE, related_name='detailed_comment')
#     text = models.TextField(null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     def __str__(self):
#         return f"Comment for {self.file_comment.filename}"

# class UserChatM2m(models.Model):
#     user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
#     chat = models.ForeignKey("Chat", on_delete=models.CASCADE)
#     is_admin = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
    
# class Chat(models.Model):
#     assignment = models.OneToOneField(Assignment, on_delete=models.CASCADE, related_name='chat') #many to many with user
#     created_at = models.DateTimeField(auto_now_add=True)
    
    
# class Message(models.Model):
#     chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
#     sender = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='sender')
#     text = models.TextField()
#     timestamp = models.DateTimeField(auto_now_add=True)
    
#     def __str__(self):
#         return f"message from sender {self.sender.user.username}: '{self.text[:50]}"
      