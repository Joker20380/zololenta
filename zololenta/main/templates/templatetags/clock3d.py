from django import template
import uuid

register = template.Library()

@register.inclusion_tag('clock3d/widget.html')
def clock3d(size=360, dark=False, class_name=''):
    """
    Вставка 3D-часов.
    :param size: размер в px (число) — ширина и высота, авто-адаптивно в контейнере
    :param dark: True/False — тёмная тема
    :param class_name: дополнительные CSS-классы для внешней обёртки
    """
    # уникальный id, если на странице несколько виджетов
    wid = f"clock3d_{uuid.uuid4().hex[:8]}"
    return {
        "wid": wid,
        "size": int(size),
        "dark": bool(dark),
        "class_name": class_name,
    }