# Generated by Django 3.2.3 on 2024-06-18 17:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_follow_date_added'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='follow',
            name='date_added',
        ),
    ]
