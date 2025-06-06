# Generated by Django 5.0.4 on 2024-04-11 14:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_userprofile_middle_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='role',
            field=models.CharField(choices=[('student', 'Student'), ('admin', 'Admin'), ('teacher', 'Teacher')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.group'),
        ),
        migrations.DeleteModel(
            name='Role',
        ),
    ]
