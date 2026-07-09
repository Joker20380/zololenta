from __future__ import annotations

import os
import uuid

from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField
from django_ckeditor_5.fields import CKEditor5Field
from model_utils import FieldTracker
from django.utils import timezone

from .fields import WEBPField
from .mixins import OccupancyMixin
from users.models import Location


def image_folder(instance, filename):
    return "photos/{}.webp".format(uuid.uuid4().hex)


class Section(models.Model):
    name = models.CharField(max_length=100, verbose_name="Раздел сайта", db_index=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="URL")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("section", kwargs={"section_slug": self.slug})

    class Meta:
        verbose_name = "Раздел сайта"
        verbose_name_plural = "Разделы сайта"
        ordering = ["id"]


class CategoryProg(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории", db_index=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="URL")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("category", kwargs={"cat_slug": self.slug})

    class Meta:
        verbose_name = "Категория проектов"
        verbose_name_plural = "Категории проектов"
        ordering = ["id"]


class Prog(OccupancyMixin, models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="URL")
    photo = WEBPField(upload_to=image_folder, verbose_name="Фото", null=True, blank=True)
    content = CKEditor5Field(blank=True, verbose_name="Текст", config_name="extends")
    photo2 = WEBPField(upload_to=image_folder, verbose_name="Фото2", null=True, blank=True)
    photo3 = WEBPField(upload_to=image_folder, verbose_name="Фото3", null=True, blank=True)
    photo4 = WEBPField(upload_to=image_folder, verbose_name="Фото4", null=True, blank=True)
    prog_statement = CKEditor5Field(blank=True, verbose_name="Положение о проекте", config_name="extends")
    photo5 = WEBPField(upload_to=image_folder, verbose_name="Фото5", null=True, blank=True)
    prog_statement2 = CKEditor5Field(blank=True, verbose_name="Положение о проекте 2 абзац", config_name="extends")
    name_pdffile = models.CharField(max_length=255, verbose_name="Имя PDF файла", null=True, blank=True)
    pdffile = models.FileField(upload_to="pdf/%Y/%m/%d/", verbose_name="PDF", null=True, blank=True)
    time_create = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время создания")
    time_update = models.DateTimeField(auto_now=True, verbose_name="Дата и время обновления")
    time_start = models.DateTimeField(verbose_name="Дата и время начала проекта", null=True, blank=True)
    time_ending = models.DateTimeField(verbose_name="Дата и время окончания проекта", null=True, blank=True)
    is_published = models.BooleanField(verbose_name="Публикация")
    supervisor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="supervisor",
        verbose_name="Руководитель",
        null=True,
        blank=True,
    )
    registration = models.ManyToManyField(User, related_name="progs", verbose_name="Участники проекта", blank=True)
    cat = models.ForeignKey(CategoryProg, on_delete=models.PROTECT, verbose_name="Категория", null=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("project", kwargs={"project_slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"
        ordering = ["time_create", "title"]


class CategoryLecture(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории", db_index=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="URL")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("category_lecture", kwargs={"cat_slug": self.slug})

    class Meta:
        verbose_name = "Категория лекции"
        verbose_name_plural = "Категории лекций"
        ordering = ["id"]


class Lecture(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="URL")
    content = models.CharField(max_length=255, blank=True, null=True, verbose_name="Текст")
    URL = models.URLField(blank=True, verbose_name="Ссылка на видео")
    prog = models.ForeignKey("Prog", on_delete=models.PROTECT, verbose_name="Программа", blank=True, null=True)
    time_create = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время создания")
    time_update = models.DateTimeField(auto_now=True, verbose_name="Дата и время обновления")
    is_published = models.BooleanField(default=True, verbose_name="Публикация")
    cat = models.ForeignKey(CategoryLecture, on_delete=models.PROTECT, verbose_name="Категория", null=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("lecture", kwargs={"lecture_slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Лекции"
        verbose_name_plural = "Лекции"
        ordering = ["time_create", "title"]


class Documents(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="URL")
    content = CKEditor5Field(blank=True, verbose_name="Текст", config_name="extends")
    name_pdffile = models.CharField(max_length=255, verbose_name="Имя PDF файла", null=True, blank=True)
    pdf_file = models.FileField(upload_to="pdf/%Y/%m/%d/", verbose_name="Файл", null=True, blank=True)
    executor = models.ForeignKey(User, on_delete=models.PROTECT, null=True, verbose_name="Исполнитель")
    time_create = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")
    time_update = models.DateTimeField(auto_now=True, verbose_name="Время обновления")
    is_published = models.BooleanField(default=True, verbose_name="Публикация")
    section = models.ManyToManyField(Section, related_name="Документы", verbose_name="Раздел сайта", blank=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("doc", kwargs={"doc_slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"
        ordering = ["time_create"]


class CategoryNews(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории", db_index=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="URL")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("category", kwargs={"cat_slug": self.slug})

    class Meta:
        verbose_name = "Категория новости"
        verbose_name_plural = "Категории новостей"
        ordering = ["id"]


class News(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="URL")
    content = CKEditor5Field(blank=True, verbose_name="Текст", config_name="extends")
    photo = WEBPField(verbose_name="фото 633x550px", upload_to=image_folder, blank=True, null=True)
    content2 = CKEditor5Field(blank=True, null=True, verbose_name="Текст2", config_name="extends")
    photo2 = WEBPField(verbose_name="фото2", upload_to=image_folder, blank=True, null=True)
    photo3 = WEBPField(verbose_name="Фото№3", upload_to=image_folder, blank=True, null=True)
    content3 = CKEditor5Field(blank=True, null=True, verbose_name="Текст3", config_name="extends")
    photo4 = WEBPField(verbose_name="Фото№4", upload_to=image_folder, blank=True, null=True)
    photo5 = WEBPField(verbose_name="Фото№5", upload_to=image_folder, blank=True, null=True)
    content4 = CKEditor5Field(blank=True, null=True, verbose_name="Текст4", config_name="extends")
    time_create = models.DateTimeField(verbose_name="Дата и время создания")
    time_update = models.DateTimeField(auto_now=True, verbose_name="Дата и время обновления")
    is_published = models.BooleanField(default=True, verbose_name="Публикация")
    tracker = FieldTracker(fields=["is_published"])
    cat = models.ForeignKey(CategoryNews, on_delete=models.PROTECT, verbose_name="Категория")
    prog = models.ForeignKey("Prog", on_delete=models.PROTECT, verbose_name="Программа", blank=True, null=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("news", kwargs={"news_slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"
        ordering = ["time_create", "title"]


# ============================================================
# КОНСТРУКТОР ЛЕНТ: опции (цвет/шрифт) + заказы + телеграм-синк
# ============================================================

class RibbonOption(models.Model):
    TYPE_COLOR = "color"
    TYPE_FONT = "font"
    TYPE_CHOICES = [
        (TYPE_COLOR, "Цвет ленты"),
        (TYPE_FONT, "Шрифт"),
    ]

    news = models.OneToOneField(
        "News",
        on_delete=models.CASCADE,
        related_name="ribbon_option",
        verbose_name="Новость-опция",
    )

    opt_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        verbose_name="Тип опции",
        db_index=True,
    )

    css_value = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="CSS значение",
        help_text="Для цвета: #RRGGBB. Для шрифта: font-family, например: Montserrat, sans-serif",
    )

    font_url = models.URLField(
        blank=True,
        default="",
        verbose_name="URL шрифта (stylesheet)",
        help_text="Только для opt_type=font. Вставляй URL на CSS, который подключается через <link rel='stylesheet'>",
    )

    is_active = models.BooleanField(default=True, verbose_name="Активно", db_index=True)

    class Meta:
        verbose_name = "Опция конструктора лент"
        verbose_name_plural = "Опции конструктора лент"
        indexes = [
            models.Index(fields=["opt_type", "is_active"], name="idx_ribbonopt_type_active"),
        ]

    def __str__(self):
        return f"{self.get_opt_type_display()}: {self.news.title}"




def generate_edit_token():
    """Возвращает новый уникальный токен для каждого заказа."""
    return uuid.uuid4().hex



class RibbonColor(models.Model):
    """
    Доменный каталог цветов ленты.

    Это новая чистая сущность конструктора.
    Не привязана к News и не зависит от legacy RibbonOption.
    """

    title = models.CharField("Название", max_length=120)
    slug = models.SlugField("Slug", max_length=140, unique=True)
    hex_value = models.CharField(
        "HEX цвет",
        max_length=7,
        help_text="Например: #7A1430",
    )
    image = models.ImageField(
        "Фото/превью ленты",
        upload_to="ribbon/colors/%Y/%m/%d/",
        blank=True,
        null=True,
    )
    sort_order = models.PositiveIntegerField("Порядок", default=100)
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Цвет ленты"
        verbose_name_plural = "Цвета лент"
        ordering = ("sort_order", "title")

    def __str__(self):
        return self.title


class RibbonTextColor(models.Model):
    """
    Каталог цветов текста/печати/фольги.
    """

    title = models.CharField("Название", max_length=120)
    slug = models.SlugField("Slug", max_length=140, unique=True)
    hex_value = models.CharField(
        "HEX цвет",
        max_length=7,
        help_text="Например: #FFFFFF",
    )
    sort_order = models.PositiveIntegerField("Порядок", default=100)
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Цвет текста на ленте"
        verbose_name_plural = "Цвета текста на ленте"
        ordering = ("sort_order", "title")

    def __str__(self):
        return self.title


class RibbonFont(models.Model):
    """
    Каталог шрифтов конструктора.

    font_family хранит CSS font-family, который используется в preview и заказе.
    font_file нужен для локальных шрифтов, preview_image — для карточки выбора.
    """

    title = models.CharField("Название", max_length=120)
    slug = models.SlugField("Slug", max_length=140, unique=True)
    font_family = models.CharField(
        "CSS font-family",
        max_length=160,
        help_text="Например: 'Romantique Script', cursive",
    )
    font_file = models.FileField(
        "Файл шрифта",
        upload_to="ribbon/fonts/",
        blank=True,
        null=True,
    )
    preview_image = models.ImageField(
        "Превью шрифта",
        upload_to="ribbon/fonts/previews/%Y/%m/%d/",
        blank=True,
        null=True,
    )
    sort_order = models.PositiveIntegerField("Порядок", default=100)
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Шрифт ленты"
        verbose_name_plural = "Шрифты лент"
        ordering = ("sort_order", "title")

    def __str__(self):
        return self.title


class RibbonTemplate(models.Model):
    """
    Шаблон/макет ленты.

    На первом этапе это каталог выбора.
    Позже сюда можно добавить JSON-настройки размещения текста, иконок, линий, венков и т.д.
    """

    title = models.CharField("Название", max_length=120)
    slug = models.SlugField("Slug", max_length=140, unique=True)
    description = models.TextField("Описание", blank=True)
    preview_image = models.ImageField(
        "Превью шаблона",
        upload_to="ribbon/templates/%Y/%m/%d/",
        blank=True,
        null=True,
    )
    layout_config = models.JSONField(
        "Настройки шаблона",
        default=dict,
        blank=True,
        help_text="JSON-конфиг макета. Можно оставить пустым.",
    )
    sort_order = models.PositiveIntegerField("Порядок", default=100)
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Шаблон ленты"
        verbose_name_plural = "Шаблоны лент"
        ordering = ("sort_order", "title")

    def __str__(self):
        return self.title


class RibbonOrder(models.Model):
    # --- идентификаторы / доступ ---
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    edit_token = models.CharField(
        max_length=64,
        unique=True,
        default=generate_edit_token,
        db_index=True,
        verbose_name="Токен редактирования",
    )

    review_token = models.CharField(
        max_length=64,
        unique=True,
        default=generate_edit_token,
        db_index=True,
        verbose_name="Токен для отзыва",
        help_text="Приватная ссылка для клиента без регистрации.",
    )

    # --- макет / параметры ---
    text = models.CharField(max_length=120, verbose_name="Текст на ленте")

    # NEW: без справочников (основная правда для нового конструктора)
    ribbon_bg = models.CharField(
        max_length=7,
        default="#1E4ED8",
        blank=True,
        verbose_name="Цвет ленты (HEX)",
        help_text="Например: #1E4ED8",
    )

    font_family = models.CharField(
        max_length=120,
        default="'Montserrat', sans-serif",
        blank=True,
        verbose_name="Шрифт (CSS font-family)",
        help_text="Например: 'Montserrat', sans-serif",
    )

    text_color = models.CharField(
        max_length=7,
        default="#FFFFFF",
        verbose_name="Цвет текста (HEX)",
        help_text="Например: #FFFFFF или #000000",
    )

    # LEGACY: старые справочники (News) — оставляем, но делаем optional
    # (чтобы не ломать старые заказы/админку и можно было мигрировать постепенно)
    ribbon_color = models.ForeignKey(
        RibbonColor,
        verbose_name="Цвет ленты",
        related_name="orders",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    ribbon_text_color = models.ForeignKey(
        RibbonTextColor,
        verbose_name="Цвет текста",
        related_name="orders",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    ribbon_font = models.ForeignKey(
        RibbonFont,
        verbose_name="Шрифт",
        related_name="orders",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    ribbon_template = models.ForeignKey(
        RibbonTemplate,
        verbose_name="Шаблон ленты",
        related_name="orders",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    color_news = models.ForeignKey(
        "News",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ribbon_orders_color",
        verbose_name="Цвет ленты (новость, legacy)",
    )
    font_news = models.ForeignKey(
        "News",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ribbon_orders_font",
        verbose_name="Шрифт (новость, legacy)",
    )

    FOIL_NONE = "none"
    FOIL_GOLD = "gold"
    FOIL_SILVER = "silver"
    FOIL_CHOICES = [
        (FOIL_NONE, "Без фольги"),
        (FOIL_GOLD, "Фольга золото"),
        (FOIL_SILVER, "Фольга серебро"),
    ]

    foil = models.CharField(
        max_length=10,
        choices=FOIL_CHOICES,
        default=FOIL_NONE,
        verbose_name="Фольга (эффект печати)",
    )

    # --- группа / список ФИО ---
    is_group_order = models.BooleanField(default=False, verbose_name="Групповой заказ")
    persons_count = models.PositiveIntegerField(default=1, verbose_name="Кол-во лент/человек")

    persons_list = models.TextField(
        blank=True,
        default="",
        verbose_name="Список ФИО (по строкам)",
        help_text="Одна строка = один человек. Например: Иванов Иван Иванович",
    )

    comment = models.TextField(blank=True, default="", verbose_name="Комментарий/пожелания")

    # --- контактные данные ---
    name = models.CharField(max_length=120, blank=True, default="", verbose_name="Контактное лицо")
    phone = models.CharField(max_length=30, blank=True, default="", verbose_name="Телефон")
    email = models.EmailField(blank=True, default="", verbose_name="Email")

    # --- статусная модель (чтобы в телеге выглядело как CRM) ---
    STATUS_NEW = "new"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_WAIT_APPROVAL = "wait_approval"
    STATUS_DONE = "done"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_NEW, "Новая"),
        (STATUS_IN_PROGRESS, "В работе"),
        (STATUS_WAIT_APPROVAL, "Ожидает согласования"),
        (STATUS_DONE, "Завершена"),
        (STATUS_ARCHIVED, "Архив"),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        db_index=True,
        verbose_name="Статус",
    )

    manager_note = models.TextField(blank=True, default="", verbose_name="Заметка менеджера")
    source = models.CharField(
        max_length=50,
        blank=True,
        default="site",
        verbose_name="Источник",
        help_text="Например: site / instagram / whatsapp",
    )

    # --- телеграм интеграция: для обновления одной “карточки” заявки, а не спама ---
    tg_chat_id = models.BigIntegerField(blank=True, null=True, db_index=True, verbose_name="TG chat_id (карточка)")
    tg_message_id = models.IntegerField(blank=True, null=True, db_index=True, verbose_name="TG message_id (карточка)")
    tg_thread_root_id = models.IntegerField(
        blank=True,
        null=True,
        db_index=True,
        verbose_name="TG root_message_id (тред/чат заявки)",
        help_text="Если будешь делать треды/форумы: сюда кладёшь ID корневого сообщения/темы",
    )
    tg_last_synced_at = models.DateTimeField(blank=True, null=True, verbose_name="Последняя синхронизация с TG")
    tg_lock_until = models.DateTimeField(blank=True, null=True, verbose_name="TG lock until")

    class Meta:
        verbose_name = "Заказ ленты"
        verbose_name_plural = "Заказы лент"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"], name="idx_ribbonorder_created"),
            models.Index(fields=["status", "created_at"], name="idx_ribbonorder_status_created"),
        ]

    def __str__(self):
        return f"Заказ {self.id} ({self.created_at:%d.%m.%Y})"

    def persons_lines(self) -> list[str]:
        if not self.persons_list:
            return []
        return [line.strip() for line in self.persons_list.splitlines() if line.strip()]

    def can_tg_sync(self) -> bool:
        if self.tg_lock_until and self.tg_lock_until > timezone.now():
            return False
        return True



class RibbonOrderReview(models.Model):
    RATING_CHOICES = [
        (5, "5 — отлично"),
        (4, "4 — хорошо"),
        (3, "3 — нормально"),
        (2, "2 — плохо"),
        (1, "1 — очень плохо"),
    ]

    order = models.OneToOneField(
        "RibbonOrder",
        on_delete=models.CASCADE,
        related_name="order_review",
        verbose_name="Заказ ленты",
    )
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        default=5,
        verbose_name="Оценка",
    )
    body = models.TextField(verbose_name="Отзыв")
    photo = models.ImageField(
        upload_to="reviews/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name="Фото",
    )
    active = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Опубликован",
        help_text="Отзыв появляется на сайте только после публикации.",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлён")

    class Meta:
        verbose_name = "Отзыв по заказу ленты"
        verbose_name_plural = "Отзывы по заказам лент"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["active", "created_at"], name="idx_ribrev_active_created"),
        ]

    def __str__(self):
        return "Отзыв по заказу {}".format(self.order_id)

    @property
    def client_name(self):
        return (self.order.name or "").strip() or "Клиент"

    @property
    def client_email(self):
        return (self.order.email or "").strip()

    @property
    def client_phone(self):
        return (self.order.phone or "").strip()





class Service(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="URL")
    content = CKEditor5Field(blank=True, verbose_name="Текст")
    price = models.DecimalField(decimal_places=2, max_digits=20, default=0.00, verbose_name="Цена")
    photo = models.ImageField(upload_to="photos/%Y/%m/%d/", verbose_name="Фото", blank=True, null=True)
    photo2 = models.ImageField(upload_to="photos/%Y/%m/%d/", verbose_name="Фото2", blank=True, null=True)
    photo3 = models.ImageField(upload_to="photos/%Y/%m/%d/", verbose_name="Фото3", blank=True, null=True)
    photo4 = models.ImageField(upload_to="photos/%Y/%m/%d/", verbose_name="Фото4", blank=True, null=True)
    photo5 = models.ImageField(upload_to="photos/%Y/%m/%d/", verbose_name="Фото5", blank=True, null=True)
    photo6 = models.ImageField(upload_to="photos/%Y/%m/%d/", verbose_name="Фото6", blank=True, null=True)
    time_create = models.DateTimeField(verbose_name="Дата и время создания")
    time_update = models.DateTimeField(verbose_name="Дата и время обновления")
    is_published = models.BooleanField(default=True, verbose_name="Публикация")
    number_of_employees = models.IntegerField(verbose_name="Количество сотрудников", default=0)
    executor = models.ManyToManyField(User, related_name="products", verbose_name="Исполнитель", blank=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("services", kwargs={"services_slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        return super().save(*args, **kwargs)

    class Meta:
        unique_together = [["title", "slug"]]
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"


class Subscriber(models.Model):
    email = models.EmailField(unique=True, verbose_name="Email")
    is_active = models.BooleanField(default=True, verbose_name="Активна ли подписка")
    unsubscribe_token = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Токен для отписки",
    )
    subscribed_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата подписки")

    class Meta:
        verbose_name = "Подписчик"
        verbose_name_plural = "Подписчики"
        ordering = ["email"]
        indexes = [
            models.Index(fields=["email"], name="idx_subscriber_email"),
            models.Index(fields=["is_active"], name="idx_subscriber_active"),
        ]

    def __str__(self) -> str:
        return self.email

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)


class ContactGroup(models.Model):
    """Группа контактов (например, Администрация, Филиал)"""

    name = models.CharField(max_length=100, verbose_name="Название группы")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")

    class Meta:
        verbose_name = "Группа контактов"
        verbose_name_plural = "Группы контактов"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.name


class Contact(models.Model):
    """Конкретный контакт"""

    group = models.ForeignKey(
        ContactGroup,
        on_delete=models.CASCADE,
        verbose_name="Группа",
        related_name="contacts",
    )
    name = models.CharField(max_length=100, verbose_name="Название")
    phone = models.CharField(max_length=20, verbose_name="Телефон", blank=True)
    email = models.EmailField(verbose_name="Email", blank=True)
    address = models.CharField(max_length=255, verbose_name="Адрес", blank=True)
    description = models.TextField(verbose_name="Описание", blank=True)
    is_main = models.BooleanField(default=False, verbose_name="Основной контакт")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")

    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="contacts",
        verbose_name="Местоположение",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Контакт"
        verbose_name_plural = "Контакты"
        ordering = ["order", "id"]
        indexes = [
            models.Index(fields=["is_main"], name="idx_contact_is_main"),
            models.Index(fields=["group", "order"], name="idx_contact_group_order"),
        ]

    def __str__(self) -> str:
        return f"{self.group}: {self.name}"


class ContactRequest(models.Model):
    name = models.CharField(max_length=100, verbose_name="Имя")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, verbose_name="Телефон", blank=True, null=True)
    message = models.TextField(verbose_name="Сообщение")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Контактное лицо",
        related_name="requests",
    )

    class Meta:
        verbose_name = "Запрос на контакт"
        verbose_name_plural = "Запросы на контакт"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"], name="idx_contactreq_created_at"),
            models.Index(fields=["contact"], name="idx_contactreq_contact"),
        ]

    def __str__(self) -> str:
        contact_name = self.contact.name if self.contact else "Общий запрос"
        return f"{self.name} → {contact_name} ({self.created_at:%d.%m.%Y})"


