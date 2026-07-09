from decimal import Decimal
from datetime import date, time, timedelta
import tempfile
import uuid

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.test import TestCase, override_settings
from django.utils import timezone

from main.models import RibbonOrder, RibbonOrderReview


def first_choice(field):
    for value, label in field.choices:
        if isinstance(label, (list, tuple)):
            return label[0][0]
        return value
    return None


def has_auto_value(field):
    return (
        field.has_default()
        or getattr(field, "auto_now", False)
        or getattr(field, "auto_now_add", False)
    )


def value_for_field(field, seen_models=None):
    seen_models = seen_models or set()

    if field.choices:
        return first_choice(field)

    if isinstance(field, models.ForeignKey):
        related_model = field.remote_field.model
        if related_model in seen_models:
            raise AssertionError(f"Cannot auto-create recursive FK for field {field.name}")
        return create_required_instance(related_model, seen_models | {related_model})

    if isinstance(field, models.EmailField):
        return "client@example.com"

    if isinstance(field, models.URLField):
        return "https://example.com"

    if isinstance(field, (models.CharField, models.SlugField, models.TextField)):
        if "phone" in field.name.lower():
            return "+79990000000"
        if "email" in field.name.lower():
            return "client@example.com"
        if "token" in field.name.lower():
            return f"test-token-{uuid.uuid4().hex[:12]}"
        return "test"

    if isinstance(field, models.BooleanField):
        return False

    if isinstance(field, (models.IntegerField, models.PositiveIntegerField, models.PositiveSmallIntegerField)):
        return 1

    if isinstance(field, models.DecimalField):
        return Decimal("1")

    if isinstance(field, models.FloatField):
        return 1.0

    if isinstance(field, models.DateTimeField):
        return timezone.now()

    if isinstance(field, models.DateField):
        return date.today()

    if isinstance(field, models.TimeField):
        return time(12, 0)

    if isinstance(field, models.DurationField):
        return timedelta(minutes=1)

    if isinstance(field, models.UUIDField):
        return uuid.uuid4()

    if isinstance(field, models.JSONField):
        return {}

    if isinstance(field, models.FileField):
        return SimpleUploadedFile("test.txt", b"test", content_type="text/plain")

    raise AssertionError(f"Unsupported required field: {field.name} ({field.__class__.__name__})")


def create_required_instance(model_class, seen_models=None, **overrides):
    seen_models = seen_models or {model_class}
    kwargs = {}

    for field in model_class._meta.concrete_fields:
        if field.primary_key:
            continue
        if field.name in overrides:
            continue
        if field.null or field.blank or has_auto_value(field):
            continue

        kwargs[field.name] = value_for_field(field, seen_models)

    kwargs.update(overrides)
    return model_class.objects.create(**kwargs)


@override_settings(
    ALLOWED_HOSTS=["testserver"],
    SECURE_SSL_REDIRECT=False,
    MEDIA_ROOT=tempfile.mkdtemp(prefix="zololenta-test-media-"),
)
class RibbonOrderReviewFlowTests(TestCase):
    def make_order(self):
        return create_required_instance(
            RibbonOrder,
            review_token=f"review-token-{uuid.uuid4().hex[:12]}",
        )

    def test_order_review_page_get_returns_200(self):
        order = self.make_order()

        response = self.client.get(f"/review/order/{order.review_token}/")

        self.assertEqual(response.status_code, 200)

    def test_order_review_page_post_creates_review(self):
        order = self.make_order()

        response = self.client.post(
            f"/review/order/{order.review_token}/",
            {
                "rating": "5",
                "body": "Тестовый отзыв по заказу ленты.",
            },
        )

        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(
            RibbonOrderReview.objects.filter(order=order, rating=5).exists()
        )
