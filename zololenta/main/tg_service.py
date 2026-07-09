import requests
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.urls import reverse


# --- MarkdownV2 escaping ---
MDV2_SPECIAL = r"_*[]()~`>#+-=|{}.!\\"

def mdv2_escape(text) -> str:
    if text is None:
        return ""
    s = str(text)
    out = []
    for ch in s:
        if ch in MDV2_SPECIAL:
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


class TelegramRateLimitError(Exception):
    def __init__(self, retry_after: int = 3, payload=None):
        super().__init__(f"Telegram rate limit: retry_after={retry_after}")
        self.retry_after = int(retry_after or 3)
        self.payload = payload or {}


def tg_call(method: str, payload: dict):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/{method}"
    timeout = getattr(settings, "TELEGRAM_API_TIMEOUT", 10)

    r = requests.post(url, json=payload, timeout=timeout)

    if r.status_code == 429:
        try:
            data = r.json()
        except Exception:
            data = {}
        retry_after = int(data.get("parameters", {}).get("retry_after", 3))
        raise TelegramRateLimitError(retry_after=retry_after, payload=data)

    r.raise_for_status()
    data = r.json()
    if not data.get("ok", False):
        raise RuntimeError(f"Telegram API error: {data}")
    return data


def _set_lock(order, seconds: int):
    order.tg_lock_until = timezone.now() + timedelta(seconds=int(seconds))
    order.save(update_fields=["tg_lock_until"])


def _should_throttle(order) -> bool:
    throttle_sec = int(getattr(settings, "TELEGRAM_THROTTLE_SECONDS", 10))
    if throttle_sec <= 0:
        return False
    if order.tg_last_synced_at:
        delta = (timezone.now() - order.tg_last_synced_at).total_seconds()
        return delta < throttle_sec
    return False


def _send_message(chat_id: int, text: str, message_thread_id: int | None = None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": getattr(settings, "TELEGRAM_PARSE_MODE", "MarkdownV2"),
        "disable_web_page_preview": True,
    }
    if message_thread_id:
        payload["message_thread_id"] = int(message_thread_id)
    return tg_call("sendMessage", payload)


def _edit_message(chat_id: int, message_id: int, text: str):
    payload = {
        "chat_id": chat_id,
        "message_id": int(message_id),
        "text": text,
        "parse_mode": getattr(settings, "TELEGRAM_PARSE_MODE", "MarkdownV2"),
        "disable_web_page_preview": True,
    }
    return tg_call("editMessageText", payload)


def _create_topic(chat_id: int, name: str) -> int:
    res = tg_call("createForumTopic", {
        "chat_id": chat_id,
        "name": name[:128],
    })
    return int(res["result"]["message_thread_id"])


def _topic_title(order) -> str:
    status = order.get_status_display()
    contact = (order.name or order.phone or order.email or "без контакта").strip()
    return f"{status} • {contact} • {str(order.id)[:8]}"


# ===== helpers for NEW model =====

def _safe_hex(v: str, default: str) -> str:
    v = (v or "").strip()
    if len(v) == 7 and v.startswith("#"):
        return v.upper()
    return default.upper()


def _human_color_value(title: str, hexv: str = "") -> str:
    """
    Telegram is a business-facing channel.

    Store HEX in the order for technical snapshots, but show only
    human-readable catalog names in manager notifications.
    """
    title = (title or "").strip()
    return title or "Не указан"


def _catalog_color_label(hexv: str) -> str:
    """
    Resolve ribbon color HEX through the clean RibbonColor catalog first.

    Fallback to legacy RibbonOption only for old orders.
    Never expose HEX in Telegram.
    """
    hexv = _safe_hex(hexv, "#E9E5D3")

    try:
        from main.models import RibbonColor, RibbonOption
    except Exception:
        return "Не указан"

    color = (
        RibbonColor.objects
        .filter(is_active=True, hex_value__iexact=hexv)
        .order_by("sort_order", "title")
        .first()
    )

    if color:
        return _human_color_value(color.title)

    option = (
        RibbonOption.objects
        .filter(
            opt_type=RibbonOption.TYPE_COLOR,
            is_active=True,
            news__cat_id=3,
            css_value__iexact=hexv,
        )
        .select_related("news")
        .order_by("-news__time_update", "id")
        .first()
    )

    if option and option.news_id:
        return _human_color_value(option.news.title)

    return "Не указан"


TEXT_COLOR_LABELS = {
    "#FFFFFF": "Белый",
    "#111827": "Чёрный",
    "#000000": "Чёрный",
    "#FFD36A": "Золото",
    "#D4AF37": "Золото",
    "#D1D5DB": "Серебро",
    "#C0C0C0": "Серебро",
    "#7A1430": "Бордовый",
}


def _order_ribbon_color_label(order) -> str:
    color = getattr(order, "ribbon_color", None)
    if color and getattr(color, "title", ""):
        return _human_color_value(color.title)

    hexv = _safe_hex(getattr(order, "ribbon_bg", ""), "#E9E5D3")

    catalog_label = _catalog_color_label(hexv)
    if catalog_label != "Не указан":
        return catalog_label

    color_obj = getattr(order, "color_news", None)
    if color_obj is not None:
        title = getattr(color_obj, "title", None)
        if title:
            return _human_color_value(title)

    return "Не указан"


