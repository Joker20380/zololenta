from __future__ import annotations

import uuid

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView, TemplateView
from django_admin_geomap import geomap_context

from .forms import (
    ContactRequestForm,
    RibbonOrderForm,
    RibbonOrderReviewForm,
    SubscriberForm,
    UnsubscriberForm,
)
from .models import (
    Contact,
    ContactGroup,
    Documents,
    News,
    RibbonOrder,
    RibbonOrderReview,
    RibbonOption,
    Subscriber,)
from .models import RibbonColor, RibbonTextColor, RibbonFont, RibbonTemplate
from .utils import DataMixin


class Index(DataMixin, ListView):
    queryset = News.objects.order_by("-time_update")
    model = News
    template_name = "zololenta/index.html"
    context_object_name = "news"
    paginate_by = 6

    @staticmethod
    def news_examples():
        return News.objects.filter(cat_id=2).order_by("-time_update")

    @staticmethod
    def news_colors():
        return News.objects.filter(cat_id=3).order_by("-time_update")

    @staticmethod
    def news_fonts():
        return News.objects.filter(cat_id=4).order_by("-time_update")

    @staticmethod
    def news_blog():
        return News.objects.filter(cat_id=5).order_by("-time_update")

    @staticmethod
    def news_package():
        return News.objects.filter(cat_id=6).order_by("-time_update")


class ShowNews(DataMixin, DetailView):
    paginate_by = 1
    model = News
    template_name = "zololenta/news-view.html"
    slug_url_kwarg = "news_slug"
    context_object_name = "news"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title=context["news"])
        return dict(list(context.items()) + list(c_def.items()))

    @staticmethod
    def post_last3():
        return News.objects.reverse()[:3]

    @staticmethod
    def post_last6():
        return News.objects.reverse()[:6]


class Blog(DataMixin, ListView):
    queryset = (
        News.objects
        .filter(cat_id=5, is_published=True)
        .select_related("cat")
        .order_by("-time_update")
    )
    template_name = "zololenta/blog.html"
    model = News
    context_object_name = "news"
    paginate_by = 9

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Новости")
        return dict(list(context.items()) + list(c_def.items()))


class RibbonConstructorView(TemplateView):
    template_name = "zololenta/ribbon_constructor.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["form"] = kwargs.get("form") or RibbonOrderForm()

        ctx["ribbon_colors"] = (
            RibbonColor.objects
            .filter(is_active=True)
            .order_by("sort_order", "title")
        )

        ctx["ribbon_text_colors"] = (
            RibbonTextColor.objects
            .filter(is_active=True)
            .order_by("sort_order", "title")
        )

        ctx["ribbon_fonts"] = (
            RibbonFont.objects
            .filter(is_active=True)
            .order_by("sort_order", "title")
        )

        ctx["ribbon_templates"] = (
            RibbonTemplate.objects
            .filter(is_active=True)
            .order_by("sort_order", "title")
        )

        return ctx

    def post(self, request, *args, **kwargs):
        form = RibbonOrderForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Заявка принята. Мы свяжемся с вами для подтверждения макета.")
            return redirect("ribbon_constructor")
        return self.render_to_response(self.get_context_data(form=form))



def ribbon_order_review(request, token):
    order = get_object_or_404(RibbonOrder, review_token=token)

    try:
        existing_review = order.order_review
    except RibbonOrderReview.DoesNotExist:
        existing_review = None

    if existing_review is not None:
        return render(
            request,
            "zololenta/ribbon_order_review.html",
            {
                "order": order,
                "form": None,
                "already_submitted": True,
                "review": existing_review,
            },
        )

    if request.method == "POST":
        form = RibbonOrderReviewForm(request.POST, request.FILES)

        if form.is_valid():
            review = form.save(commit=False)
            review.order = order
            review.active = False
            review.save()

            return render(
                request,
                "zololenta/ribbon_order_review.html",
                {
                    "order": order,
                    "form": None,
                    "submitted": True,
                    "review": review,
                },
            )
    else:
        form = RibbonOrderReviewForm()

    return render(
        request,
        "zololenta/ribbon_order_review.html",
        {
            "order": order,
            "form": form,
            "submitted": False,
            "already_submitted": False,
        },
    )


