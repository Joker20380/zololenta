# Золотая лента

Django-проект сайта мастерской выпускных и памятных лент.

Проект включает публичный сайт, новости, контакты, подписку, интерактивный конструктор именной ленты, админку заказов и Telegram-уведомления.

## Основной функционал

- Главная страница и информационные страницы.
- Новости и материалы.
- Контакты и карта.
- Подписка и отписка от рассылки.
- Кастомные страницы ошибок 400, 403, 404, 500.
- Конструктор выпускной ленты.
- Заявки в Django admin.
- Telegram-синхронизация заказов.

## Конструктор ленты

Пользователь выбирает:

- текст на ленте;
- цвет ленты;
- цвет текста;
- шрифт;
- фольгу;
- количество;
- список ФИО для группового заказа;
- контактные данные;
- комментарий.

После отправки создаётся RibbonOrder. Затем сигнал post_save запускает отправку или обновление сообщения в Telegram.

## Каталог цветов

Цвета хранятся через RibbonOption:

- opt_type = color;
- css_value = #RRGGBB;
- связанная News хранит название и изображение;
- категория цветов: cat_id=3.

Команда обновления палитры:

    python manage.py seed_ribbon_colors_from_catalog --dry-run
    python manage.py seed_ribbon_colors_from_catalog

После обновления:

    python manage.py check
    python manage.py collectstatic --noinput
    touch tmp/restart.txt

## Каталог шрифтов

Шрифты конструктора локальные. Google Fonts в каталоге конструктора не используются.

Файлы шрифтов:

    static/zololenta/fonts/ribbon/

CSS:

    static/zololenta/css/ribbon-fonts.css

Шрифты хранятся через RibbonOption:

- opt_type = font;
- css_value = "'Font Name', cursive";
- font_url пустой;
- связанная News хранит название и превью;
- категория шрифтов: cat_id=4.

Команда синхронизации шрифтов:

    python manage.py seed_ribbon_fonts --dry-run
    python manage.py seed_ribbon_fonts

Генерация превью:

    python manage.py generate_ribbon_font_previews --dry-run --force
    python manage.py generate_ribbon_font_previews --force

## Telegram

Telegram-сообщение формируется в main/tg_service.py.

В сообщении указываются:

- ID заказа;
- статус;
- текст;
- цвет ленты;
- шрифт;
- цвет текста;
- фольга;
- количество;
- список ФИО;
- комментарий;
- контакты.

Цвет ленты отображается в человекочитаемом виде:

    RibbonOrder.ribbon_bg
    -> RibbonOption TYPE_COLOR по css_value
    -> News.title

Пример:

    Цвет ленты: Молочный · #E9E5D3
    Цвет текста: Золото · #FFD36A

## Static

Схема static:

    source static:
    zololenta/static/

    collected static:
    ../static/

В settings.py:

    STATIC_URL = "static/"
    STATIC_ROOT = "/home/j/joker2038/zololenta/public_html/static/"
    STATICFILES_DIRS = [BASE_DIR / "static"]

После изменения CSS, JS, картинок или шрифтов:

    python manage.py collectstatic --noinput
    touch tmp/restart.txt

## Основные модели

### News

Используется для новостей и карточек каталога.

Для конструктора:

- цвета: cat_id=3;
- шрифты: cat_id=4;
- title — название;
- photo — картинка карточки;
- content — служебное описание.

### RibbonOption

Опция конструктора.

Ключевые поля:

- news;
- opt_type;
- css_value;
- font_url;
- is_active.

### RibbonOrder

Заявка из конструктора.

Ключевые поля:

- text;
- ribbon_bg;
- font_family;
- text_color;
- foil;
- persons_count;
- persons_list;
- comment;
- name;
- phone;
- email;
- status;
- tg_chat_id;
- tg_message_id;
- tg_thread_root_id;
- tg_last_synced_at.

## Проверка формы конструктора

Smoke-test без создания заказа:

    python manage.py shell -c "
    from main.forms import RibbonOrderForm
    from main.models import RibbonOption

    font = RibbonOption.objects.filter(
        opt_type=RibbonOption.TYPE_FONT,
        is_active=True,
    ).order_by('id').first()

    data = {
        'text': 'Тестовая лента',
        'ribbon_bg': '#E9E5D3',
        'font_family': font.css_value if font else '',
        'text_color': '#FFFFFF',
        'is_group_order': '',
        'persons_count': '1',
        'persons_list': '',
        'comment': '',
        'name': 'Тест',
        'phone': '+79990000000',
        'email': '',
    }

    form = RibbonOrderForm(data=data)
    print('form valid:', form.is_valid())
    print('errors:', form.errors.as_json(escape_html=False))
    "

Ожидаемо:

    form valid: True

## Production workflow

Перед правками делать backup.

Проверки:

    python manage.py check
    git status --short

Не использовать:

    git add .

Добавлять только целевые файлы.

## Git

Пример фикса README:

    git add README.md
    git commit -m "Add project README"
    git push origin main
