import re

from django.core.management.base import BaseCommand
from django.db import transaction

from main.models import (
    RibbonOption,
    RibbonColor,
    RibbonTextColor,
    RibbonFont,
    RibbonTemplate,
)


HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


TEXT_COLORS = [
    {
        "title": "Белый",
        "slug": "text-white",
        "hex_value": "#FFFFFF",
        "sort_order": 10,
    },
    {
        "title": "Золото",
        "slug": "text-gold",
        "hex_value": "#D4AF37",
        "sort_order": 20,
    },
    {
        "title": "Серебро",
        "slug": "text-silver",
        "hex_value": "#C0C0C0",
        "sort_order": 30,
    },
    {
        "title": "Чёрный",
        "slug": "text-black",
        "hex_value": "#000000",
        "sort_order": 40,
    },
    {
        "title": "Бордовый",
        "slug": "text-burgundy",
        "hex_value": "#7A1430",
        "sort_order": 50,
    },
]


TEMPLATES = [
    {
        "title": "Классическая траурная лента",
        "slug": "classic-memorial-ribbon",
        "description": "Базовый шаблон с двумя строками текста на ленте.",
        "layout_config": {
            "type": "classic",
            "text_lines": 2,
            "text_align": "center",
        },
        "sort_order": 10,
    },
]


