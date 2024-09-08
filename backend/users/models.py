from django.conf import settings
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.models import AbstractUser
from django.db import models

from users.constants import MAX_EMAIL_LENGTH, MAX_NAME_LENGTH
from users.validators import (
    first_name_validator,
    last_name_validator,
)


class User(AbstractUser):
    """Модель для пользователей"""

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = (
        "username",
        "first_name",
        "last_name",
        "password",
    )

    email = models.EmailField(
        verbose_name="Адрес электронной почты",
        max_length=MAX_EMAIL_LENGTH,
        unique=True,
        error_messages={
            "unique": "Данный адрес уже существует",
        },
    )

    username = models.CharField(
        verbose_name="Логин",
        max_length=MAX_NAME_LENGTH,
        validators=[
            UnicodeUsernameValidator(
                message="Имя пользователя содержит недопустимые символы"
            )
        ],
        unique=True,
        error_messages={
            "unique": "Пользователь с таким именем уже существует",
        },
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=MAX_NAME_LENGTH,
        validators=(first_name_validator,),
    )

    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=MAX_NAME_LENGTH,
        validators=(last_name_validator,),
    )

    avatar = models.ImageField(
        verbose_name="Аватар", upload_to="users/", blank=True, null=True
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("username",)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Подписчик",
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Автор",
        on_delete=models.CASCADE,
        related_name="subscribers",
    )

    class Meta:
        ordering = ("id",)
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = (
            models.UniqueConstraint(
                fields=("user", "author"),
                name="Такая подписка уже есть",
            ),
            models.CheckConstraint(
                check=~models.Q(author=models.F("user")),
                name="Нет смысла в подписке на себя",
            ),
        )

    def __str__(self) -> str:
        return f"{self.user.username} -> {self.author.username}"
