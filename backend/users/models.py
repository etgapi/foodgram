from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from users.validators import (
    first_name_validator,
    last_name_validator,
)

MAX_NAME_LENGTH = 150  # Максимальная длина имени
MAX_EMAIL_LENGTH = 254  # Максимальная длина электронной почты


class User(AbstractUser):
    """Модель для пользователей"""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name',
        'password',
    )

    username = models.CharField(
        "Логин",
        max_length=MAX_NAME_LENGTH,
        validators=[UnicodeUsernameValidator(
            message='Имя пользователя содержит недопустимые символы'
        )],
        unique=True,
        error_messages={
            'unique': 'Пользователь с таким именем уже существует',
        }
    )
    password = models.CharField(
        "Пароль",
        max_length=150,
    )
    email = models.EmailField(
        "Адрес электронной почты",
        max_length=MAX_EMAIL_LENGTH,
        unique=True,
        error_messages={
            'unique': 'Такая почта уже зарегистрирована',
        },
    )
    first_name = models.CharField(
        "Имя",
        max_length=MAX_NAME_LENGTH,
        validators=(first_name_validator,)
    )
    last_name = models.CharField(
        "Фамилия",
        max_length=MAX_NAME_LENGTH,
        validators=(last_name_validator,)
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to='avatars/',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "пользователя"
        verbose_name_plural = "Пользователи"
        ordering = ["username"]

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Модель для подписчиков"""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Автор",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик",
    )

    class Meta:
        ordering = ["author_id"]
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"],
                name="Вы уже подписаны на этого автора"
            ),
        ]

    def clean(self):
        if self.user == self.author:
            raise ValidationError('Невозможно подписаться на себя')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def str(self):
        return f"{self.user} подписался на {self.author}"
