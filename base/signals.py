from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from models import File

@receiver(post_save, sender=File)
def update_topic_submission_status_on_save(sender, instance, **kwargs):
    topic_submission = instance.topic_submission
    topic_submission.update_status()

@receiver(post_delete, sender=File)
def update_topic_submission_status_on_delete(sender, instance, **kwargs):
    topic_submission = instance.topic_submission
    topic_submission.update_status()
