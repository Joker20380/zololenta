from __future__ import annotations

from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.db.models.fields.files import FileField

from main.models import News, RibbonOption


@dataclass(frozen=True)
class FontSpec:
    title: str
    slug: str
    family: str
    fallback: str
    url: str

    @property
    def css_value(self) -> str:
        return f"'{self.family}', {self.fallback}"


FONT_SPECS = (
    # Рукописные
    FontSpec(
        title="Marck Script",
        slug="font-marck-script",
        family="Marck Script",
        fallback="cursive",
        url="https://fonts.googleapis.com/css2?family=Marck+Script&display=swap",
    ),
    FontSpec(
        title="Bad Script",
        slug="font-bad-script",
        family="Bad Script",
        fallback="cursive",
        url="https://fonts.googleapis.com/css2?family=Bad+Script&display=swap",
    ),
    FontSpec(
        title="Caveat",
        slug="font-caveat",
        family="Caveat",
        fallback="cursive",
        url=(
            "https://fonts.googleapis.com/css2?"
            "family=Caveat:wght@400;500;600;700&display=swap"
        ),
    ),
    FontSpec(
        title="Neucha",
        slug="font-neucha",
        family="Neucha",
        fallback="cursive",
        url="https://fonts.googleapis.com/css2?family=Neucha&display=swap",
    ),
    FontSpec(
        title="Pacifico",
        slug="font-pacifico",
        family="Pacifico",
        fallback="cursive",
        url="https://fonts.googleapis.com/css2?family=Pacifico&display=swap",
    ),
    FontSpec(
        title="Lobster",
        slug="font-lobster",
        family="Lobster",
        fallback="cursive",
        url="https://fonts.googleapis.com/css2?family=Lobster&display=swap",
    ),

    # Элегантные и классические
    FontSpec(
        title="Cormorant Garamond",
        slug="font-cormorant-garamond",
        family="Cormorant Garamond",
        fallback="serif",
        url=(
            "https://fonts.googleapis.com/css2?"
            "family=Cormorant+Garamond:wght@500;600;700&display=swap"
        ),
    ),
    FontSpec(
        title="Yeseva One",
        slug="font-yeseva-one",
        family="Yeseva One",
        fallback="serif",
        url="https://fonts.googleapis.com/css2?family=Yeseva+One&display=swap",
    ),
    FontSpec(
        title="Forum",
        slug="font-forum",
        family="Forum",
        fallback="serif",
        url="https://fonts.googleapis.com/css2?family=Forum&display=swap",
    ),
    FontSpec(
        title="Alice",
        slug="font-alice",
        family="Alice",
        fallback="serif",
        url="https://fonts.googleapis.com/css2?family=Alice&display=swap",
    ),
    FontSpec(
        title="Philosopher",
        slug="font-philosopher",
        family="Philosopher",
        fallback="serif",
        url=(
            "https://fonts.googleapis.com/css2?"
            "family=Philosopher:wght@400;700&display=swap"
        ),
    ),

    # Современные и акцентные
    FontSpec(
        title="Poiret One",
        slug="font-poiret-one",
        family="Poiret One",
        fallback="sans-serif",
        url="https://fonts.googleapis.com/css2?family=Poiret+One&display=swap",
    ),
    FontSpec(
        title="Russo One",
        slug="font-russo-one",
        family="Russo One",
        fallback="sans-serif",
        url="https://fonts.googleapis.com/css2?family=Russo+One&display=swap",
    ),
    FontSpec(
        title="Comfortaa",
        slug="font-comfortaa",
        family="Comfortaa",
        fallback="sans-serif",
        url=(
            "https://fonts.googleapis.com/css2?"
            "family=Comfortaa:wght@400;500;600;700&display=swap"
        ),
    ),
)


