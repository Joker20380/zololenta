from __future__ import annotations

import io
import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from main.models import RibbonOption

try:
    from PIL import Image, ImageDraw, ImageFont, features
except ImportError as exc:
    raise CommandError(
        "Pillow не установлен в виртуальном окружении."
    ) from exc


@dataclass(frozen=True)
class FontSource:
    family: str
    repository_directory: str


FONT_SOURCES = {
    "Marck Script": FontSource(
        family="Marck Script",
        repository_directory="ofl/marckscript",
    ),
    "Bad Script": FontSource(
        family="Bad Script",
        repository_directory="ofl/badscript",
    ),
    "Caveat": FontSource(
        family="Caveat",
        repository_directory="ofl/caveat",
    ),
    "Neucha": FontSource(
        family="Neucha",
        repository_directory="ofl/neucha",
    ),
    "Pacifico": FontSource(
        family="Pacifico",
        repository_directory="ofl/pacifico",
    ),
    "Lobster": FontSource(
        family="Lobster",
        repository_directory="ofl/lobster",
    ),
    "Cormorant Garamond": FontSource(
        family="Cormorant Garamond",
        repository_directory="ofl/cormorantgaramond",
    ),
    "Yeseva One": FontSource(
        family="Yeseva One",
        repository_directory="ofl/yesevaone",
    ),
    "Forum": FontSource(
        family="Forum",
        repository_directory="ofl/forum",
    ),
    "Alice": FontSource(
        family="Alice",
        repository_directory="ofl/alice",
    ),
    "Philosopher": FontSource(
        family="Philosopher",
        repository_directory="ofl/philosopher",
    ),
    "Poiret One": FontSource(
        family="Poiret One",
        repository_directory="ofl/poiretone",
    ),
    "Russo One": FontSource(
        family="Russo One",
        repository_directory="ofl/russoone",
    ),
    "Comfortaa": FontSource(
        family="Comfortaa",
        repository_directory="ofl/comfortaa",
    ),
}


