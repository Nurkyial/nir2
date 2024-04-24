from django.db import models
from django.contrib.auth.models import User
# Create your models here.

    
class Group(models.Model):
    group_name = models.CharField(max_length=20)
    
    def __str__(self):
        return self.group_name
    
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    middle_name = models.CharField(max_length=30, blank=True, null=True)
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('admin', 'Admin'), 
        ('teacher', 'Teacher')
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, null=True)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} ({self.role if self.role else 'No role'})"
    
    


