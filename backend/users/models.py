from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    """Модель для пользователей"""

    username = models.CharField(
        "Логин",
        max_length=150,
        unique=True
    )
    password = models.CharField(
        "Пароль",
        max_length=150,
    )
    email = models.EmailField(
        "Адрес электронной почты",
        max_length=254,
        unique=True,
    )
    first_name = models.CharField(
        "Имя",
        max_length=150,
    )
    last_name = models.CharField(
        "Фамилия",
        max_length=150,
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
        return f"{self.username} {self.first_name}"


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
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"],
                name="Вы уже подписаны на этого автора"
            ),
        ]
        ordering = ["author_id"]
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def clean(self):
        if self.user == self.author:
            raise ValidationError('Невозможно подписаться на себя')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def str(self):
        return f"{self.user} подписался на {self.author}"
