from django.db import models
from users.models import UserProfile
from django.utils.timezone import now
from django.utils.text import slugify

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
    is_accepted = models.BooleanField(default=False)
    is_reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    text = models.TextField(blank=True)
    # нужно добавить семестр (но не сейчас)
    
    def __str__(self):
        return f"Assignment for {self.student.user.username} with {self.teacher.user.username}"


class Semester(models.Model):
    SPRING = 'Spring'
    FALL = 'Fall'

    SEMESTER_CHOICES = [
        (SPRING, 'Весенний семестр'),
        (FALL, 'Осенний семестр'),
    ]

    semester_type = models.CharField(
        max_length=10,
        choices=SEMESTER_CHOICES,
        editable=False,  # Тип семестра будет генерироваться автоматически,
        null=True
    )
    semester_name = models.CharField(max_length=100, null=True, blank=True, editable=False)
    start_date = models.DateField()
    end_date = models.DateField()

    def save(self, *args, **kwargs):
        """
        Автоматически генерирует тип семестра и его название перед сохранением.
        """
        # Определяем тип семестра на основе даты начала
        if 1 <= self.start_date.month <= 6:  # Январь - Июнь
            self.semester_type = self.SPRING
        else:  # Июль - Декабрь
            self.semester_type = self.FALL

        # Генерируем учебный год
        self.semester_name = f"{self.get_semester_type_display()} {self.academic_year()} учебного года"

        super().save(*args, **kwargs)

    def academic_year(self):
        """
        Возвращает учебный год в формате 2023/2024 на основе даты начала семестра.
        """
        start_year = self.start_date.year
        if self.semester_type == self.SPRING:
            end_year = start_year
        else:
            end_year = start_year + 1
        return f"{start_year}/{end_year}"

    def __str__(self):
        return self.semester_name

    def is_within_semester(self, date):
        """Проверяет, входит ли дата в диапазон текущего семестра."""
        return self.start_date <= date <= self.end_date


class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, null=True, blank=True) 
    research_work = models.ForeignKey(ResearchWork, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    
    def __str__(self):
        research_work_name = "No Research Work Assigned" if self.research_work is None else self.research_work.name
        return f"{research_work_name} - for student {self.assignment.student.user.username} in semester - {self.semester}"
    
    def create_topic_submission(self):
        """Создаёт TopicSubmission для всех тем, связанных с исследовательской работой."""
        if self.research_work:
            topics = Topic.objects.filter(research_work=self.research_work)
            for topic in topics:
                TopicSubmission.objects.get_or_create(submission=self, topic=topic)

class TopicSubmission(models.Model):
    submission = models.ForeignKey(Submission, related_name='topic_submissions', on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, related_name='topic_submissions', on_delete=models.CASCADE)
    is_accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"Submission {self.submission.id} for Topic {self.topic.name}"
    
    def update_status(self):
        """
        Обновляет поле is_accepted на основе статуса последнего загруженного файла.
        """
        latest_file = self.files.order_by('-upload_date')
        if latest_file:
            self.is_accepted = latest_file.is_accepted
        else:
            self.is_accepted = False
        self.save(update_fields=['is_accepted'])
    
    
class File(models.Model):
    # topic = models.ForeignKey(Topic, related_name='files', on_delete=models.CASCADE, null=True)
    # submission = models.ForeignKey(Submission, related_name='files', on_delete=models.CASCADE, null=True)
    topic_submission = models.ForeignKey(TopicSubmission, related_name='files', on_delete=models.CASCADE, null=True, blank=True) # это нужно удалить
    filename = models.FileField(upload_to='submissions/', null=True) 
    upload_date = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)
    is_reviewed = models.BooleanField(default=False)
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"File: {self.filename.name} for Topic: {self.topic.name}"
    