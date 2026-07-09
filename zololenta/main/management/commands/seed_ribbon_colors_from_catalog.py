from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from main.models import News, RibbonOption


@dataclass(frozen=True)
class ColorSpec:
    title: str
    code: str
    hex_value: str


PALETTE_RAW = """
Молочный|нет близкого / 12-0601|#E9E5D3
Сливочный|нет близкого / 11-0606|#E8DAAA
Кремовый|нет близкого / 12-1006|#EDE0DE
Телесный|нет близкого / 11-1305|#E5C7AB
Светло-бежевый|7506C / 13-0814|#EED4AD
Бежевый|468C / 13-0922|#E5D5AA
Темно-бежевый|874C / 16-0924|#BFAC87
Золотистый|1245C / 16-0953|#AF993E
Нежный золотой|1245C / 16-0953|#BCAC71
Пастельный персиковый|нет близкого / 12-1010|#D5CDC7
Персиковый|726C / 14-1122|#E1B795
Кофейный|7611C / 14-1307|#C9B3A8
Камея-розовый|7633C / нет близкого|#B4A09C
Светло-имбирный|7632C / 13-3801|#BBAF9F
Имбирный|727C / 16-1221|#C1998D
Светло-коричневый|479C / 17-1224|#A17A5D
Медно-коричневый|7566C / 18-1163|#A27649
Каштановый|2320C / 19-1034|#7C684E
Коричневый|4625C / 18-1130|#5B4641
Лакричный|412C / 19-1109|#4D4742
Зелено-желтый|380C / 13-0650|#CBCD3C
Желтый|012C / 14-0756|#DEB84A
Желто-золотой|1225C / 13-0840|#DFA044
Желто-оранжевый|1375C / 14-1064|#E18B3A
Светло-оранжевый|151C / 15-1160|#E18952
Оранжевый|159C / 17-1257|#C97541
Терракотовый|484C / 17-1446|#8D3C26
Апельсиновый|1655C / 16-1364|#E27D53
Неоновый оранжево-розовый|805C / нет близкого|#E98878
Бледно-розовый|706C / 13-2804|#E6D0CE
Клубнично-сливочный|7422C / 12-1708|#F6BDBE
Нежно-розовый|182C / 14-1911|#ECB5C4
Тюльпановый|516C / 13-2806|#E9B6D2
Роза-Дикая|695C / 15-2215|#BD9096
Роза-Пыльная|694C / 16-1715|#CFA09B
Светло-розовый|190C / 15-2216|#E87BB2
Коралловый|709C / 17-1744|#E06A7B
Розовый|191C / 18-1755|#E66990
Орхидейный|674C / 18-2333|#E965A1
Фуксия-розовый|215C / 18-2436|#D784C3
Фиалковый|7431C / 17-1818|#BD829C
Малиновый|2452C / 18-1945|#B53D63
Алый|186C / 17-1664|#BF3B42
Огненный|3556C / 17-1563|#F13837
Ярко-красный|1795C / 18-1664|#B3282E
Красный|193C / 18-1664|#99273E
Темно-красный|201C / 19-1761|#8D2C31
Бутон-красный|2041C / 18-1950|#932E50
Винный|683C / 19-2033|#764552
Бордовый|7428C / 18-2027|#987C86
Бледно-голубой|656C / нет близкого|#D2DEE1
Светло-голубой|544C / 13-4409|#C7D4E1
Нежно-сизый|2706C / 14-4110|#B2BAD5
Лазурный|629C / 14-4620|#8BDBDA
Эвкалиптовый|549C / 15-5210|#81B4A1
Пастельный-мятный|573C / 12-5407|#AAD2B5
Мятный|331C / 13-5409|#A9D0AF
Шалфейный|5585C / 15-5812|#B0C1B2
Оливковый|2404C / 15-6313|#E0E1D2
Бирюзовый|3252C / 15-5425|#C9E1E0
Нежно-голубой|7451C / 14-4121|#9BB3CB
Небесный|2169C / 14-4320|#8BB8DC
Адриатический|2123C / 17-3936|#677CC3
Голубой|638C / 14-4522|#5BAECC
Волшебно-голубой|7710C / 16-4834|#09B3BA
Аквамариновый|2220C / 16-4719|#7BA5A7
Морская волна|322C / 18-4735|#0B8882
Ярко-синий|2193C / 18-4440|#458DC8
Фантастический Синий|2145C / 19-4150|#5170C1
Синий|7687C / 19-4056|#5271C5
Незабудковый|2705C / 16-3925|#A2ABDF
Синий-дым|2111C / 18-3932|#7892BE
Джинс|3590C / 18-3945|#5E67B6
Темный океанический|2767C / 19-3923|#3C3D59
Темно-синий|5225C / 19-3925|#373A6A
Глубинный синий|532C / 19-3810|#3E3D47
Лаванда-сиреневый|2099C / 15-3817|#9B8AAE
Бледно-сиреневый|нет близкого / 15-3807|#C6C9DF
Розово-сиреневый|2071C / 14-3612|#D1CCE6
Розово-лиловый|680C / 14-3209|#F2B6DA
Аметистовый|519C / 18-3013|#97818C
Светло-сиреневый|7439C / 16-3520|#A87AAE
Сиреневый|2593C / 18-3324|#843F97
Сливовый|269C / 19-3640|#623D67
Фиолетовый|518C / 19-3323|#51315B
Изюм-темный|7644C / 19-1617|#644B4D
Сиренево-фиолетовый|2112C / 18-3840|#664F98
Кислотно-зеленый|802C / нет близкого|#0CC61D
Мятно-зеленый|351C / 13-0117|#C8E7BF
Полынный|5555C / 18-6216|#74896B
Необычный Зеленый|2243C / 17-5641|#4EB288
Зеленый|362C / 16-0235|#7BBA43
Папоротник|348C / 17-6153|#569B47
Сочный зеленый|2426C / 16-6340|#73BA51
Темно-зеленый|349C / 18-6030|#4F804E
Изумрудный|7736C / 19-6311|#425742
Лесной зеленый|342C / 18-6024|#4D8152
Сине-зеленый еловый|3308C / 18-5424|#286D62
Зелено-синий морской|7477C / 19-4526|#147D91
Хаки|448C / 18-0430|#6F6E4E
Серебристый|877C / 14-4102|#D4D4D7
Серый|Cool Gray 6C / 16-3802|#B2B2B7
Темно-серый стальной|424C / 17-3914|#A4A4A2
Темно-серый|2334C / 18-3905|#625C58
Глубокий серый|2379C / 19-3930|#52535B
""".strip()