class Confidential_information(DataMixin, ListView):
    model = Documents
    template_name = "zololenta/confidential_information.html"
    context_object_name = "news"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Политика конфиденциальности")
        return dict(list(context.items()) + list(c_def.items()))

    @staticmethod
    def post_last3():
        return News.objects.reverse()[:3]

    @staticmethod
    def news_all_conf():
        return News.objects.filter(title="Политика конфиденциальности")


def Subscribe(request):
    if request.method != "POST":
        # GET-запрос — показать форму (если ты реально используешь этот рендер)
        form = SubscriberForm()
        return render(request, "zololenta/index.html", {"form": form})

    email = (request.POST.get("email") or "").strip()

    if Subscriber.objects.filter(email__iexact=email).exists():
        messages.info(request, "Этот e-mail уже подписан на рассылку.")
        return redirect("index")

    form = SubscriberForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Вы успешно подписались на рассылку!")
    else:
        messages.error(request, "Проверьте форму: есть ошибки.")
    return redirect("index")


def Unsubscribe(request):
    if request.method == "POST":
        form = UnsubscriberForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            try:
                subscriber = Subscriber.objects.get(email=email, is_active=True)
                subscriber.unsubscribe_token = uuid.uuid4().hex
                subscriber.save()

                unsubscribe_url = request.build_absolute_uri(
                    f"/unsubscribe/confirm/{subscriber.unsubscribe_token}/"
                )

                send_mail(
                    "Подтверждение отписки",
                    f"Для подтверждения отписки перейдите по ссылке: {unsubscribe_url}",
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                messages.success(request, "На ваш email отправлено письмо с подтверждением отписки.")
            except Subscriber.DoesNotExist:
                messages.error(request, "Подписка с таким email не найдена.")
            return redirect("unsubscribe_request")
    else:
        form = UnsubscriberForm()

    return render(request, "zololenta/unsubscribe_form.html", {"form": form})


def Unsubscribe_confirm(request, token):
    subscriber = get_object_or_404(Subscriber, unsubscribe_token=token, is_active=True)
    subscriber.is_active = False
    subscriber.unsubscribe_token = None
    subscriber.save()
    messages.success(request, "Вы успешно отписались от рассылки.")
    return render(request, "zololenta/unsubscribe_success.html")


class ContactsView(TemplateView):
    template_name = "zololenta/contacts.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        contacts = list(
            Contact.objects
            .select_related("location", "group")
            .order_by("order", "id")
        )

        main_contact = next(
            (contact for contact in contacts if contact.is_main),
            contacts[0] if contacts else None,
        )

        map_locations = []
        used_location_ids = set()

        for contact in contacts:
            location = contact.location

            if (
                location is None
                or location.lat is None
                or location.lon is None
                or location.pk in used_location_ids
            ):
                continue

            used_location_ids.add(location.pk)
            map_locations.append(location)

        ctx["main_contact"] = main_contact
        ctx["contact_groups"] = (
            ContactGroup.objects
            .prefetch_related("contacts__location")
            .all()
        )
        ctx["show_contact_directory"] = len(contacts) > 1
        ctx["map_locations"] = map_locations
        ctx["form"] = kwargs.get("form") or ContactRequestForm()

        center_latitude = "43.0367"
        center_longitude = "44.6818"

        if (
            main_contact
            and main_contact.location
            and main_contact.location.lat is not None
            and main_contact.location.lon is not None
        ):
            center_latitude = f"{main_contact.location.lat:.6f}"
            center_longitude = f"{main_contact.location.lon:.6f}"

            ctx["location_lat"] = center_latitude
            ctx["location_lon"] = center_longitude
            ctx["location_name"] = main_contact.name

        ctx.update(
            geomap_context(
                map_locations,
                map_longitude=center_longitude,
                map_latitude=center_latitude,
                map_zoom="15",
                auto_zoom="16",
                map_height="520px",
            )
        )

        return ctx

    def post(self, request, *args, **kwargs):
        form = ContactRequestForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Пожалуйста, заполните обязательные поля корректно.")
            return self.get(request, form=form, *args, **kwargs)

        form.save()
        messages.success(request, "Ваше сообщение успешно отправлено!")
        return redirect("contacts")
