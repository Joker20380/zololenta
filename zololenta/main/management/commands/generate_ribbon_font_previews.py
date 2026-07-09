from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from main.models import RibbonOption

try:
    from PIL import Image, ImageDraw, ImageFont, features
except ImportError as exc:
    raise CommandError("Pillow не установлен в виртуальном окружении.") from exc


@dataclass(frozen=True)
class LocalFontSource:
    family: str
    filename: str


LOCAL_FONT_SOURCES = {
    "Romantique Script": LocalFontSource("Romantique Script", "romantique-script.ttf"),
    "Good Vibes Pro": LocalFontSource("Good Vibes Pro", "good-vibes-pro.ttf"),
    "Zither Script": LocalFontSource("Zither Script", "zither-script.ttf"),
    "Grosvenor Script": LocalFontSource("Grosvenor Script", "grosvenor-script.ttf"),
    "Esenin Script": LocalFontSource("Esenin Script", "esenin-script.ttf"),
    "Mon Amour One": LocalFontSource("Mon Amour One", "monamourone-medium.ttf"),
    "Magnolia Script": LocalFontSource("Magnolia Script", "magnolia-script.otf"),
    "Belissimo Script": LocalFontSource("Belissimo Script", "belissimo-script.ttf"),
    "Mazurka Script": LocalFontSource("Mazurka Script", "mazurka-script.ttf"),
    "Ceremonious One": LocalFontSource("Ceremonious One", "ceremoniousone.ttf"),
    "Astoria Script One": LocalFontSource("Astoria Script One", "astoria-script-one.ttf"),
}


class Command(BaseCommand):
    help = "Генерирует WebP-превью для локальных шрифтов конструктора."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--force", action="store_true")
        parser.add_argument("--family", action="append", default=[])

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        force = options["force"]
        selected_families = set(options["family"])

        if not features.check("webp"):
            raise CommandError("Pillow не поддерживает WebP.")

        font_dir = Path(settings.BASE_DIR) / "static" / "zololenta" / "fonts" / "ribbon"
        if not font_dir.exists():
            raise CommandError(f"Папка шрифтов не найдена: {font_dir}")

        ui_font = self._find_ui_font()

        qs = (
            RibbonOption.objects
            .filter(opt_type=RibbonOption.TYPE_FONT, is_active=True)
            .select_related("news")
            .order_by("id")
        )

        saved = 0
        skipped = 0
        errors = 0

        for option in qs:
            family = self._extract_family(option.css_value)

            if selected_families and family not in selected_families:
                continue

            source = LOCAL_FONT_SOURCES.get(family)
            if not source:
                self.stdout.write(self.style.WARNING(f"SKIP: нет источника для {family!r}"))
                skipped += 1
                continue

            font_path = font_dir / source.filename
            if not font_path.exists():
                self.stdout.write(self.style.ERROR(f"MISSING: {font_path}"))
                errors += 1
                continue

            if option.news.photo and not force:
                self.stdout.write(f"EXISTS: {option.news.title} — {option.news.photo.name}")
                skipped += 1
                continue

            try:
                image_bytes = self._render_preview(
                    family=family,
                    font_path=font_path,
                    ui_font_path=ui_font,
                )
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"ERROR: {family} — {exc}"))
                errors += 1
                continue

            filename = f"ribbon-font-local-{slugify(family) or option.pk}.webp"

            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"DRY RUN: {option.news.title} — {len(image_bytes)} bytes"
                    )
                )
                saved += 1
                continue

            option.news.photo.save(filename, ContentFile(image_bytes), save=False)
            option.news.save(update_fields=["photo"])

            self.stdout.write(
                self.style.SUCCESS(
                    f"SAVED: {option.news.title} — {option.news.photo.name}"
                )
            )
            saved += 1

        self.stdout.write("")
        self.stdout.write(f"saved_or_checked: {saved}")
        self.stdout.write(f"skipped: {skipped}")
        self.stdout.write(f"errors: {errors}")

        if errors:
            raise CommandError("Есть ошибки генерации превью.")

    @staticmethod
    def _extract_family(css_value: str) -> str:
        value = (css_value or "").strip()
        family = value.split(",", 1)[0].strip()
        return family.strip("'\"")

    @staticmethod
    def _find_ui_font() -> Path | None:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]

        for candidate in candidates:
            p = Path(candidate)
            if p.exists():
                return p

        return None

    @staticmethod
    def _font_supports_text(font_path: Path, text: str) -> bool:
        font = ImageFont.truetype(str(font_path), size=72)
        mask = font.getmask(text)
        return bool(mask.getbbox())

    @classmethod
    def _render_preview(
        cls,
        *,
        family: str,
        font_path: Path,
        ui_font_path: Path | None,
    ) -> bytes:
        width = 900
        height = 420

        image = Image.new("RGB", (width, height), "#FFF7FA")
        draw = ImageDraw.Draw(image)

        draw.rounded_rectangle(
            (24, 24, width - 24, height - 24),
            radius=36,
            fill="#FFFFFF",
            outline="#E9CFD9",
            width=3,
        )

        draw.rounded_rectangle(
            (54, 70, width - 54, height - 116),
            radius=28,
            fill="#FFF1F6",
            outline="#EFD4DE",
            width=2,
        )

        cyr_text = "Выпускник 2026"
        latin_text = "Graduate 2026"

        sample_text = cyr_text
        if not cls._font_supports_text(font_path, cyr_text):
            sample_text = latin_text

        selected_font = None
        selected_bbox = None

        for size in range(112, 42, -2):
            candidate = ImageFont.truetype(str(font_path), size=size)
            bbox = draw.textbbox((0, 0), sample_text, font=candidate)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

            if text_w <= width - 150 and text_h <= height - 190:
                selected_font = candidate
                selected_bbox = bbox
                break

        if selected_font is None or selected_bbox is None:
            selected_font = ImageFont.truetype(str(font_path), size=48)
            selected_bbox = draw.textbbox((0, 0), sample_text, font=selected_font)

        text_w = selected_bbox[2] - selected_bbox[0]
        text_h = selected_bbox[3] - selected_bbox[1]

        x = (width - text_w) / 2 - selected_bbox[0]
        y = 168 - text_h / 2 - selected_bbox[1]

        draw.text((x, y), sample_text, font=selected_font, fill="#7A1430")

        if ui_font_path:
            label_font = ImageFont.truetype(str(ui_font_path), size=28)
            note_font = ImageFont.truetype(str(ui_font_path), size=22)
        else:
            label_font = ImageFont.load_default()
            note_font = ImageFont.load_default()

        label = family
        label_bbox = draw.textbbox((0, 0), label, font=label_font)
        label_w = label_bbox[2] - label_bbox[0]

        draw.text(
            ((width - label_w) / 2, height - 92),
            label,
            font=label_font,
            fill="#8E4058",
        )

        note = "локальный шрифт"
        if sample_text == latin_text:
            note = "нет кириллицы в файле"

        note_bbox = draw.textbbox((0, 0), note, font=note_font)
        note_w = note_bbox[2] - note_bbox[0]

        draw.text(
            ((width - note_w) / 2, height - 56),
            note,
            font=note_font,
            fill="#B26B82",
        )

        output = io.BytesIO()
        image.save(output, format="WEBP", quality=90, method=6)
        return output.getvalue()
