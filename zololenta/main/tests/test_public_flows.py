from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.core import mail
from django.db import IntegrityError

from main.models import Subscriber, ContactGroup, Contact, ContactRequest
from users.models import Location


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="no-reply@example.com",
)
class SubscribeFlowTests(TestCase):
    def test_subscribe_post_new_email_creates_subscriber_and_redirects_to_index(self):
        url = reverse("subscribe")
        resp = self.client.post(url, data={"email": "Test@Example.com"}, follow=True)

        self.assertEqual(resp.status_code, 200)
        # email должен храниться нормализованным (form.clean_email + model.save)
        self.assertTrue(Subscriber.objects.filter(email="test@example.com").exists())
        self.assertEqual(resp.request["PATH_INFO"], reverse("index"))

        msgs = list(resp.context["messages"])
        self.assertTrue(any("успеш" in str(m).lower() and "подпис" in str(m).lower() for m in msgs))

    def test_subscribe_post_existing_email_case_insensitive_no_duplicate(self):
        Subscriber.objects.create(email="test@example.com", is_active=True)

        url = reverse("subscribe")
        resp = self.client.post(url, data={"email": "TEST@EXAMPLE.COM"}, follow=True)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Subscriber.objects.filter(email="test@example.com").count(), 1)
        self.assertEqual(resp.request["PATH_INFO"], reverse("index"))

        msgs = list(resp.context["messages"])
        self.assertTrue(any("уже подписан" in str(m).lower() for m in msgs))

    def test_subscribe_post_invalid_email_shows_error(self):
        url = reverse("subscribe")
        resp = self.client.post(url, data={"email": "not-an-email"}, follow=True)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Subscriber.objects.count(), 0)
        self.assertEqual(resp.request["PATH_INFO"], reverse("index"))

        msgs = list(resp.context["messages"])
        self.assertTrue(any("ошиб" in str(m).lower() or "проверьте" in str(m).lower() for m in msgs))

    def test_subscribe_handles_integrityerror_race_condition(self):
        """
        Эмуляция гонки: в момент создания словили IntegrityError.
        Требование: никаких 500, получаем корректный UX (как минимум info).
        """
        url = reverse("subscribe")

        with patch("main.views.Subscriber.objects.get_or_create", side_effect=IntegrityError):
            resp = self.client.post(url, data={"email": "race@example.com"}, follow=True)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.request["PATH_INFO"], reverse("index"))

        msgs = list(resp.context["messages"])
        self.assertTrue(any("уже подписан" in str(m).lower() or "подпис" in str(m).lower() for m in msgs))


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="no-reply@example.com",
)
class UnsubscribeFlowTests(TestCase):
    def test_unsubscribe_get_returns_200(self):
        url = reverse("unsubscribe_request")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_unsubscribe_post_existing_active_sets_token_and_sends_email(self):
        s = Subscriber.objects.create(email="sub@example.com", is_active=True)

        url = reverse("unsubscribe_request")
        resp = self.client.post(url, data={"email": "sub@example.com"}, follow=True)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.request["PATH_INFO"], reverse("unsubscribe_request"))

        s.refresh_from_db()
        self.assertTrue(s.unsubscribe_token)

        self.assertEqual(len(mail.outbox), 1)
        out = mail.outbox[0]
        self.assertIn("подтверждение", out.subject.lower())
        self.assertIn(s.unsubscribe_token, out.body)

        msgs = list(resp.context["messages"])
        self.assertTrue(any("письмо" in str(m).lower() and "подтвержден" in str(m).lower() for m in msgs))

    def test_unsubscribe_post_missing_email_shows_error(self):
        url = reverse("unsubscribe_request")
        resp = self.client.post(url, data={"email": "missing@example.com"}, follow=True)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.request["PATH_INFO"], reverse("unsubscribe_request"))
        self.assertEqual(len(mail.outbox), 0)

        msgs = list(resp.context["messages"])
        self.assertTrue(any("не найдена" in str(m).lower() for m in msgs))

    def test_unsubscribe_confirm_deactivates_and_clears_token(self):
        s = Subscriber.objects.create(email="sub@example.com", is_active=True, unsubscribe_token="tok123")

        url = reverse("unsubscribe_confirm", kwargs={"token": "tok123"})
        resp = self.client.get(url, follow=True)

        self.assertEqual(resp.status_code, 200)

        s.refresh_from_db()
        self.assertFalse(s.is_active)
        self.assertIsNone(s.unsubscribe_token)

        msgs = list(resp.context["messages"])
        self.assertTrue(any("успешно" in str(m).lower() and "отпис" in str(m).lower() for m in msgs))

    def test_unsubscribe_confirm_invalid_token_404(self):
        url = reverse("unsubscribe_confirm", kwargs={"token": "bad"})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_unsubscribe_confirm_token_cannot_be_reused(self):
        """
        Важный бизнес-контроль: после подтверждения токен очищается,
        второй заход по тому же URL должен быть 404.
        """
        s = Subscriber.objects.create(email="sub@example.com", is_active=True, unsubscribe_token="tok_reuse")

        url = reverse("unsubscribe_confirm", kwargs={"token": "tok_reuse"})
        first = self.client.get(url)
        self.assertEqual(first.status_code, 200)

        s.refresh_from_db()
        self.assertIsNone(s.unsubscribe_token)
        self.assertFalse(s.is_active)

        second = self.client.get(url)
        self.assertEqual(second.status_code, 404)