class Command(BaseCommand):
    help = "Наполняет новые чистые сущности каталога лент из legacy RibbonOption."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать изменения без записи в БД.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        self.stdout.write("=== CLEAN RIBBON CATALOG SEED ===")
        self.stdout.write(f"dry_run: {dry_run}")

        with transaction.atomic():
            color_count = self.seed_ribbon_colors(dry_run=dry_run)
            text_color_count = self.seed_text_colors(dry_run=dry_run)
            font_count = self.seed_fonts(dry_run=dry_run)
            template_count = self.seed_templates(dry_run=dry_run)

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write("")
        self.stdout.write("=== SUMMARY ===")
        self.stdout.write(f"RibbonColor planned/changed: {color_count}")
        self.stdout.write(f"RibbonTextColor planned/changed: {text_color_count}")
        self.stdout.write(f"RibbonFont planned/changed: {font_count}")
        self.stdout.write(f"RibbonTemplate planned/changed: {template_count}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: изменения не сохранены."))
        else:
            self.stdout.write(self.style.SUCCESS("Новые сущности каталога обновлены."))

    def seed_ribbon_colors(self, dry_run):
        self.stdout.write("")
        self.stdout.write("=== RIBBON COLORS FROM LEGACY OPTIONS ===")

        changed = 0
        options = (
            RibbonOption.objects
            .select_related("news")
            .filter(opt_type=RibbonOption.TYPE_COLOR, is_active=True)
            .order_by("id")
        )

        for index, option in enumerate(options, start=1):
            css_value = (option.css_value or "").strip().upper()

            if not HEX_RE.match(css_value):
                self.stdout.write(
                    self.style.WARNING(
                        f"SKIP color option #{option.id}: invalid hex '{option.css_value}'"
                    )
                )
                continue

            news = option.news
            title = (getattr(news, "title", "") or f"Цвет ленты {index}").strip()
            slug = f"legacy-ribbon-color-{option.id}"

            defaults = {
                "title": title,
                "hex_value": css_value,
                "sort_order": index * 10,
                "is_active": True,
            }

            image_name = ""
            if news and getattr(news, "photo", None):
                image_name = news.photo.name or ""

            obj, created = RibbonColor.objects.get_or_create(
                slug=slug,
                defaults={
                    **defaults,
                    "image": image_name,
                },
            )

            needs_update = created
            if not created:
                for key, value in defaults.items():
                    if getattr(obj, key) != value:
                        setattr(obj, key, value)
                        needs_update = True

                if image_name and getattr(obj.image, "name", "") != image_name:
                    obj.image = image_name
                    needs_update = True

            if needs_update:
                changed += 1
                self.stdout.write(
                    f"{'CREATE' if created else 'UPDATE'} RibbonColor: "
                    f"{title} | {css_value} | image={image_name or '-'}"
                )
                if not dry_run:
                    obj.save()
            else:
                self.stdout.write(f"OK RibbonColor: {title} | {css_value}")

        return changed

    def seed_text_colors(self, dry_run):
        self.stdout.write("")
        self.stdout.write("=== TEXT COLORS ===")

        changed = 0

        for item in TEXT_COLORS:
            obj, created = RibbonTextColor.objects.get_or_create(
                slug=item["slug"],
                defaults={
                    "title": item["title"],
                    "hex_value": item["hex_value"],
                    "sort_order": item["sort_order"],
                    "is_active": True,
                },
            )

            needs_update = created
            if not created:
                for key in ["title", "hex_value", "sort_order"]:
                    if getattr(obj, key) != item[key]:
                        setattr(obj, key, item[key])
                        needs_update = True

                if not obj.is_active:
                    obj.is_active = True
                    needs_update = True

            if needs_update:
                changed += 1
                self.stdout.write(
                    f"{'CREATE' if created else 'UPDATE'} RibbonTextColor: "
                    f"{item['title']} | {item['hex_value']}"
                )
                if not dry_run:
                    obj.save()
            else:
                self.stdout.write(
                    f"OK RibbonTextColor: {item['title']} | {item['hex_value']}"
                )

        return changed

    def seed_fonts(self, dry_run):
        self.stdout.write("")
        self.stdout.write("=== RIBBON FONTS FROM LEGACY OPTIONS ===")

        changed = 0
        options = (
            RibbonOption.objects
            .select_related("news")
            .filter(opt_type=RibbonOption.TYPE_FONT, is_active=True)
            .order_by("id")
        )

        for index, option in enumerate(options, start=1):
            font_family = (option.css_value or "").strip()
            if not font_family:
                self.stdout.write(
                    self.style.WARNING(f"SKIP font option #{option.id}: empty css_value")
                )
                continue

            news = option.news
            title = (getattr(news, "title", "") or f"Шрифт ленты {index}").strip()
            slug = f"legacy-ribbon-font-{option.id}"

            defaults = {
                "title": title,
                "font_family": font_family,
                "sort_order": index * 10,
                "is_active": True,
            }

            preview_name = ""
            if news and getattr(news, "photo", None):
                preview_name = news.photo.name or ""

            obj, created = RibbonFont.objects.get_or_create(
                slug=slug,
                defaults={
                    **defaults,
                    "preview_image": preview_name,
                },
            )

            needs_update = created
            if not created:
                for key, value in defaults.items():
                    if getattr(obj, key) != value:
                        setattr(obj, key, value)
                        needs_update = True

                if preview_name and getattr(obj.preview_image, "name", "") != preview_name:
                    obj.preview_image = preview_name
                    needs_update = True

            if needs_update:
                changed += 1
                self.stdout.write(
                    f"{'CREATE' if created else 'UPDATE'} RibbonFont: "
                    f"{title} | {font_family} | preview={preview_name or '-'}"
                )
                if not dry_run:
                    obj.save()
            else:
                self.stdout.write(f"OK RibbonFont: {title} | {font_family}")

        return changed

    def seed_templates(self, dry_run):
        self.stdout.write("")
        self.stdout.write("=== RIBBON TEMPLATES ===")

        changed = 0

        for item in TEMPLATES:
            obj, created = RibbonTemplate.objects.get_or_create(
                slug=item["slug"],
                defaults={
                    "title": item["title"],
                    "description": item["description"],
                    "layout_config": item["layout_config"],
                    "sort_order": item["sort_order"],
                    "is_active": True,
                },
            )

            needs_update = created
            if not created:
                for key in ["title", "description", "layout_config", "sort_order"]:
                    if getattr(obj, key) != item[key]:
                        setattr(obj, key, item[key])
                        needs_update = True

                if not obj.is_active:
                    obj.is_active = True
                    needs_update = True

            if needs_update:
                changed += 1
                self.stdout.write(
                    f"{'CREATE' if created else 'UPDATE'} RibbonTemplate: {item['title']}"
                )
                if not dry_run:
                    obj.save()
            else:
                self.stdout.write(f"OK RibbonTemplate: {item['title']}")

        return changed
