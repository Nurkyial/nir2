# Generated by Django 5.0.4 on 2024-06-17 21:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0008_delete_comment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userchatm2m',
            name='chat',
        ),
        migrations.RemoveField(
            model_name='message',
            name='chat',
        ),
        migrations.RemoveField(
            model_name='message',
            name='sender',
        ),
        migrations.RemoveField(
            model_name='userchatm2m',
            name='user',
        ),
        migrations.DeleteModel(
            name='Chat',
        ),
        migrations.DeleteModel(
            name='Message',
        ),
        migrations.DeleteModel(
            name='UserChatM2m',
        ),
    ]