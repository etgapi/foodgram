from django.core.validators import RegexValidator

from users.constants import (FIRST_NAME_PATTERN, LAST_NAME_PATTERN,
                             USERNAME_PATTERN)

username_validator = RegexValidator(
    regex=USERNAME_PATTERN,
    message="Недопустимые символы в имени логина",
    code="invalid_username",
)

first_name_validator = RegexValidator(
    regex=FIRST_NAME_PATTERN,
    message="Имя должно состоять только из букв",
)

last_name_validator = RegexValidator(
    regex=LAST_NAME_PATTERN,
    message="В фамилии могут быть только буквы пробелы и тире",
)
