# Generated by Django 3.2.3 on 2024-06-18 17:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_alter_user_avatar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Аватар'),
        ),
    ]