class Command(BaseCommand):
    help = "Добавляет в конструктор проверенные Google Fonts с кириллицей."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Проверить и показать изменения без сохранения.",
        )
        parser.add_argument(
            "--skip-remote-check",
            action="store_true",
            help="Не проверять Google Fonts CSS. Использовать только при сетевых проблемах.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        skip_remote_check = options["skip_remote_check"]

        if not skip_remote_check:
            self.stdout.write("Проверяем Google Fonts CSS...")

            for spec in FONT_SPECS:
                self._verify_google_font(spec)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  OK: {spec.title} — кириллица найдена"
                    )
                )

        template_option = (
            RibbonOption.objects
            .filter(opt_type=RibbonOption.TYPE_FONT)
            .select_related("news")
            .order_by("id")
            .first()
        )

        if template_option is None:
            raise CommandError(
                "Нет существующего RibbonOption типа font, "
                "который можно использовать как шаблон."
            )

        template_news = template_option.news

        created_news = 0
        created_options = 0
        updated_options = 0
        existing_options = 0

        with transaction.atomic():
            for spec in FONT_SPECS:
                existing_by_css = (
                    RibbonOption.objects
                    .filter(
                        opt_type=RibbonOption.TYPE_FONT,
                        css_value=spec.css_value,
                    )
                    .select_related("news")
                    .first()
                )

                if existing_by_css is not None:
                    changed_fields = []

                    if existing_by_css.font_url != spec.url:
                        existing_by_css.font_url = spec.url
                        changed_fields.append("font_url")

                    if not existing_by_css.is_active:
                        existing_by_css.is_active = True
                        changed_fields.append("is_active")

                    if changed_fields:
                        existing_by_css.save(update_fields=changed_fields)
                        updated_options += 1

                        self.stdout.write(
                            f"UPDATE: {spec.title} "
                            f"(option #{existing_by_css.pk})"
                        )
                    else:
                        existing_options += 1
                        self.stdout.write(
                            f"EXISTS: {spec.title} "
                            f"(option #{existing_by_css.pk})"
                        )

                    continue

                matching_news = list(
                    News.objects
                    .filter(
                        Q(slug=spec.slug) |
                        Q(title=spec.title)
                    )
                    .order_by("pk")[:2]
                )

                if len(matching_news) > 1:
                    raise CommandError(
                        f"Для {spec.title} найдено несколько News. "
                        "Нужно устранить дубль вручную."
                    )

                news = matching_news[0] if matching_news else None

                if news is None:
                    news_values = self._clone_values(
                        template_news,
                        excluded={"title", "slug"},
                    )

                    news_values["title"] = spec.title
                    news_values["slug"] = spec.slug

                    if "content" in {
                        field.name
                        for field in News._meta.concrete_fields
                    }:
                        news_values["content"] = (
                            f"<p>Шрифт {spec.title} для оформления "
                            "именных и выпускных лент.</p>"
                        )

                    news = News.objects.create(**news_values)
                    self._copy_m2m(template_news, news)

                    created_news += 1
                    self.stdout.write(
                        f"CREATE NEWS: {spec.title} (news #{news.pk})"
                    )

                option = (
                    RibbonOption.objects
                    .filter(news=news)
                    .first()
                )

                if option is not None:
                    if option.opt_type != RibbonOption.TYPE_FONT:
                        raise CommandError(
                            f"News #{news.pk} уже связан с опцией "
                            f"типа {option.opt_type!r}, а не font."
                        )

                    option.css_value = spec.css_value
                    option.font_url = spec.url
                    option.is_active = True
                    option.save(
                        update_fields=[
                            "css_value",
                            "font_url",
                            "is_active",
                        ]
                    )

                    updated_options += 1
                    self.stdout.write(
                        f"UPDATE OPTION: {spec.title} "
                        f"(option #{option.pk})"
                    )
                else:
                    option_values = self._clone_values(
                        template_option,
                        excluded={
                            "news",
                            "opt_type",
                            "css_value",
                            "font_url",
                            "is_active",
                        },
                    )

                    option_values.update(
                        {
                            "news_id": news.pk,
                            "opt_type": RibbonOption.TYPE_FONT,
                            "css_value": spec.css_value,
                            "font_url": spec.url,
                            "is_active": True,
                        }
                    )

                    option = RibbonOption.objects.create(
                        **option_values
                    )

                    created_options += 1
                    self.stdout.write(
                        f"CREATE OPTION: {spec.title} "
                        f"(option #{option.pk})"
                    )

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "DRY RUN завершён — база не изменена."
                if dry_run
                else "Импорт шрифтов завершён."
            )
        )

        self.stdout.write(f"Новых News: {created_news}")
        self.stdout.write(f"Новых опций: {created_options}")
        self.stdout.write(f"Обновлено опций: {updated_options}")
        self.stdout.write(f"Уже существовало: {existing_options}")

    @staticmethod
    def _verify_google_font(spec: FontSpec) -> None:
        request = Request(
            spec.url,
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
            with urlopen(request, timeout=20) as response:
                css = response.read().decode(
                    "utf-8",
                    errors="replace",
                )
        except (HTTPError, URLError, TimeoutError) as exc:
            raise CommandError(
                f"Не удалось проверить {spec.title}: {exc}"
            ) from exc

        css_lower = css.lower()

        if "font-family" not in css_lower:
            raise CommandError(
                f"Google Fonts не вернул CSS для {spec.title}."
            )

        if "cyrillic" not in css_lower:
            raise CommandError(
                f"У {spec.title} в ответе Google Fonts "
                "не найден кириллический subset."
            )

    @staticmethod
    def _clone_values(instance, *, excluded: set[str]) -> dict:
        values = {}

        for field in instance._meta.concrete_fields:
            if field.primary_key:
                continue

            if field.name in excluded:
                continue

            if getattr(field, "auto_now", False):
                continue

            if getattr(field, "auto_now_add", False):
                continue

            if field.unique:
                if field.has_default():
                    continue

                raise CommandError(
                    f"Нельзя автоматически клонировать уникальное поле "
                    f"{instance._meta.label}.{field.name}."
                )

            if isinstance(field, FileField) and field.blank:
                values[field.name] = ""
                continue

            if field.is_relation:
                values[field.attname] = getattr(
                    instance,
                    field.attname,
                )
            else:
                values[field.name] = getattr(
                    instance,
                    field.name,
                )

        return values

    @staticmethod
    def _copy_m2m(source, target) -> None:
        for field in source._meta.many_to_many:
            through = field.remote_field.through

            if not through._meta.auto_created:
                continue

            getattr(target, field.name).set(
                getattr(source, field.name).all()
            )
