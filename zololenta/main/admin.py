from django.contrib import admin, messages
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.utils import timezone
from import_export.admin import ImportExportModelAdmin

from .models import (
    Section, CategoryNews, News,
    CategoryLecture, Lecture,
    CategoryProg, Prog,
    Documents, Service, Subscriber,
    ContactGroup, Contact, ContactRequest, RibbonOrderReview,
    RibbonOption, RibbonOrder,
)


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    list_display_links = ("id", "name")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(CategoryNews)
class CategoryNewsAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    list_display_links = ("id", "name")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(News)
class NewsAdmin(ImportExportModelAdmin):
    list_display = ("id", "title", "get_photo", "time_create", "time_update", "is_published")
    list_display_links = ("id", "title")
    search_fields = ("title", "content")
    list_editable = ("is_published",)
    list_filter = ("is_published", "time_create", "cat")
    prepopulated_fields = {"slug": ("title",)}

    def get_photo(self, obj):
        if obj.photo:
            return mark_safe(f"<img src='{obj.photo.url}' width=50>")
        return None

    get_photo.short_description = "Фото"


@admin.register(CategoryLecture)
class CategoryLectureAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    list_display_links = ("id", "name")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "time_create", "is_published")
    list_display_links = ("id", "title")
    search_fields = ("title",)
    list_editable = ("is_published",)
    list_filter = ("is_published", "time_create")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(CategoryProg)
class CategoryProgAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    list_display_links = ("id", "name")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Prog)
class ProgAdmin(ImportExportModelAdmin):
    list_display = ("id", "title", "get_photo", "supervisor", "time_create", "is_published")
    list_display_links = ("id", "title")
    search_fields = ("title",)
    list_editable = ("is_published",)
    list_filter = ("is_published", "time_create")
    filter_horizontal = ("registration",)
    prepopulated_fields = {"slug": ("title",)}

    def get_photo(self, obj):
        if obj.photo:
            return mark_safe(f"<img src='{obj.photo.url}' width=50>")
        return None

    get_photo.short_description = "Фото"


@admin.register(Documents)
class DocumentsAdmin(ImportExportModelAdmin):
    list_display = ("id", "title", "name_pdffile", "is_published")
    list_display_links = ("id", "title", "is_published")
    search_fields = ("title",)
    list_filter = ("is_published", "time_create")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Service)
class ServiceAdmin(ImportExportModelAdmin):
    list_display = ("id", "title", "time_create", "is_published")
    list_display_links = ("id", "title")
    search_fields = ("title",)
    list_editable = ("is_published",)
    list_filter = ("is_published", "time_create")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "is_active", "subscribed_at")
    list_display_links = ("id", "email")
    search_fields = ("email",)
    list_filter = ("is_active", "subscribed_at")


@admin.register(ContactGroup)
class ContactGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "contacts_count")
    list_editable = ("order",)
    ordering = ("order",)

    def contacts_count(self, obj):
        return obj.contacts.count()

    contacts_count.short_description = "Кол-во контактов"


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "group", "phone", "email", "is_main", "order")
    list_filter = ("group", "is_main")
    list_editable = ("is_main", "order")
    search_fields = ("name", "phone", "email")
    fieldsets = (
        (None, {"fields": ("group", "name", "is_main", "order", "location")}),
        ("Контактная информация", {"fields": ("phone", "email", "address", "description")}),
    )


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "contact_link", "created_at", "is_new")
    list_filter = ("created_at", "contact__group")
    search_fields = ("name", "email", "phone", "message")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"

    def contact_link(self, obj):
        if obj.contact:
            return format_html(
                '<a href="/admin/contacts/contact/{}/change/">{}</a>',
                obj.contact.id, obj.contact.name
            )
        return "-"

    contact_link.short_description = "Контакт"

    def is_new(self, obj):
        return obj.created_at.date() == timezone.now().date()

    is_new.boolean = True
    is_new.short_description = "Новый?"


@admin.register(RibbonOrderReview)
class RibbonOrderReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "client_name", "rating", "active", "created_at")
    list_filter = ("active", "rating", "created_at")
    search_fields = (
        "body",
        "order__id",
        "order__name",
        "order__phone",
        "order__email",
    )
    readonly_fields = ("created_at", "updated_at", "client_name", "client_phone", "client_email")
    list_editable = ("active",)
    ordering = ("-created_at",)

    @admin.display(description="Имя клиента")
    def client_name(self, obj):
        return obj.client_name

    @admin.display(description="Телефон")
    def client_phone(self, obj):
        return obj.client_phone

    @admin.display(description="Email")
    def client_email(self, obj):
        return obj.client_email


@admin.register(RibbonOption)
class RibbonOptionAdmin(ImportExportModelAdmin):
    list_display = ("id", "opt_type", "news", "css_value", "is_active")
    list_display_links = ("id", "news")
    list_editable = ("is_active",)
    list_filter = ("opt_type", "is_active")
    search_fields = ("news__title", "css_value")
    autocomplete_fields = ("news",)
    fieldsets = (
        (None, {"fields": ("news", "opt_type", "is_active")}),
        ("CSS / Шрифт", {"fields": ("css_value", "font_url")}),
    )


