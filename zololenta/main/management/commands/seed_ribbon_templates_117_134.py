from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from main.models import News, RibbonTemplate


class Command(BaseCommand):
    help = "Наполняет RibbonTemplate из News с id 117..134."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать изменения без записи в БД.",
        )
        parser.add_argument(
            "--deactivate-empty",
            action="store_true",
            help="Отключить активные шаблоны без фото после успешного импорта.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        deactivate_empty = options["deactivate_empty"]

        news_ids = list(range(117, 135))

        self.stdout.write("=== SEED RIBBON TEMPLATES FROM NEWS 117..134 ===")
        self.stdout.write(f"dry_run: {dry_run}")
        self.stdout.write(f"deactivate_empty: {deactivate_empty}")
        self.stdout.write(f"news ids: {news_ids[0]}..{news_ids[-1]}")

        qs = (
            News.objects
            .filter(id__in=news_ids)
            .order_by("id")
        )

        found_ids = set(qs.values_list("id", flat=True))
        missing_ids = [pk for pk in news_ids if pk not in found_ids]

        if missing_ids:
            self.stdout.write(
                self.style.WARNING(
                    "Missing News ids: " + ", ".join(map(str, missing_ids))
                )
            )

        changed = 0
        imported = 0
        skipped_no_photo = 0

        with transaction.atomic():
            for index, news in enumerate(qs, start=1):
                photo_name = news.photo.name if getattr(news, "photo", None) else ""

                if not photo_name:
                    skipped_no_photo += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"SKIP News #{news.id}: no photo | {news.title}"
                        )
                    )
                    continue

                title = (news.title or f"Шаблон ленты {news.id}").strip()
                slug = f"ribbon-template-news-{news.id}"

                defaults = {
                    "title": title,
                    "description": (
                        "Фото-пример оформления ленты. "
                        "Используется как визуальный ориентир и не меняет превью справа."
                    ),
                    "preview_image": photo_name,
                    "layout_config": {
                        "type": "photo_example",
                        "source": "news",
                        "news_id": news.id,
                        "affects_preview": False,
                    },
                    "sort_order": index * 10,
                    "is_active": True,
                }

                obj, created = RibbonTemplate.objects.get_or_create(
                    slug=slug,
                    defaults=defaults,
                )

                needs_update = created

                if not created:
                    for field, value in defaults.items():
                        current = getattr(obj, field)

                        if field == "preview_image":
                            current = obj.preview_image.name if obj.preview_image else ""

                        if current != value:
                            setattr(obj, field, value)
                            needs_update = True

                if needs_update:
                    action = "CREATE" if created else "UPDATE"
                    changed += 1
                    self.stdout.write(
                        f"{action}: News #{news.id} -> Template "
                        f"'{title}' | image={photo_name}"
                    )
                    if not dry_run:
                        obj.save()
                else:
                    self.stdout.write(
                        f"OK: News #{news.id} -> Template "
                        f"'{title}' | image={photo_name}"
                    )

                imported += 1

            deactivated = 0
            if deactivate_empty and imported:
                empty_templates = RibbonTemplate.objects.filter(is_active=True).filter(
                    Q(preview_image="") | Q(preview_image__isnull=True)
                )

                deactivated = empty_templates.count()

                if deactivated:
                    self.stdout.write(
                        f"DEACTIVATE active templates without photo: {deactivated}"
                    )
                    if not dry_run:
                        empty_templates.update(is_active=False)

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write("")
        self.stdout.write("=== SUMMARY ===")
        self.stdout.write(f"found news: {qs.count()}")
        self.stdout.write(f"missing news ids: {len(missing_ids)}")
        self.stdout.write(f"imported templates with photo: {imported}")
        self.stdout.write(f"skipped without photo: {skipped_no_photo}")
        self.stdout.write(f"changed: {changed}")
        self.stdout.write(f"deactivated empty templates: {deactivated}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: изменения не сохранены."))
        else:
            self.stdout.write(self.style.SUCCESS("RibbonTemplate обновлены из News 117..134."))
