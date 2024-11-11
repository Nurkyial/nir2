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

class Semester(models.Model):
    semester_name = models.CharField(max_length=100, null=True)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.semester_name}: {self.start_date} - {self.end_date}"  
    
    def is_within_semester(self, date):
        """Проверяет, входит ли дата в диапазое текущего семестра"""
        return self.start_date <= date <= self.end_date

class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    # SEMESTER_CHOICES = (
    #     ('1', 'Semester 1'),
    #     ('2', 'Semester 2'),
    #     ('3', 'Semester 3'),
    #     ('4', 'Semester 4'),
    #     ('5', 'Semester 5'),
    #     ('6', 'Semester 6'),
    #     ('7', 'Semester 7'),
    #     ('8', 'Semester 8'),
    # )
    # semester = models.CharField(max_length=100, null=True, choices=SEMESTER_CHOICES)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, null=True) 
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
    