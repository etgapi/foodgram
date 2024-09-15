from django.core.validators import RegexValidator

from users.constants import (FIRST_NAME_PATTERN, LAST_NAME_PATTERN,
                             USERNAME_PATTERN)

username_validator = RegexValidator(
    regex=USERNAME_PATTERN,
    message="Недопустимые символы в логине",
    code="invalid_username",
)

first_name_validator = RegexValidator(
    regex=FIRST_NAME_PATTERN,
    message="Имя состоит не только из букв",
)

last_name_validator = RegexValidator(
    regex=LAST_NAME_PATTERN,
    message="В фамилии встречаются не только буквы пробелы и тире",
)
