from __future__ import annotations

from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from django.urls import reverse

from dal import autocomplete
from allauth.account.forms import LoginForm, ResetPasswordForm
from phonenumber_field.formfields import PhoneNumberField as PhoneNumberFormField

from users.models import UserProfile
from .models import (
    Subscriber,
    RibbonOrder,
    RibbonOption,
    Contact,
    ContactRequest,
)


# ============================================================
# Allauth кастомизация
# ============================================================

class CustomResetPasswordForm(ResetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update({
            "class": "newsletter_input",
            "placeholder": "Введите ваш email",
            "autocomplete": "email",
        })


class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in ["login", "password"]:
                field.widget.attrs.update({"class": "newsletter_input"})


# ============================================================
# Профиль пользователя
# ============================================================

class UserProfileForm(forms.ModelForm):
    last_name = forms.CharField(
        max_length=30,
        required=False,
        label="Фамилия",
        widget=forms.TextInput(attrs={"placeholder": "Фамилия", "class": "newsletter_input"}),
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        label="Имя",
        widget=forms.TextInput(attrs={"placeholder": "Имя", "class": "newsletter_input"}),
    )
    patronymic = forms.CharField(
        max_length=30,
        required=False,
        label="Отчество",
        widget=forms.TextInput(attrs={"placeholder": "Отчество", "class": "newsletter_input"}),
    )
    address = forms.CharField(
        max_length=30,
        required=False,
        label="Адрес",
        widget=forms.TextInput(attrs={"placeholder": "Адрес", "class": "newsletter_input"}),
    )
    phone_number = PhoneNumberFormField(
        region="RU",
        label="Номер телефона",
        widget=forms.TextInput(attrs={"placeholder": "Номер телефона", "class": "newsletter_input"}),
        required=False,  # сделай True, если это обязательное поле
    )

    class Meta:
        model = UserProfile
        fields = ["last_name", "first_name", "patronymic", "gender", "address", "phone_number"]


class SchoolSelect2Widget(autocomplete.ModelSelect2):
    search_fields = ["title__icontains", "location__name__icontains"]

    def get_url(self):
        return reverse("school-autocomplete")


class PersonalAreaForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": "Username",
            "autocomplete": "username",
            "class": "newsletter_input",
        }),
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            "placeholder": "Email",
            "autocomplete": "email",
            "class": "newsletter_input",
        }),
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        label="Фамилия",
        widget=forms.TextInput(attrs={"placeholder": "Фамилия", "class": "newsletter_input"}),
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        label="Имя",
        widget=forms.TextInput(attrs={"placeholder": "Имя", "class": "newsletter_input"}),
    )
    patronymic = forms.CharField(
        max_length=30,
        required=False,
        label="Отчество",
        widget=forms.TextInput(attrs={"placeholder": "Отчество", "class": "newsletter_input"}),
    )
    address = forms.CharField(
        max_length=30,
        required=False,
        label="Адрес",
        widget=forms.TextInput(attrs={"placeholder": "Адрес", "class": "newsletter_input"}),
    )
    phone_number = PhoneNumberFormField(
        region="RU",
        label="Номер телефона",
        widget=forms.TextInput(attrs={"placeholder": "Номер телефона", "class": "newsletter_input"}),
        required=False,
    )
    merit = forms.CharField(
        max_length=500,
        required=False,
        label="О себе",
        widget=forms.Textarea(attrs={"placeholder": "О себе", "class": "newsletter_input", "rows": 3}),
    )

    class Meta:
        model = UserProfile
        fields = [
            "image",
            "username",
            "email",
            "last_name",
            "first_name",
            "patronymic",
            "address",
            "phone_number",
            "birth",
            "merit",
            # Если у UserProfile есть поле school — добавь сюда:
            # "school",
        ]
        widgets = {
            "birth": AdminDateWidget(attrs={"type": "text", "class": "newsletter_input datepicker"}),
            # Если у UserProfile есть поле school — раскомментируй:
            # "school": autocomplete.ModelSelect2(url="school-autocomplete"),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.user = user

        self.fields["username"].initial = user.username
        self.fields["email"].initial = user.email
        self.fields["first_name"].initial = user.first_name
        self.fields["last_name"].initial = user.last_name

        self.fields["patronymic"].initial = getattr(user.userprofile, "patronymic", "")
        self.fields["address"].initial = getattr(user.userprofile, "address", "")
        self.fields["phone_number"].initial = getattr(user.userprofile, "phone_number", "")
        self.fields["birth"].initial = getattr(user.userprofile, "birth", "")
        self.fields["merit"].initial = getattr(user.userprofile, "merit", "")
        self.fields["image"].initial = getattr(user.userprofile, "image", None)

        # Если поле school есть:
        # self.fields["school"].initial = getattr(user.userprofile, "school", None)

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image:
            max_size_mb = 5
            if image.size > max_size_mb * 1024 * 1024:
                raise forms.ValidationError(f"Размер изображения не должен превышать {max_size_mb} МБ.")
        return image

    def save(self, commit=True):
        user_profile = super().save(commit=False)

        user = self.user
        user.username = self.cleaned_data.get("username", user.username)
        user.email = self.cleaned_data.get("email", user.email)
        user.first_name = self.cleaned_data.get("first_name", user.first_name)
        user.last_name = self.cleaned_data.get("last_name", user.last_name)

        if commit:
            user.save()
            user_profile.save()
            self.save_m2m()

        return user_profile


# ============================================================
# Подписки
# ============================================================

class SubscriberForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ["email"]
        widgets = {
            "email": forms.EmailInput(attrs={
                "placeholder": "Введите ваш email",
                "autocomplete": "email",
                "class": "form-control",
            })
        }

    def clean_email(self):
        return (self.cleaned_data.get("email") or "").strip().lower()


class UnsubscriberForm(forms.Form):
    email = forms.EmailField(
        label="Ваш email",
        widget=forms.EmailInput(attrs={
            "placeholder": "Введите ваш email",
            "autocomplete": "email",
            "class": "newsletter_input",
        }),
    )


# ============================================================
# Конструктор лент
# ============================================================

class RibbonOrderForm(forms.ModelForm):
    """
    Важно:
    - ribbon_bg и font_family приходят скрытыми полями из UI-каталога.
    - Валидируем строго по RibbonOption, привязанным к News нужной категории.
    """

    class Meta:
        model = RibbonOrder
        fields = [
            "text",
            "ribbon_bg",
            "font_family",
            "text_color",
            "is_group_order",
            "persons_count",
            "persons_list",
            "comment",
            "name",
            "phone",
            "email",
        ]
        widgets = {
            "text": forms.TextInput(attrs={"class": "form-control"}),

            "ribbon_bg": forms.HiddenInput(),
            "font_family": forms.HiddenInput(),
            "text_color": forms.HiddenInput(),

            "persons_list": forms.Textarea(attrs={"rows": 5, "class": "form-control"}),
            "comment": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ribbon_bg"].initial = "#1E4ED8"
        self.fields["text_color"].initial = "#FFFFFF"
        self.fields["font_family"].initial = "'Montserrat', sans-serif"

        self.fields["text"].widget.attrs.update({
            "placeholder": "Например: Выпускник 2026 · 11-А класс",
            "autocomplete": "off",
        })
        self.fields["name"].widget.attrs.update({
            "placeholder": "Как к вам обращаться",
            "autocomplete": "name",
        })
        self.fields["phone"].widget.attrs.update({
            "placeholder": "+7 999 000-00-00",
            "autocomplete": "tel",
        })
        self.fields["email"].widget.attrs.update({
            "placeholder": "name@example.ru",
            "autocomplete": "email",
        })

    def clean_text(self):
        t = (self.cleaned_data.get("text") or "").strip()
        if len(t) < 3:
            raise forms.ValidationError("Текст слишком короткий.")
        if len(t) > 120:
            raise forms.ValidationError("Слишком длинный текст (максимум 120 символов).")
        return t

    @staticmethod
    def _is_hex(v: str) -> bool:
        return bool(v) and len(v) == 7 and v[0] == "#" and all(c in "0123456789abcdefABCDEF" for c in v[1:])

    def clean_text_color(self):
        v = (self.cleaned_data.get("text_color") or "").strip() or "#FFFFFF"
        if not self._is_hex(v):
            raise forms.ValidationError("Некорректный цвет текста.")
        return v.upper()

    def _active_option_exists(self, opt_type: str, *, cat_id: int, value: str) -> bool:
        return RibbonOption.objects.filter(
            opt_type=opt_type,
            is_active=True,
            news__cat_id=cat_id,
            css_value__iexact=value,
        ).exists()

    def clean_ribbon_bg(self):
        v = (self.cleaned_data.get("ribbon_bg") or "").strip() or "#1E4ED8"
        if not self._is_hex(v):
            raise forms.ValidationError("Некорректный цвет ленты.")

        if not self._active_option_exists(RibbonOption.TYPE_COLOR, cat_id=3, value=v):
            raise forms.ValidationError("Выберите цвет ленты из каталога.")
        return v.upper()

    def clean_font_family(self):
        v = (self.cleaned_data.get("font_family") or "").strip() or "'Montserrat', sans-serif"
        if not self._active_option_exists(RibbonOption.TYPE_FONT, cat_id=4, value=v):
            raise forms.ValidationError("Выберите шрифт из каталога.")
        return v

    def clean(self):
        cleaned = super().clean()

        phone = (cleaned.get("phone") or "").strip()
        email = (cleaned.get("email") or "").strip().lower()

        cleaned["phone"] = phone
        cleaned["email"] = email

        if not phone and not email:
            message = "Укажите телефон или email, чтобы мы могли связаться с вами."
            self.add_error("phone", message)
            self.add_error("email", message)

        if cleaned.get("is_group_order"):
            if not cleaned.get("persons_count"):
                self.add_error("persons_count", "Укажите количество человек.")

            if not (cleaned.get("persons_list") or "").strip():
                self.add_error("persons_list", "Добавьте список ФИО.")

        return cleaned


# ============================================================
# Контакты: обратная связь
# ============================================================

class OptionalContactChoiceField(forms.ModelChoiceField):
    """Не блокирует обращение, если необязательный получатель уже удалён."""

    def to_python(self, value):
        if value in self.empty_values:
            return None

        try:
            return super().to_python(value)
        except (forms.ValidationError, TypeError, ValueError):
            return None


class ContactRequestForm(forms.ModelForm):
    contact = OptionalContactChoiceField(
        queryset=Contact.objects.select_related("group").order_by("group__order", "order", "id"),
        required=False,
        empty_label="Выберите получателя (необязательно)",
        widget=forms.Select(attrs={"class": "form-control", "id": "contact_form_contact"}),
        label="Кому",
    )

    class Meta:
        model = ContactRequest
        fields = ["name", "email", "phone", "message", "contact"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Имя", "autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email", "autocomplete": "email"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Телефон", "autocomplete": "tel"}),
            "message": forms.Textarea(attrs={"class": "form-control", "placeholder": "Сообщение", "rows": 7}),
        }

    def clean_name(self):
        return (self.cleaned_data.get("name") or "").strip()

    def clean_email(self):
        return (self.cleaned_data.get("email") or "").strip().lower()

    def clean_phone(self):
        return (self.cleaned_data.get("phone") or "").strip()

    def clean_message(self):
        msg = (self.cleaned_data.get("message") or "").strip()
        if len(msg) < 5:
            raise forms.ValidationError("Сообщение слишком короткое.")
        return msg