ALIASES = {
    "Пастельный персиковый": ["Пастельный-персиковый"],
    "Желто-золотой": ["Желто-Золотой"],
    "Желто-оранжевый": ["Желто-Оранжевый"],
    "Светло-оранжевый": ["Светло-Оранжевый"],
    "Бледно-розовый": ["Бледно-Розовый"],
    "Роза-Дикая": ["Роза дикая", "Роза-Дикая"],
    "Роза-Пыльная": ["Роза-пыльная", "Роза-Пыльная"],
    "Бутон-красный": ["Бутон красный"],
    "Неоновый оранжево-розовый": ["Оранжево-розовый"],
    "Папоротник": ["Папоротник зеленый"],
    "Сине-зеленый еловый": ["Еловый"],
    "Зелено-синий морской": ["Морской"],
    "Темно-серый стальной": ["Стальной"],
}


def normalize(value: str) -> str:
    value = (value or "").strip().lower().replace("ё", "е")
    value = re.sub(r"[\s\-–—_]+", "", value)
    return value


def parse_palette() -> list[ColorSpec]:
    items = []

    for line in PALETTE_RAW.splitlines():
        title, code, hex_value = [part.strip() for part in line.split("|")]
        items.append(
            ColorSpec(
                title=title,
                code=code,
                hex_value=hex_value.upper(),
            )
        )

    return items


def unique_slug(base: str) -> str:
    slug = base
    index = 2

    while News.objects.filter(slug=slug).exists():
        slug = f"{base}-{index}"
        index += 1

    return slug


def hex_to_rgb(hex_value: str) -> tuple[int, int, int]:
    value = hex_value.strip().lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


