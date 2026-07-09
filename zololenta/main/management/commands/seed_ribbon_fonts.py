from __future__ import annotations

from dataclasses import dataclass

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from main.models import RibbonOption


@dataclass(frozen=True)
class FontSpec:
    title: str
    family: str
    fallback: str = "cursive"

    @property
    def css_value(self) -> str:
        return f"'{self.family}', {self.fallback}"


FONT_SPECS = (
    FontSpec("Romantique Script", "Romantique Script"),
    FontSpec("Good Vibes Pro", "Good Vibes Pro"),
    FontSpec("Zither Script", "Zither Script"),
    FontSpec("Grosvenor Script", "Grosvenor Script"),
    FontSpec("Esenin Script", "Esenin Script"),
    FontSpec("Mon Amour One", "Mon Amour One"),
    FontSpec("Magnolia Script", "Magnolia Script"),
    FontSpec("Belissimo Script", "Belissimo Script"),
    FontSpec("Mazurka Script", "Mazurka Script"),
    FontSpec("Ceremonious One", "Ceremonious One"),
    FontSpec("Astoria Script One", "Astoria Script One"),
)


class Command(BaseCommand):
    help = "Заменяет каталог шрифтов конструктора на локальные шрифты из static."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать изменения без сохранения.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        font_options = list(
            RibbonOption.objects
            .filter(opt_type=RibbonOption.TYPE_FONT)
            .select_related("news")
            .order_by("id")
        )

        if len(font_options) < len(FONT_SPECS):
            raise CommandError(
                f"Недостаточно существующих font-опций: "
                f"{len(font_options)} вместо {len(FONT_SPECS)}."
            )

        self.stdout.write(
            f"Найдено font-опций: {len(font_options)}. "
            f"Активными будут первые {len(FONT_SPECS)}."
        )

        if dry_run:
            for option, spec in zip(font_options, FONT_SPECS):
                self.stdout.write(
                    f"WOULD UPDATE #{option.pk}: "
                    f"{option.news.title!r} -> {spec.title!r}, "
                    f"{option.css_value!r} -> {spec.css_value!r}"
                )

            for option in font_options[len(FONT_SPECS):]:
                self.stdout.write(
                    f"WOULD DEACTIVATE #{option.pk}: {option.news.title!r}"
                )

            self.stdout.write(self.style.WARNING("DRY RUN: изменений нет."))
            return

        updated = 0
        deactivated = 0

        with transaction.atomic():
            for option, spec in zip(font_options, FONT_SPECS):
                option.css_value = spec.css_value
                option.font_url = ""
                option.is_active = True
                option.save(update_fields=["css_value", "font_url", "is_active"])

                news = option.news
                news.title = spec.title

                if news.photo:
                    news.photo = ""

                news.save(update_fields=["title", "photo"])

                updated += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"UPDATE #{option.pk}: {spec.title} — {spec.css_value}"
                    )
                )

            for option in font_options[len(FONT_SPECS):]:
                changed = []

                if option.is_active:
                    option.is_active = False
                    changed.append("is_active")

                if option.font_url:
                    option.font_url = ""
                    changed.append("font_url")

                if changed:
                    option.save(update_fields=changed)
                    deactivated += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"DEACTIVATE #{option.pk}: {option.news.title}"
                        )
                    )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Каталог локальных шрифтов обновлён."))
        self.stdout.write(f"Обновлено активных: {updated}")
        self.stdout.write(f"Отключено старых: {deactivated}")