class Command(BaseCommand):
    help = (
        "Генерирует WebP-превью для шрифтов конструктора "
        "и сохраняет их в News.photo."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Скачать и проверить шрифты, но не сохранять фото.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Перезаписать уже существующие изображения.",
        )
        parser.add_argument(
            "--family",
            action="append",
            default=[],
            help=(
                "Обработать только указанное семейство. "
                "Параметр можно повторять."
            ),
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        force = options["force"]
        selected_families = set(options["family"])

        if not features.check("webp"):
            raise CommandError(
                "Текущая сборка Pillow не поддерживает WebP."
            )

        system_font = self._find_system_font()

        font_options = (
            RibbonOption.objects
            .filter(
                opt_type=RibbonOption.TYPE_FONT,
                is_active=True,
            )
            .select_related("news")
            .order_by("id")
        )

        created = 0
        skipped = 0
        unsupported = 0

        with tempfile.TemporaryDirectory(
            prefix="zololenta_font_previews_"
        ) as temp_dir:
            cache_dir = Path(temp_dir)

            for option in font_options:
                family = self._extract_family(option.css_value)

                if selected_families and family not in selected_families:
                    continue

                source = FONT_SOURCES.get(family)

                if source is None:
                    unsupported += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"SKIP: {option.news.title} — "
                            f"нет источника для {family!r}"
                        )
                    )
                    continue

                if option.news.photo and not force:
                    skipped += 1
                    self.stdout.write(
                        f"EXISTS: {option.news.title} — "
                        f"{option.news.photo.name}"
                    )
                    continue

                self.stdout.write(
                    f"DOWNLOAD: {family}"
                )

                font_path = self._download_font(
                    source=source,
                    cache_dir=cache_dir,
                )

                image_bytes = self._render_preview(
                    title=option.news.title,
                    family=family,
                    font_path=font_path,
                    system_font_path=system_font,
                )

                filename = (
                    f"ribbon-font-"
                    f"{slugify(family) or option.pk}.webp"
                )

                if dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"DRY RUN: {option.news.title} — "
                            f"{len(image_bytes)} bytes"
                        )
                    )
                    created += 1
                    continue

                option.news.photo.save(
                    filename,
                    ContentFile(image_bytes),
                    save=False,
                )

                option.news.save(
                    update_fields=["photo"]
                )

                created += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"SAVED: {option.news.title} — "
                        f"{option.news.photo.name}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Dry-run завершён."
                if dry_run
                else "Генерация превью завершена."
            )
        )
        self.stdout.write(f"Создано: {created}")
        self.stdout.write(f"Пропущено существующих: {skipped}")
        self.stdout.write(f"Без настроенного источника: {unsupported}")

    @staticmethod
    def _extract_family(css_value: str) -> str:
        value = (css_value or "").strip()

        if not value:
            return ""

        family = value.split(",", 1)[0].strip()
        return family.strip("'\"")

    @staticmethod
    def _github_api_request(url: str) -> bytes:
        request = Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "zololenta-font-preview-generator",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )

        try:
            with urlopen(request, timeout=30) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError) as exc:
            raise CommandError(
                f"Ошибка загрузки {url}: {exc}"
            ) from exc

    def _download_font(
        self,
        *,
        source: FontSource,
        cache_dir: Path,
    ) -> Path:
        filenames = {
            "Marck Script": "MarckScript-Regular.ttf",
            "Bad Script": "BadScript-Regular.ttf",
            "Caveat": "Caveat[wght].ttf",
            "Neucha": "Neucha-Regular.ttf",
            "Pacifico": "Pacifico-Regular.ttf",
            "Lobster": "Lobster-Regular.ttf",
            "Cormorant Garamond": "CormorantGaramond[wght].ttf",
            "Yeseva One": "YesevaOne-Regular.ttf",
            "Forum": "Forum-Regular.ttf",
            "Alice": "Alice-Regular.ttf",
            "Philosopher": "Philosopher-Regular.ttf",
            "Poiret One": "PoiretOne-Regular.ttf",
            "Russo One": "RussoOne-Regular.ttf",
            "Comfortaa": "Comfortaa[wght].ttf",
        }

        filename = filenames.get(source.family)

        if not filename:
            raise CommandError(
                f"Для {source.family} не задан прямой TTF-файл."
            )

        target = cache_dir / filename

        if target.exists() and target.stat().st_size >= 10_000:
            return target

        encoded_filename = quote(filename, safe="")

        url = (
            "https://raw.githubusercontent.com/"
            "google/fonts/main/"
            f"{source.repository_directory}/"
            f"{encoded_filename}"
        )

        request = Request(
            url,
            headers={
                "User-Agent": "zololenta-font-preview-generator",
                "Accept": "application/octet-stream",
            },
        )

        try:
            with urlopen(request, timeout=45) as response:
                data = response.read()
        except (HTTPError, URLError, TimeoutError) as exc:
            raise CommandError(
                f"Ошибка загрузки TTF для {source.family}: "
                f"{url}: {exc}"
            ) from exc

        if len(data) < 10_000:
            raise CommandError(
                f"Получен слишком маленький файл "
                f"для {source.family}: {len(data)} bytes"
            )

        target.write_bytes(data)

        return target

    @staticmethod
    def _font_file_priority(filename: str) -> int:
        name = filename.lower()

        if "italic" in name:
            return 50

        if "regular" in name:
            return 0

        if "[wght]" in name:
            return 5

        if "variable" in name:
            return 10

        return 20

    @staticmethod
    def _find_system_font() -> Path:
        candidates = (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
            Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
        )

        for candidate in candidates:
            if candidate.exists():
                return candidate

        raise CommandError(
            "Не найден системный шрифт для служебных подписей."
        )

    def _render_preview(
        self,
        *,
        title: str,
        family: str,
        font_path: Path,
        system_font_path: Path,
    ) -> bytes:
        width = 1200
        height = 675

        image = Image.new(
            "RGB",
            (width, height),
            "#f7f1e5",
        )
        draw = ImageDraw.Draw(image)

        self._draw_background(draw, width, height)

        label_font = ImageFont.truetype(
            str(system_font_path),
            27,
        )
        title_font = ImageFont.truetype(
            str(system_font_path),
            31,
        )

        draw.text(
            (80, 62),
            "ШРИФТ ДЛЯ ВЫПУСКНЫХ ЛЕНТ",
            font=label_font,
            fill="#9c792d",
        )

        draw.text(
            (80, 119),
            title,
            font=title_font,
            fill="#29241c",
        )

        main_text = "Выпускник 2026"
        main_font = self._fit_font(
            draw=draw,
            text=main_text,
            font_path=font_path,
            max_width=1020,
            start_size=118,
            minimum_size=48,
        )

        main_box = draw.textbbox(
            (0, 0),
            main_text,
            font=main_font,
        )

        main_width = main_box[2] - main_box[0]
        main_height = main_box[3] - main_box[1]

        main_x = (width - main_width) / 2
        main_y = 260 - main_height / 2 - main_box[1]

        draw.text(
            (main_x + 3, main_y + 5),
            main_text,
            font=main_font,
            fill="#dfd2b6",
        )

        draw.text(
            (main_x, main_y),
            main_text,
            font=main_font,
            fill="#29241c",
        )

        secondary_text = "Золотая лента"
        secondary_font = self._fit_font(
            draw=draw,
            text=secondary_text,
            font_path=font_path,
            max_width=720,
            start_size=67,
            minimum_size=35,
        )

        secondary_box = draw.textbbox(
            (0, 0),
            secondary_text,
            font=secondary_font,
        )

        secondary_width = (
            secondary_box[2] - secondary_box[0]
        )

        secondary_x = (
            width - secondary_width
        ) / 2

        draw.text(
            (secondary_x, 442),
            secondary_text,
            font=secondary_font,
            fill="#a07b31",
        )

        footer_font = ImageFont.truetype(
            str(system_font_path),
            22,
        )

        footer_text = family

        footer_box = draw.textbbox(
            (0, 0),
            footer_text,
            font=footer_font,
        )

        footer_width = footer_box[2] - footer_box[0]

        draw.text(
            ((width - footer_width) / 2, 595),
            footer_text,
            font=footer_font,
            fill="#736856",
        )

        output = io.BytesIO()

        image.save(
            output,
            format="WEBP",
            quality=90,
            method=6,
        )

        return output.getvalue()

    @staticmethod
    def _draw_background(
        draw: ImageDraw.ImageDraw,
        width: int,
        height: int,
    ) -> None:
        top = (250, 247, 239)
        bottom = (236, 225, 204)

        for y in range(height):
            ratio = y / max(height - 1, 1)

            color = tuple(
                round(
                    top[channel]
                    + (
                        bottom[channel]
                        - top[channel]
                    )
                    * ratio
                )
                for channel in range(3)
            )

            draw.line(
                (0, y, width, y),
                fill=color,
            )

        draw.rounded_rectangle(
            (38, 38, width - 38, height - 38),
            radius=28,
            outline="#c9a553",
            width=3,
        )

        draw.line(
            (80, 185, width - 80, 185),
            fill="#d6bd82",
            width=2,
        )

        draw.ellipse(
            (width - 310, -130, width + 80, 260),
            outline="#e3cf9e",
            width=3,
        )

        draw.ellipse(
            (-160, height - 220, 220, height + 160),
            outline="#dfc88e",
            width=3,
        )

    @staticmethod
    def _fit_font(
        *,
        draw: ImageDraw.ImageDraw,
        text: str,
        font_path: Path,
        max_width: int,
        start_size: int,
        minimum_size: int,
    ):
        for size in range(
            start_size,
            minimum_size - 1,
            -2,
        ):
            font = ImageFont.truetype(
                str(font_path),
                size,
            )

            box = draw.textbbox(
                (0, 0),
                text,
                font=font,
            )

            width = box[2] - box[0]

            if width <= max_width:
                return font

        return ImageFont.truetype(
            str(font_path),
            minimum_size,
        )