class Command(BaseCommand):
    help = "Обновляет каталог цветов лент по таблице сатиновых цветов."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать изменения без сохранения.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        palette = parse_palette()

        existing = list(
            RibbonOption.objects
            .filter(opt_type=RibbonOption.TYPE_COLOR)
            .select_related("news")
            .order_by("id")
        )

        by_title = {}
        for option in existing:
            if option.news_id:
                by_title.setdefault(normalize(option.news.title), option)

        used_option_ids = set()

        created = 0
        updated = 0
        reactivated = 0
        deactivated = 0

        base_time = timezone.now() + timedelta(days=1)

        if dry_run:
            self.stdout.write(f"Palette colors: {len(palette)}")
            self.stdout.write(f"Existing color options: {len(existing)}")

        with transaction.atomic():
            for index, spec in enumerate(palette, start=1):
                option = by_title.get(normalize(spec.title))

                if option is None:
                    for alias in ALIASES.get(spec.title, []):
                        option = by_title.get(normalize(alias))
                        if option is not None:
                            break

                order_time = base_time - timedelta(seconds=index)

                r, g, b = hex_to_rgb(spec.hex_value)
                content = (
                    f"<p>Цвет сатиновой ленты из каталога.</p>"
                    f"<p>Код: {spec.code}</p>"
                    f"<p>RGB: {r}, {g}, {b}. HEX: {spec.hex_value}</p>"
                )

                if option is None:
                    if dry_run:
                        self.stdout.write(
                            f"WOULD CREATE: {index:03d}. {spec.title} — {spec.hex_value}"
                        )
                        created += 1
                        continue

                    news = News.objects.create(
                        title=spec.title,
                        slug=unique_slug(f"ribbon-color-catalog-{index:03d}"),
                        content=content,
                        cat_id=3,
                        is_published=True,
                        time_create=order_time,
                        time_update=order_time,
                    )

                    option = RibbonOption.objects.create(
                        news=news,
                        opt_type=RibbonOption.TYPE_COLOR,
                        css_value=spec.hex_value,
                        is_active=True,
                    )

                    used_option_ids.add(option.id)
                    created += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"CREATE #{option.id}: {spec.title} — {spec.hex_value}"
                        )
                    )
                    continue

                used_option_ids.add(option.id)

                changed = []

                if option.css_value.upper() != spec.hex_value:
                    changed.append(f"css {option.css_value} -> {spec.hex_value}")
                    option.css_value = spec.hex_value

                if not option.is_active:
                    option.is_active = True
                    changed.append("reactivate")
                    reactivated += 1

                news = option.news

                if news.title != spec.title:
                    changed.append(f"title {news.title!r} -> {spec.title!r}")
                    news.title = spec.title

                news.content = content
                news.is_published = True

                if dry_run:
                    if changed:
                        updated += 1
                        self.stdout.write(
                            f"WOULD UPDATE #{option.id}: {spec.title} — "
                            + "; ".join(changed)
                        )
                    else:
                        self.stdout.write(
                            f"KEEP #{option.id}: {spec.title} — {spec.hex_value}"
                        )
                    continue

                option.save(update_fields=["css_value", "is_active"])
                news.save(update_fields=["title", "content", "is_published"])
                News.objects.filter(pk=news.pk).update(time_update=order_time)

                if changed:
                    updated += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"UPDATE #{option.id}: {spec.title} — {spec.hex_value}"
                        )
                    )

            for option in existing:
                if option.id in used_option_ids:
                    continue

                if not option.is_active:
                    continue

                if dry_run:
                    deactivated += 1
                    self.stdout.write(
                        f"WOULD DEACTIVATE #{option.id}: {option.news.title}"
                    )
                    continue

                option.is_active = False
                option.save(update_fields=["is_active"])
                deactivated += 1

                self.stdout.write(
                    self.style.WARNING(
                        f"DEACTIVATE #{option.id}: {option.news.title}"
                    )
                )

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Dry-run завершён." if dry_run else "Каталог цветов обновлён."
            )
        )
        self.stdout.write(f"Палитра: {len(palette)}")
        self.stdout.write(f"Создано: {created}")
        self.stdout.write(f"Обновлено: {updated}")
        self.stdout.write(f"Повторно активировано: {reactivated}")
        self.stdout.write(f"Отключено старых: {deactivated}")