@admin.register(RibbonOrder)
class RibbonOrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "status_badge",   # цветной статус
        "text",
        "ribbon_bg", "font_family", "text_color",
        "color_news", "font_news",
        "foil", "is_group_order", "persons_count",
    )
    list_filter = ("status", "created_at", "is_group_order")
    search_fields = ("text", "name", "phone", "email", "persons_list")
    readonly_fields = ("created_at", "updated_at", "edit_token", "tg_last_synced_at")

    actions = [
        "action_set_in_progress",
        "action_set_wait_approval",
        "action_set_done",
        "action_set_archived",
    ]

    fieldsets = (
        ("Макет", {"fields": (
            "text",
            "ribbon_bg", "font_family", "text_color", "foil",
            "color_news", "font_news",
        )}),
        ("Группа", {"fields": ("is_group_order", "persons_count", "persons_list")}),
        ("Контакты", {"fields": ("name", "phone", "email")}),
        ("Статус", {"fields": ("status", "manager_note", "source")}),
        ("Telegram", {"fields": ("tg_chat_id", "tg_message_id", "tg_thread_root_id", "tg_last_synced_at")}),
    )

    # --- UI: colored status badge ---
    @admin.display(description="Статус", ordering="status")
    def status_badge(self, obj: RibbonOrder):
        label = obj.get_status_display() if hasattr(obj, "get_status_display") else (obj.status or "")

        palette = {
            RibbonOrder.STATUS_NEW: ("#7c3aed", "#ffffff"),           # purple
            RibbonOrder.STATUS_IN_PROGRESS: ("#2563eb", "#ffffff"),   # blue
            RibbonOrder.STATUS_WAIT_APPROVAL: ("#f59e0b", "#111827"), # amber
            RibbonOrder.STATUS_DONE: ("#16a34a", "#ffffff"),          # green
            RibbonOrder.STATUS_ARCHIVED: ("#6b7280", "#ffffff"),      # gray
        }
        bg, fg = palette.get(obj.status, ("#e5e7eb", "#111827"))

        return format_html(
            '<span style="display:inline-block; padding:3px 10px; '
            'border-radius:999px; font-weight:600; font-size:12px; '
            'background:{}; color:{};">{}</span>',
            bg, fg, label
        )

    # --- helpers ---
    def _bulk_set_status(self, request, queryset, status_value: str, label: str):
        updated = queryset.update(status=status_value)
        self.message_user(request, f"{label}: обновлено {updated} заказов", level=messages.SUCCESS)

    # --- actions ---
    @admin.action(description="Статус: В работе")
    def action_set_in_progress(self, request, queryset):
        self._bulk_set_status(request, queryset, RibbonOrder.STATUS_IN_PROGRESS, "В работе")

    @admin.action(description="Статус: Ожидает согласования")
    def action_set_wait_approval(self, request, queryset):
        self._bulk_set_status(request, queryset, RibbonOrder.STATUS_WAIT_APPROVAL, "Ожидает согласования")

    @admin.action(description="Статус: Завершена")
    def action_set_done(self, request, queryset):
        self._bulk_set_status(request, queryset, RibbonOrder.STATUS_DONE, "Завершена")

    @admin.action(description="Статус: Архив")
    def action_set_archived(self, request, queryset):
        self._bulk_set_status(request, queryset, RibbonOrder.STATUS_ARCHIVED, "Архив")


# Настройки интерфейса админки
admin.site.site_title = "Администрирование сайта"
admin.site.site_header = "Администрирование сайта"

# --- Ribbon constructor clean catalog entities ---

from django.contrib import admin as _ribbon_catalog_admin
from .models import RibbonColor, RibbonTextColor, RibbonFont, RibbonTemplate


class RibbonCatalogBaseAdmin(_ribbon_catalog_admin.ModelAdmin):
    list_display = ("title", "slug", "sort_order", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("sort_order", "title")


@_ribbon_catalog_admin.register(RibbonColor)
class RibbonColorAdmin(RibbonCatalogBaseAdmin):
    list_display = ("title", "hex_value", "sort_order", "is_active", "updated_at")
    search_fields = ("title", "slug", "hex_value")


@_ribbon_catalog_admin.register(RibbonTextColor)
class RibbonTextColorAdmin(RibbonCatalogBaseAdmin):
    list_display = ("title", "hex_value", "sort_order", "is_active", "updated_at")
    search_fields = ("title", "slug", "hex_value")


@_ribbon_catalog_admin.register(RibbonFont)
class RibbonFontAdmin(RibbonCatalogBaseAdmin):
    list_display = ("title", "font_family", "sort_order", "is_active", "updated_at")
    search_fields = ("title", "slug", "font_family")


@_ribbon_catalog_admin.register(RibbonTemplate)
class RibbonTemplateAdmin(RibbonCatalogBaseAdmin):
    list_display = ("title", "sort_order", "is_active", "updated_at")
