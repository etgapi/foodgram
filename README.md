# Проект Foodgram

Дипломный проект "Яндекс Практикум".

Программа дополнительного профессионального образования «Python-разработчик»
 
## Описание
 
«Фудграм» — это сайт, на котором пользователи могут публиковать свои рецепты,
добавлять чужие рецепты в избранное и подписываться на публикации других авторов. 
Зарегистрированным пользователям доступен сервис «Список покупок».
Он позволяет добавлять в корзину список продуктов, которые нужно купить для блюд.
Такой список продуктов (с общим количеством ингредиентов) можно скачать в формате txt.
Страницу любого рецепта можно скопировать при помощи короткой ссылки.

Сайт доступен по адресу: welcome.onthewifi.com

## Стэк используемых технологий
- Python
- Django
- Django Rest Framework
- Docker
- Gunicorn
- Nginx
- PostgreSQL

## Запуск проекта локально
### 1. Клонируем репозиторий на свой компьютер
```
git clone https://github.com/etgapi/foodgram.git
```
В корне проекта необходимо создать файл .env со своими данными
```
POSTGRES_USER      #имя юзера в БД PostgreSQL
POSTGRES_PASSWORD  #пароль юзера в БД PostgreSQL
POSTGRES_DB        #имя БД
DB_HOST            #имя контейнера, где запущен сервер БД
DB_PORT            #порт, по которому Django будет обращаться к серверу с БД 

SECRET_KEY         #ваш секретный код из settings.py для Django проекта
DEBUG              #статус режима отладки (default=False)
ALLOWED_HOSTS      #список доступных хостов
```

### 2. Запуск Docker engine
### В корне проекта, где лежит файл docker-compose.yml, выполнить команду:
```
docker compose -f docker-compose.yml up -d

docker compose -f docker-compose.yml exec backend python manage.py makemigrations

docker compose -f docker-compose.yml exec backend python manage.py migrate

docker compose -f docker-compose.yml exec backend python manage.py add_ingredients

docker compose -f docker-compose.yml exec backend python manage.py add_tags
```
Последние команды загружают в БД подготовленный набор необходимых данных (ингредиенты и тэги)
Дополнительно можно создать суперпользователя, для доступа к админ-панели сайта, командой:
```
docker compose exec backend python manage.py createsuperuser
```
Также необходимо скопировать статику для админки Django
```
docker compose -f docker-compose.yml exec backend python manage.py collectstatic --no-input
```
И скопировать статику в volume static для бэкенда
```
docker compose -f docker-compose.yml exec backend cp -r /app/collected_static/. /static/
```

Проект Foodgram доступен по адресу http://localhost

Спецификация API доступна по адресу http://localhost/api/docs/

## Автор: 
Цой Анна 
https://github.com/etgapi

