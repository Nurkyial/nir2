# Generated by Django 5.0.4 on 2024-05-11 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_researchwork_rename_created_at_file_upload_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='text',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='submission',
            name='semester',
            field=models.CharField(choices=[('1', 'Semester 1'), ('2', 'Semester 2'), ('3', 'Semester 3'), ('4', 'Semester 4'), ('5', 'Semester 5'), ('6', 'Semester 6'), ('7', 'Semester 7'), ('8', 'Semester 8')], max_length=100, null=True),
        ),
    ]
