from django.http import HttpResponse
from recipes.models import RecipeIngredient


def shopping_list_txt(user):
    """Функция скачивания текстового файла списка ингредиентов."""
    text_shop_list = 'Список покупок \n\n'
    measurement_unit = {}
    ingredient_amount = {}
    ingredients = RecipeIngredient.objects.filter(
        recipe__shopping_cart__user=user
    ).values(
        'ingredient__name', 'ingredient__measurement_unit', 'amount')
    for ingredient in ingredients:
        if ingredient['ingredient__name'] in ingredient_amount:
            ingredient_amount[
                ingredient['ingredient__name']
            ] += ingredient['amount']
        else:
            measurement_unit[
                ingredient['ingredient__name']
            ] = ingredient['ingredient__measurement_unit']
            ingredient_amount[
                ingredient['ingredient__name']
            ] = ingredient['amount']
    for ingredient, amount in ingredient_amount .items():
        text_shop_list += (
            f'{ingredient} - {amount}'
            f'{measurement_unit[ingredient]}\n'
        )
    response = HttpResponse(text_shop_list, content_type='text/plain')
    response[
        'Content-Disposition'
    ] = 'attachment; filename="shopping_list.txt"'
    return response
