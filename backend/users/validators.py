from django.core.validators import RegexValidator

USERNAME_PATTERN = r'^(?!.*\bme\b)[\w.@+-]+\Z'  # r'^[\w.@+-]+\z'
FIRST_NAME_PATTERN = r'^[a-zA-Zа-яА-Я\s]*$'
LAST_NAME_PATTERN = r'^[a-zA-Zа-яА-Я\s\-]*$'


username_validator = RegexValidator(
    regex=USERNAME_PATTERN,
    message='Недопустимые символы в логине',
    code='invalid_username'
)

first_name_validator = RegexValidator(
    regex=FIRST_NAME_PATTERN,
    message='Имя состоит не только из букв.',
)

last_name_validator = RegexValidator(
    regex=LAST_NAME_PATTERN,
    message='В фамилии встречаются не только буквы пробелы и тире.',
)
