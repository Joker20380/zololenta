# 🎀 Золотая лента — сайт и конструктор выпускных лент

Django-проект для мастерской выпускных и памятных лент.

Платформа объединяет публичный сайт, каталог материалов, контакты, подписку, интерактивный конструктор именной ленты, Django admin и Telegram-уведомления по заказам.

Главная цель проекта — дать клиенту быстрый и понятный путь от выбора цвета, шрифта и текста до готовой заявки на согласование макета.

---

## 🚀 Основные возможности

### 🌐 Публичный сайт

- Главная страница с презентационными блоками.
- Информационные страницы.
- Новости и материалы.
- Контакты и карта.
- Подписка и отписка от рассылки.
- Адаптивный дизайн.
- Кастомные страницы ошибок 400, 403, 404, 500.

---

## 🎨 Конструктор выпускной ленты

Ключевая бизнес-функция сайта — интерактивный конструктор.

Пользователь может выбрать:

- текст на ленте;
- цвет ленты;
- цвет текста;
- шрифт;
- фольгу;
- количество;
- список ФИО для группового заказа;
- контактные данные;
- комментарий к заказу.

После отправки создаётся заявка RibbonOrder, а затем система отправляет или обновляет сообщение в Telegram.

---

## 🧵 Каталог цветов ленты

Цвета лент управляются через справочник RibbonOption.

### Логика хранения

- opt_type = color
- css_value = HEX-цвет в формате #RRGGBB
- News.title = человекочитаемое название цвета
- News.photo = изображение карточки цвета
- категория цветов = cat_id=3

### Пример отображения

    Молочный · #E9E5D3
    Золотистый · #AF993E
    Винный · #764552

### Обновление каталога цветов

    cd ~/zololenta/public_html/zololenta
    source ../venv/bin/activate

    python manage.py seed_ribbon_colors_from_catalog --dry-run
    python manage.py seed_ribbon_colors_from_catalog

После обновления:

    python manage.py check
    python manage.py collectstatic --noinput
    touch tmp/restart.txt

---

## ✍️ Каталог шрифтов

Шрифты конструктора локальные. Каталог конструктора не зависит от Google Fonts.

### Где лежат файлы

    zololenta/static/zololenta/fonts/ribbon/

### Где подключаются font-face

    zololenta/static/zololenta/css/ribbon-fonts.css

### Логика хранения

- opt_type = font
- css_value = CSS font-family
- font_url пустой
- News.title = название шрифта
- News.photo = превью шрифта
- категория шрифтов = cat_id=4

### Текущий набор шрифтов

- Romantique Script
- Good Vibes Pro
- Zither Script
- Grosvenor Script
- Esenin Script
- Mon Amour One
- Magnolia Script
- Belissimo Script
- Mazurka Script
- Ceremonious One
- Astoria Script One

### Синхронизация шрифтов

    cd ~/zololenta/public_html/zololenta
    source ../venv/bin/activate

    python manage.py seed_ribbon_fonts --dry-run
    python manage.py seed_ribbon_fonts

### Генерация превью шрифтов

    python manage.py generate_ribbon_font_previews --dry-run --force
    python manage.py generate_ribbon_font_previews --force

Превью сохраняются в News.photo у связанных шрифтовых опций.

---

## 📲 Telegram-интеграция

Telegram-сообщение формируется в:

    main/tg_service.py

В сообщение попадают:

- ID заказа;
- статус;
- текст ленты;
- цвет ленты;
- шрифт;
- цвет текста;
- фольга;
- количество;
- список ФИО;
- комментарий;
- контакты клиента.

### Человекочитаемые цвета

Цвет ленты в заказе хранится как HEX, но в Telegram резолвится через каталог:

    RibbonOrder.ribbon_bg
    -> RibbonOption TYPE_COLOR по css_value
    -> News.title

Пример:

    Цвет ленты: Молочный · #E9E5D3
    Цвет текста: Золото · #FFD36A

Быстрые цвета текста:

| HEX | Название |
| --- | --- |
| #FFFFFF | Белый |
| #111827 | Чёрный |
| #FFD36A | Золото |
| #D1D5DB | Серебро |

---

## 🧩 Основные модели

### News

Используется не только для новостей, но и как карточка каталога.

Для конструктора:

| Назначение | Категория |
| --- | --- |
| Цвета лент | cat_id=3 |
| Шрифты | cat_id=4 |

Ключевые поля:

- title
- slug
- content
- photo
- cat
- is_published
- time_create
- time_update

### RibbonOption

Связывает карточку News с бизнес-опцией конструктора.

Ключевые поля:

- news
- opt_type
- css_value
- font_url
- is_active

### RibbonOrder

Заявка из конструктора.

Ключевые поля:

- text
- ribbon_bg
- font_family
- text_color
- foil
- persons_count
- persons_list
- comment
- name
- phone
- email
- status
- tg_chat_id
- tg_message_id
- tg_thread_root_id
- tg_last_synced_at

---

## 🗂️ Static и media

### Source static

    zololenta/static/

### Collected static

    static/

### Настройки

В Django-проекте используется:

    STATIC_URL = "static/"
    STATIC_ROOT = "/home/j/joker2038/zololenta/public_html/static/"
    STATICFILES_DIRS = [BASE_DIR / "static"]

После изменения CSS, JS, изображений или шрифтов:

    cd ~/zololenta/public_html/zololenta
    source ../venv/bin/activate

    python manage.py collectstatic --noinput
    touch tmp/restart.txt

---

## ✅ Smoke-test конструктора

Проверка формы без создания заказа:

    cd ~/zololenta/public_html/zololenta
    source ../venv/bin/activate

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

Ожидаемый результат:

    form valid: True

---

## 🛠️ Полезные команды

### Проверка проекта

    cd ~/zololenta/public_html/zololenta
    source ../venv/bin/activate

    python manage.py check

### Последние заказы

    python manage.py shell -c "
    from main.models import RibbonOrder

    for x in RibbonOrder.objects.order_by('-created_at')[:10]:
        print(x.created_at, x.id, x.name, x.phone, x.ribbon_bg, x.text_color)
    "

### Активные цвета

    python manage.py shell -c "
    from main.models import RibbonOption

    qs = RibbonOption.objects.filter(
        opt_type=RibbonOption.TYPE_COLOR,
        is_active=True,
    ).select_related('news').order_by('-news__time_update')

    print('active colors:', qs.count())
    for x in qs[:120]:
        print(x.id, x.news.title, x.css_value)
    "

### Активные шрифты

    python manage.py shell -c "
    from main.models import RibbonOption

    qs = RibbonOption.objects.filter(
        opt_type=RibbonOption.TYPE_FONT,
        is_active=True,
    ).select_related('news').order_by('id')

    print('active fonts:', qs.count())
    for x in qs:
        print(x.id, x.news.title, x.css_value, x.font_url)
    "

---

## 🔐 Production workflow

Перед правками делать backup.

Базовый порядок:

    cd ~/zololenta/public_html/zololenta
    source ../venv/bin/activate

    python manage.py check
    git status --short

Не использовать:

    git add .

Добавлять только целевые файлы.

---

## 🧾 Git policy

Репозиторий может содержать много рабочих файлов, поэтому фиксировать нужно точечно.

Пример:

    git add README.md
    git commit -m "Polish project README"
    git push origin main

---

## 🏁 Статус

Проект разворачивается на production-хостинге и поддерживает рабочий контур:

    клиент
    -> конструктор
    -> RibbonOrder
    -> Django admin
    -> Telegram
    -> согласование макета
