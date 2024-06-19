import json
import random

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from recipes.models import Recipe, IngredientsAmount
from recipes.models import Tag
from recipes.models import Ingredient


User = get_user_model()


class Command(BaseCommand):
    fake_image = ''
    author = None
    users = User.objects.all()
    tags = Tag.objects.all()
    ingredients = Ingredient.objects.all()

    def get_random_author(self):
        return random.choice(self.users)

    def get_random_ingredient(self):
        return random.choice(self.ingredients)

    def get_random_tag(self):
        return random.choice(self.tags)

    def handle(self, *args, **options):
        # file_path = settings.BASE_DIR / 'data/recipes.json'
        file_path = settings.BASE_DIR / 'data/recipes_ar.json'
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not self.get_random_author():
            self.stdout.write(self.style.ERROR('Нет пользователей.'))
            return
        try:
            for recipe_data in data:
                self._create_recipe(recipe_data)

        except Exception as e:
            self.stdout.write(self.style.ERROR(str(e)))

    def _create_recipe(self, recipe_data):
        tags = [self.get_random_tag().slug for x in range(2)]
        ingredients = [
            {'name': self.get_random_ingredient().name,
             'amount': random.randrange(1, 100) / 2}
            for x in range(len(recipe_data['ingredients']))
        ]  # recipe_data.pop('ingredients')
        recipe_name = recipe_data['title']
        if Recipe.objects.filter(name=recipe_name).exists():
            self.stdout.write(
                self.style.ERROR(f'Рецепт {recipe_name!r} уже существует!')
            )
            return

        with transaction.atomic():
            recipe = Recipe.objects.create(
                author=self.get_random_author(),
                image=self.fake_image,
                name=recipe_data['title'],
                text=recipe_data['instructions'],
                image='http://127.0.0.1:8000/media/recipes/images/logo.png',
                cooking_time=random.randrange(1, 200) / 10
            )

            recipe.tags.set(
                Tag.objects.filter(slug__in=tags).values_list('id', flat=True)
            )
            for ingredient in ingredients:
                if not Ingredient.objects.filter(
                    name=ingredient['name']
                ).exists():
                    raise ValueError(
                        f'Ингредиент {ingredient["name"]!r} не существует!'
                    )

                current_ingredient = Ingredient.objects.get(
                    name=ingredient['name']
                )
                IngredientsAmount.objects.create(
                    recipe=recipe,
                    ingredient=current_ingredient,
                    amount=ingredient['amount'],
                )

            self.stdout.write(
                self.style.SUCCESS(f'Успешно добавлен {recipe_name!r}!')
            )