def _text_color_label(hexv: str) -> str:
    hexv = _safe_hex(hexv, "#FFFFFF")
    return _human_color_value(TEXT_COLOR_LABELS.get(hexv, ""))


def _order_text_color_label(order) -> str:
    color = getattr(order, "ribbon_text_color", None)
    if color and getattr(color, "title", ""):
        return _human_color_value(color.title)

    return _text_color_label(getattr(order, "text_color", ""))


def _order_font_label(order) -> str:
    font = getattr(order, "ribbon_font", None)
    if font and getattr(font, "title", ""):
        return font.title

    font_obj = getattr(order, "font_news", None)
    legacy_title = getattr(font_obj, "title", None) if font_obj is not None else None
    if legacy_title:
        return legacy_title

    ff = (getattr(order, "font_family", "") or "").strip()
    if ff:
        return ff.replace("'", "").replace('"', "").split(",")[0].strip() or "—"

    return "—"


def _order_review_url(order) -> str:
    token = (getattr(order, "review_token", "") or "").strip()
    if not token:
        return "—"

    path = reverse("ribbon_order_review", args=[token])
    base = (
        getattr(settings, "SITE_URL", "")
        or getattr(settings, "SITE_BASE_URL", "")
        or getattr(settings, "PUBLIC_SITE_URL", "")
        or ""
    ).rstrip("/")

    if base:
        return f"{base}{path}"

    return path


# ===== formatter =====

def format_order(order) -> str:
    persons_raw = ""
    if hasattr(order, "persons_lines") and callable(order.persons_lines):
        persons_raw = "\n".join(order.persons_lines())
    persons_raw = (persons_raw or "").strip()
    persons = persons_raw if persons_raw else "—"

    ribbon_color = _order_ribbon_color_label(order)
    font_label = _order_font_label(order)
    text_color = _order_text_color_label(order)
    review_url = _order_review_url(order)

    return (
        "🎓 *Заявка на ленты*\n\n"
        f"*ID:* `{mdv2_escape(order.id)}`\n"
        f"*Статус:* {mdv2_escape(order.get_status_display())}\n\n"
        f"*Текст:* {mdv2_escape(order.text)}\n"
        f"*Цвет ленты:* {mdv2_escape(ribbon_color)}\n"
        f"*Шрифт:* {mdv2_escape(font_label)}\n"
        f"*Цвет текста:* {mdv2_escape(text_color)}\n"
        f"*Фольга:* {mdv2_escape(order.get_foil_display())}\n\n"
        f"*Кол\\-во:* {mdv2_escape(order.persons_count)}\n"
        f"*Список ФИО:*\n{mdv2_escape(persons)}\n\n"
        f"*Комментарий:* {mdv2_escape(order.comment or '—')}\n\n"
        f"*Контакт:* {mdv2_escape(order.name or '—')}\n"
        f"*Телефон:* {mdv2_escape(order.phone or '—')}\n"
        f"*Email:* {mdv2_escape(order.email or '—')}\n"
        f"*Ссылка на отзыв:* {mdv2_escape(review_url)}\n"
    )


# ===== sync =====

def sync_order_to_tg(order):
    if not getattr(settings, "TELEGRAM_ENABLED", False):
        return
    if not order.can_tg_sync():
        return
    if _should_throttle(order):
        return

    chat_id = int(getattr(settings, "TELEGRAM_ORDERS_CHAT_ID", 0) or 0)
    if not chat_id:
        return

    text = format_order(order)

    try:
        if getattr(settings, "TELEGRAM_USE_TOPICS", True):
            if not order.tg_thread_root_id:
                title = _topic_title(order)
                thread_id = _create_topic(chat_id, title)
                order.tg_chat_id = chat_id
                order.tg_thread_root_id = thread_id
                order.save(update_fields=["tg_chat_id", "tg_thread_root_id"])

            if order.tg_message_id:
                try:
                    _edit_message(chat_id, order.tg_message_id, text)
                except Exception:
                    res = _send_message(chat_id, text, message_thread_id=order.tg_thread_root_id)
                    order.tg_message_id = int(res["result"]["message_id"])
            else:
                res = _send_message(chat_id, text, message_thread_id=order.tg_thread_root_id)
                order.tg_message_id = int(res["result"]["message_id"])

        else:
            if order.tg_message_id:
                try:
                    _edit_message(chat_id, order.tg_message_id, text)
                except Exception:
                    res = _send_message(chat_id, text)
                    order.tg_message_id = int(res["result"]["message_id"])
            else:
                res = _send_message(chat_id, text)
                order.tg_message_id = int(res["result"]["message_id"])
            order.tg_chat_id = chat_id

        order.tg_last_synced_at = timezone.now()
        order.save(update_fields=["tg_message_id", "tg_chat_id", "tg_last_synced_at"])

    except TelegramRateLimitError as e:
        _set_lock(order, max(10, e.retry_after))
        return
    except Exception:
        return
