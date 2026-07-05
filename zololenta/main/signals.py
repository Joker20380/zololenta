from django.db.models.signals import post_save
from django.dispatch import receiver

from main.models import RibbonOrder
from main.tg_service import sync_order_to_tg


TG_ONLY_UPDATE_FIELDS = {
    "tg_chat_id",
    "tg_message_id",
    "tg_thread_root_id",
    "tg_last_synced_at",
    "tg_lock_until",
    "updated_at",
}


@receiver(post_save, sender=RibbonOrder)
def ribbon_order_post_save(sender, instance: RibbonOrder, created: bool, update_fields=None, **kwargs):
    """
    Единственная точка Telegram-sync.

    Важно: tg_service внутри делает order.save(update_fields=[...tg_*...]),
    это тоже вызывает post_save. Чтобы не было дублей/циклов:
    - игнорируем сохранения, где менялись только tg_* поля и updated_at.
    """
    if update_fields:
        uf = set(update_fields)
        if uf.issubset(TG_ONLY_UPDATE_FIELDS):
            return

    sync_order_to_tg(instance)
