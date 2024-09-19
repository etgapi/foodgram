# users/models.py
# Максимальная длина электронной почты
MAX_EMAIL_LENGTH = 254
# Максимальная длина имени
MAX_NAME_LENGTH = 150

# users/validators.py
# Имя должно состоять только из букв
FIRST_NAME_PATTERN = r"^[a-zA-Zа-яА-Я\s]*$"
# В фамилии могут быть только буквы пробелы и тире
LAST_NAME_PATTERN = r"^[a-zA-Zа-яА-Я\s\-]*$"
# Допустимые символы в имени логина
USERNAME_PATTERN = r"^(?!.*\bme\b)[\w.@+-]+\Z"

# api/serializers.py
# Минимальная длина имени при создании в API
MIN_USERNAME_LENGTH_API = 5
