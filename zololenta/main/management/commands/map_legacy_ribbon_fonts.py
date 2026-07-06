from __future__ import annotations

from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from main.models import News, RibbonOption


FONT_MAP = {
    110: ("Marck Script", "cursive"),
    111: ("Lobster", "cursive"),
    112: ("Cormorant Garamond", "serif"),
    113: ("Bad Script", "cursive"),
    114: ("Yeseva One", "serif"),
    115: ("Pacifico", "cursive"),
    116: ("Forum", "serif"),
    117: ("Neucha", "cursive"),
    119: ("Alice", "serif"),
    120: ("Philosopher", "serif"),
    121: ("Poiret One", "sans-serif"),
    122: ("Playfair Display", "serif"),
    123: ("Cormorant Infant", "serif"),
    124: ("Kurale", "serif"),
    125: ("Oranienbaum", "serif"),
    126: ("PT Serif", "serif"),
    127: ("Pangolin", "cursive"),
    128: ("Caveat", "cursive"),
    129: ("Tenor Sans", "sans-serif"),
    130: ("Alegreya", "serif"),
    131: ("Old Standard TT", "serif"),
    132: ("Cormorant Unicase", "serif"),
    133: ("Comfortaa", "sans-serif"),
    134: ("Kelly Slab", "serif"),
}


SEED_SLUGS = {
    "font-marck-script",
    "font-bad-script",
    "font-caveat",
    "font-neucha",
    "font-pacifico",
    "font-lobster",
    "font-cormorant-garamond",
    "font-yeseva-one",
    "font-forum",
    "font-alice",
    "font-philosopher",
    "font-poiret-one",
    "font-russo-one",
    "font-comfortaa",
}