class ContactsViewTests(TestCase):
    def test_contacts_get_context_has_main_contact_groups_and_coords(self):
        loc = Location.objects.create(name="Gent", lat=51.054342, lon=3.717424)
        group = ContactGroup.objects.create(name="Администрация", order=0)
        main = Contact.objects.create(
            group=group,
            name="Главный",
            is_main=True,
            location=loc,
            order=0,
        )

        url = reverse("contacts")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("main_contact", resp.context)
        self.assertIn("contact_groups", resp.context)

        self.assertEqual(resp.context["main_contact"].id, main.id)
        self.assertEqual(resp.context["location_name"], main.name)
        self.assertEqual(resp.context["location_lat"], "51.054342")
        self.assertEqual(resp.context["location_lon"], "3.717424")

    def test_contacts_get_no_main_contact_is_ok(self):
        """
        На будущее: если main_contact отсутствует, view не должен падать.
        """
        url = reverse("contacts")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("main_contact", resp.context)
        self.assertIsNone(resp.context["main_contact"])

    def test_contacts_post_missing_required_fields_shows_error_and_no_request_created(self):
        url = reverse("contacts")
        resp = self.client.post(url, data={"name": "", "email": "", "message": ""}, follow=True)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.request["PATH_INFO"], reverse("contacts"))
        self.assertEqual(ContactRequest.objects.count(), 0)

        msgs = list(resp.context["messages"])
        self.assertTrue(any("заполните" in str(m).lower() or "обязатель" in str(m).lower() for m in msgs))

    def test_contacts_post_invalid_contact_id_creates_request_with_contact_none(self):
        url = reverse("contacts")
        resp = self.client.post(
            url,
            data={"name": "John", "email": "john@example.com", "message": "Hello", "contact": "999999"},
            follow=True,
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.request["PATH_INFO"], reverse("contacts"))
        self.assertEqual(ContactRequest.objects.count(), 1)

        cr = ContactRequest.objects.first()
        self.assertIsNone(cr.contact)

    def test_contacts_post_valid_creates_contact_request_and_redirects(self):
        group = ContactGroup.objects.create(name="Администрация", order=0)
        contact = Contact.objects.create(group=group, name="Менеджер", is_main=True, order=0)

        url = reverse("contacts")
        resp = self.client.post(
            url,
            data={
                "name": "John",
                "email": "john@example.com",
                "phone": "+321234567",
                "message": "Hello",
                "contact": str(contact.id),
            },
            follow=True,
        )

        self.assertEqual(resp.status_code, 200)
        # по твоей логике: redirect('contacts') -> снова contacts
        self.assertEqual(resp.request["PATH_INFO"], reverse("contacts"))
        self.assertEqual(ContactRequest.objects.count(), 1)

        cr = ContactRequest.objects.first()
        self.assertEqual(cr.email, "john@example.com")
        self.assertEqual(cr.contact_id, contact.id)

        msgs = list(resp.context["messages"])
        self.assertTrue(any("успешно" in str(m).lower() and "отправ" in str(m).lower() for m in msgs))
