# users/models.py
MAX_NAME_LENGTH = 150  # Максимальная длина имени
MAX_EMAIL_LENGTH = 254  # Максимальная длина электронной почты

# users/validators.py
USERNAME_PATTERN = r'^(?!.*\bme\b)[\w.@+-]+\Z'  # r'^[\w.@+-]+\z'
FIRST_NAME_PATTERN = r'^[a-zA-Zа-яА-Я\s]*$'
LAST_NAME_PATTERN = r'^[a-zA-Zа-яА-Я\s\-]*$'

# api/serializers.py
MIN_API_USERNAME_LENGTH = 5  # Минимальная длина имени создаваемого через API