class Command(BaseCommand):
    help = (
        "Переименовывает News 110–134 и назначает им "
        "кириллические Google Fonts."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Применить изменения. Без параметра работает dry-run.",
        )
        parser.add_argument(
            "--skip-remote-check",
            action="store_true",
            help="Пропустить проверку Google Fonts.",
        )

    def handle(self, *args, **options):
        apply_changes = options["apply"]
        skip_remote_check = options["skip_remote_check"]

        target_ids = set(FONT_MAP)

        news_items = {
            news.pk: news
            for news in News.objects
            .filter(pk__in=target_ids)
            .order_by("pk")
        }

        missing_news = sorted(target_ids - set(news_items))

        if missing_news:
            raise CommandError(
                f"Не найдены News: {missing_news}"
            )

        font_options = {
            option.news_id: option
            for option in RibbonOption.objects
            .filter(
                news__id__in=target_ids,
                opt_type=RibbonOption.TYPE_FONT,
            )
            .select_related("news")
        }

        missing_options = sorted(
            target_ids - set(font_options)
        )

        if missing_options:
            raise CommandError(
                f"Не найдены RibbonOption для News: "
                f"{missing_options}"
            )

        self.stdout.write("=== PHOTO CHECK ===")

        for news_id in sorted(target_ids):
            news = news_items[news_id]

            if not news.photo:
                raise CommandError(
                    f"У News #{news_id} отсутствует photo."
                )

            try:
                exists = news.photo.storage.exists(
                    news.photo.name
                )
            except Exception as exc:
                raise CommandError(
                    f"Ошибка проверки фото News #{news_id}: "
                    f"{exc}"
                ) from exc

            if not exists:
                raise CommandError(
                    f"Файл фото News #{news_id} не найден: "
                    f"{news.photo.name}"
                )

            self.stdout.write(
                f"OK: News #{news_id} — {news.photo.name}"
            )

        self.stdout.write("")
        self.stdout.write("=== GOOGLE FONT CHECK ===")

        mapping = {}

        for news_id, (family, fallback) in FONT_MAP.items():
            css_value = f"'{family}', {fallback}"

            font_url = (
                "https://fonts.googleapis.com/css2?"
                f"family={quote_plus(family)}"
                "&display=swap"
            )

            mapping[news_id] = {
                "family": family,
                "fallback": fallback,
                "css_value": css_value,
                "font_url": font_url,
            }

            if skip_remote_check:
                self.stdout.write(
                    f"SKIP REMOTE CHECK: {family}"
                )
                continue

            self._check_google_font(
                family=family,
                font_url=font_url,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"OK: {family} — Cyrillic найден"
                )
            )

        self.stdout.write("")
        self.stdout.write("=== PROPOSED MAPPING ===")

        for news_id in sorted(target_ids):
            news = news_items[news_id]
            option = font_options[news_id]
            target = mapping[news_id]

            self.stdout.write(
                f"News #{news_id}: "
                f"{news.title!r} -> "
                f"{target['family']!r}"
            )

            self.stdout.write(
                f"    css: "
                f"{option.css_value!r} -> "
                f"{target['css_value']!r}"
            )

            self.stdout.write(
                f"    url: "
                f"{option.font_url!r} -> "
                f"{target['font_url']!r}"
            )

            self.stdout.write(
                f"    photo: {news.photo.name}"
            )

        if not apply_changes:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(
                    "DRY RUN: база не изменена. "
                    "Для применения добавьте --apply."
                )
            )
            return

        self.stdout.write("")
        self.stdout.write("=== APPLY ===")

        with transaction.atomic():
            locked_news = {
                news.pk: news
                for news in News.objects
                .select_for_update()
                .filter(pk__in=target_ids)
            }

            locked_options = {
                option.news_id: option
                for option in RibbonOption.objects
                .select_for_update()
                .filter(
                    news__id__in=target_ids,
                    opt_type=RibbonOption.TYPE_FONT,
                )
            }

            for news_id in sorted(target_ids):
                news = locked_news[news_id]
                option = locked_options[news_id]
                target = mapping[news_id]

                changed_news_fields = []

                if news.title != target["family"]:
                    news.title = target["family"]
                    changed_news_fields.append("title")

                if changed_news_fields:
                    news.save(
                        update_fields=changed_news_fields
                    )

                changed_option_fields = []

                if option.css_value != target["css_value"]:
                    option.css_value = target["css_value"]
                    changed_option_fields.append("css_value")

                if option.font_url != target["font_url"]:
                    option.font_url = target["font_url"]
                    changed_option_fields.append("font_url")

                if not option.is_active:
                    option.is_active = True
                    changed_option_fields.append("is_active")

                if changed_option_fields:
                    option.save(
                        update_fields=changed_option_fields
                    )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"UPDATED: News #{news_id} — "
                        f"{target['family']}"
                    )
                )

            target_css_values = {
                item["css_value"]
                for item in mapping.values()
            }

            duplicate_seed_options = list(
                RibbonOption.objects
                .select_for_update()
                .filter(
                    opt_type=RibbonOption.TYPE_FONT,
                    is_active=True,
                    news__slug__in=SEED_SLUGS,
                    css_value__in=target_css_values,
                )
                .exclude(news__id__in=target_ids)
                .select_related("news")
            )

            for duplicate in duplicate_seed_options:
                duplicate.is_active = False
                duplicate.save(
                    update_fields=["is_active"]
                )

                self.stdout.write(
                    self.style.WARNING(
                        f"DEACTIVATED DUPLICATE: "
                        f"Option #{duplicate.pk} — "
                        f"{duplicate.news.title}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Карта шрифтов успешно применена."
            )
        )

    @staticmethod
    def _check_google_font(
        *,
        family: str,
        font_url: str,
    ) -> None:
        request = Request(
            font_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 "
                    "Chrome/126 Safari/537.36"
                ),
                "Accept": "text/css,*/*;q=0.1",
            },
        )

        try:
            with urlopen(
                request,
                timeout=25,
            ) as response:
                css = response.read().decode(
                    "utf-8",
                    errors="replace",
                )

        except (
            HTTPError,
            URLError,
            TimeoutError,
        ) as exc:
            raise CommandError(
                f"Не удалось проверить {family}: {exc}"
            ) from exc

        lowered = css.lower()

        if "font-family" not in lowered:
            raise CommandError(
                f"Google Fonts не вернул CSS для {family}."
            )

        if "cyrillic" not in lowered:
            raise CommandError(
                f"У {family} не найден Cyrillic subset."
            )
