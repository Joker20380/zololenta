# Generated manually after safe unique-token migration fix.

import uuid

import django.db.models.deletion
import main.models
from django.db import migrations, models


def fill_unique_review_tokens(apps, schema_editor):
    RibbonOrder = apps.get_model("main", "RibbonOrder")
    db_alias = schema_editor.connection.alias

    used = set(
        RibbonOrder.objects.using(db_alias)
        .exclude(review_token__isnull=True)
        .exclude(review_token="")
        .values_list("review_token", flat=True)
    )

    for order in RibbonOrder.objects.using(db_alias).all().only("id", "review_token"):
        if order.review_token:
            continue

        token = uuid.uuid4().hex
        while token in used:
            token = uuid.uuid4().hex

        used.add(token)
        order.review_token = token
        order.save(update_fields=["review_token"])


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0008_fix_ribbonorder_edit_token_default"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="review",
                    name="ribbon_order",
                    field=models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="review",
                        to="main.ribbonorder",
                        verbose_name="Заказ ленты",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="ribbonorder",
            name="review_token",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=64,
                null=True,
                verbose_name="Токен для отзыва",
                help_text="Приватная ссылка для клиента без регистрации.",
            ),
        ),
        migrations.RunPython(fill_unique_review_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="ribbonorder",
            name="review_token",
            field=models.CharField(
                db_index=True,
                default=main.models.generate_edit_token,
                help_text="Приватная ссылка для клиента без регистрации.",
                max_length=64,
                unique=True,
                verbose_name="Токен для отзыва",
            ),
        ),
    ]
