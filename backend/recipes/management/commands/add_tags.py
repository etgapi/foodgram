import csv

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q

from recipes.models import Tag


class Command(BaseCommand):
    help = 'Добавляет теги в базу.'

    def handle(self, *args, **options):
        file_path = settings.BASE_DIR / 'data/tags.csv'
        with open(file_path, 'r', encoding='utf-8') as f:
            for row in csv.reader(f):
                if Tag.objects.filter(
                    Q(name=row[0]) | Q(slug=row[1])
                ).exists():
                    self.stdout.write(
                        self.style.ERROR(f'{row[0]!r} уже есть!')
                    )
                    continue
                Tag.objects.create(name=row[0], slug=row[1])
                self.stdout.write(
                    self.style.SUCCESS(f'Добавлен тег {row[0]!r}')
                )