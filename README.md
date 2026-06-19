# kval1 — Django-шаблон для квалификационного экзамена

Готовая обвязка под задание «реализуйте бэкенд для управления данными».
Вариант на **функциональных представлениях (FBV)**.

- Проект (пакет настроек): `kval`
- Приложение: `main`
- Модель: `Record` в `main/models.py`
- `.env` читает отдельный модуль `kval/env.py`
- Метрики запросов: `main/middleware.py` → файл `requests.log`
- База по умолчанию: SQLite (`data.sqlite3`)

> Под конкретный билет редактируешь **`main/models.py`** (поля + `clean()`),
> словарь виджетов в **`main/forms.py`** и колонки таблицы в
> **`main/templates/main/list.html`**. Остальное (админка, middleware, `.env`,
> `/ping/`, 404, статика) уже готово.

---

## 1. Быстрый старт

```bash
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Адреса:
- Свой интерфейс (список записей): http://127.0.0.1:8000/
- Админка: http://127.0.0.1:8000/admin/
- Тест-эндпоинт: http://127.0.0.1:8000/ping/

| URL | Имя маршрута | Назначение |
|-----|--------------|------------|
| `/` | `main:list` | список записей |
| `/add/` | `main:add` | создание |
| `/<id>/edit/` | `main:edit` | редактирование |
| `/<id>/remove/` | `main:remove` | удаление (с подтверждением) |
| `/admin/` | — | админка |
| `/ping/` | `ping` | health-check (200) |

---

## 2. Как адаптировать модель под любой вариант

Меняешь класс `Record` в `main/models.py`, поля формы — в `main/forms.py`
(словарь `widgets` в `Meta`), и колонки таблицы — в
`main/templates/main/list.html`.

### 2.1. Типы полей — шпаргалка

| В задании | Поле модели |
|-----------|-------------|
| VARCHAR(n) | `models.CharField("Метка", max_length=n)` |
| TEXT (длинный текст) | `models.TextField("Метка")` |
| INTEGER | `models.IntegerField("Метка")` |
| Целое ≥ 0 | `models.IntegerField("Метка", validators=[MinValueValidator(0)])` |
| Целое > 0 | `models.PositiveIntegerField("Метка", validators=[MinValueValidator(1)])` |
| DECIMAL(10,2) | `models.DecimalField("Метка", max_digits=10, decimal_places=2)` |
| DATE (только дата) | `models.DateField("Метка")` |
| TIMESTAMP (дата+время) | `models.DateTimeField("Метка")` |
| Дата создания (авто) | `models.DateTimeField("Создано", auto_now_add=True)` |
| BOOLEAN (флаг) | `models.BooleanField("Метка", default=False)` |
| EMAIL (проверка формата) | `models.EmailField("Email", max_length=100)` |

Модификаторы (в скобках через запятую):
- `unique=True` — поле уникально (дубликат → ошибка автоматически, отдельно проверять не надо);
- `blank=True` — необязательно в форме (для текста);
- `null=True, blank=True` — необязательно в форме и в БД (для чисел/дат).

### 2.2. Значения по умолчанию (default)

| Что нужно | Как написать |
|-----------|--------------|
| Дата по умолчанию = сегодня | `models.DateField("Дата", default=timezone.localdate)` |
| Дата+время по умолчанию = сейчас | `models.DateTimeField("Когда", default=timezone.now)` |
| Число по умолчанию = 0 | `models.IntegerField("Просмотры", default=0)` |
| Флаг по умолчанию = False | `models.BooleanField("Опубликован", default=False)` |
| Текст по умолчанию | `models.CharField("Статус", max_length=20, default="новый")` |

Для дат нужен импорт `from django.utils import timezone`.
Важно: передаётся **функция без скобок** (`default=timezone.localdate`, а не
`timezone.localdate()`), иначе значение «застынет» на моменте запуска сервера.
Значение из `default` автоматически подставится в форму создания.

### 2.3. Валидация — метод `clean()` в модели

`clean()` вызывается и формой своего интерфейса, и админкой — правила работают
везде. Ключ в `ValidationError({...})` — это **имя поля**, под которым покажется
сообщение.

```python
from django.utils import timezone   # нужен для проверок с датами

def clean(self):
    # 1) текст не пустой (и не из одних пробелов)
    name = (self.name or "").strip()
    if not name:
        raise ValidationError({"name": "Поле не может быть пустым."})
    self.name = name

    # 2) число строго больше 0
    if self.price is not None and self.price <= 0:
        raise ValidationError({"price": "Значение должно быть больше 0."})

    # 3) число не отрицательное (>= 0)
    if self.count is not None and self.count < 0:
        raise ValidationError({"count": "Значение не может быть отрицательным."})

    # 4) дата НЕ в будущем (DateField)
    if self.on_date and self.on_date > timezone.localdate():
        raise ValidationError({"on_date": "Дата не может быть в будущем."})

    # 5) email содержит @
    if self.email and "@" not in self.email:
        raise ValidationError({"email": "Email должен содержать символ @."})
```

> `DateField` сравнивай с `timezone.localdate()`, `DateTimeField` — с `timezone.now()`.

В этом шаблоне форма ещё дублирует пару проверок методами `clean_name` /
`clean_price` в `main/forms.py` — это не обязательно, основная логика в модели.

### 2.4. Не забыть про форму и таблицу

- `main/forms.py`: в `Meta.fields` перечисли поля формы и пропиши им виджеты в
  словаре `widgets` (для чекбокса — `forms.CheckboxInput(attrs={"class": "form-check-input"})`,
  для даты — `forms.DateInput(attrs={"type": "date", "class": "form-control"})`).
- `main/templates/main/list.html`: добавь/убери колонки `<th>`/`<td>` под новые поля.

### 2.5. Пересоздать миграции после правки модели

**Полный сброс (надёжнее всего на экзамене):**
```bash
rm main/migrations/0001_initial.py        # Windows: del main\migrations\0001_initial.py
rm data.sqlite3                           # Windows: del data.sqlite3
python manage.py makemigrations
python manage.py migrate
```
(Удаляй только файлы вида `0001_initial.py`, не трогай `__init__.py`.)

**Без удаления данных (если просто добавил поле):**
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 3. Проверка перед сдачей

```bash
python manage.py test            # /ping/ -> 200 (+ smoke-тесты списка/формы/404)
python manage.py showmigrations  # миграции применены
```
Метрики (middleware): открой несколько страниц — статистика печатается в
консоль (`[stats] ...`) и пишется в `requests.log`.

### Статика при DEBUG=False (чтобы админка была со стилями и работала 404)

```bash
python manage.py collectstatic --noinput
# в .env поставь: DEBUG=False
python manage.py runserver
```
Стили отдаёт WhiteNoise. Кастомная страница 404 показывается только при
`DEBUG=False`. После проверки верни `DEBUG=True`.

---

## 4. Куда смотрит комиссия (оценочный лист)

| № | Критерий | Файл |
|---|----------|------|
| 1 | Модель + миграции | `main/models.py` |
| 2 | CRUD через админку | `main/admin.py` |
| 3 | Валидация | `main/models.py` (`clean()`) |
| 4 | 404 | `main/views.py` (`get_object_or_404`) + `main/templates/404.html` |
| 5 | Middleware метрик | `main/middleware.py` |
| 6 | Конфиг через `.env` | `.env` + `kval/env.py` + `kval/settings.py` |
| 7 | Тест `/ping/` | `main/tests.py` |
| 8 | Статика при `DEBUG=False` | `kval/settings.py` (WhiteNoise) |
| 9–10 | Веб-интерфейс (доп.) | `main/templates/`, `main/views.py`, `main/urls.py` |

---

## 5. Как устроен код (объяснение для защиты)

### Структура
```
kval1/
├── manage.py                 # точка входа Django (kval.settings)
├── .env                      # DEBUG, SECRET_KEY, параметры БД
├── kval/                     # пакет проекта (настройки и корневые маршруты)
│   ├── settings.py           # все настройки; вызывает env.read_dotenv()
│   ├── env.py                # мини-загрузчик .env (без сторонних библиотек)
│   ├── urls.py               # /admin/, /ping/, и include('main.urls')
│   └── wsgi.py               # точка входа для сервера
└── main/                     # приложение с логикой
    ├── models.py             # модель Record + валидация (clean)
    ├── forms.py              # RecordForm (виджеты в Meta.widgets)
    ├── admin.py              # настройка админки
    ├── views.py              # FBV: list / create / edit / delete / ping
    ├── urls.py               # маршруты приложения (app_name = "main")
    ├── middleware.py         # подсчёт метрик запросов → requests.log
    ├── tests.py              # smoke-тесты
    └── templates/            # layout.html, main/list/edit/remove, 404.html
```

### settings.py + env.py — конфигурация
`settings.py` в начале зовёт `env.read_dotenv()` — модуль `kval/env.py` читает
файл `.env` строка за строкой и кладёт значения в окружение (своя реализация,
работает без интернета и без `python-dotenv`). Дальше `SECRET_KEY`, `DEBUG`,
параметры БД берутся через `env.get()` / `env.flag()`. БД по умолчанию SQLite
(`data.sqlite3`); при `DB_ENGINE=postgres` подключится PostgreSQL. В `MIDDLEWARE`
включены WhiteNoise (статика при `DEBUG=False`) и `RequestStatsMiddleware`.

### models.py — данные и валидация
Класс `Record` описывает таблицу. У `price` стоит `MinValueValidator`, а метод
`clean()` содержит правила, которые трудно выразить одним валидатором (непустой
текст, число > 0). `clean()` вызывается и формой, и админкой, поэтому проверки
едины. `created` с `auto_now_add=True` проставляется автоматически.

### forms.py — форма своего интерфейса
`RecordForm` — `ModelForm`. Поля и их HTML-виджеты заданы **явно** в
`Meta.fields` и `Meta.widgets` (текст — `form-control`, чекбокс —
`form-check-input`, дата — `type="date"`). Методы `clean_name` / `clean_price`
повторяют проверки на уровне формы.

### admin.py — админка
`RecordAdmin` задаёт `list_display`, `search_fields`, `readonly_fields` —
CRUD-операции доступны прямо из `/admin/`.

### views.py — обработчики (FBV)
- `healthcheck` — отдаёт `pong`, статус 200 (для теста `/ping/`);
- `record_list` — отдаёт список записей в `main/list.html`;
- `record_create` / `record_edit` — показывают форму; при ошибке валидации
  возвращают её обратно со статусом **400** и сообщением, при успехе — редирект;
- `record_edit` / `record_delete` — через `get_object_or_404`, поэтому
  несуществующая запись даёт **404**.

### middleware.py — метрики
`RequestStatsMiddleware` после каждого ответа смотрит статус-код и увеличивает
счётчики (`total` / `2xx` / `4xx` / `5xx`) в общем `Counter`. Строка печатается
в консоль (`[stats] ...`) и дописывается в `requests.log`.

### urls.py — маршруты
`kval/urls.py` подключает `/admin/`, `/ping/` и `include("main.urls")`.
`main/urls.py` задаёт CRUD-маршруты с `app_name = "main"`, поэтому в шаблонах
ссылки пишутся как `{% url 'main:list' %}`, `{% url 'main:edit' record.pk %}`.

### templates/ — интерфейс
`main/layout.html` — каркас с Bootstrap и блоком сообщений. Остальные
наследуются: `list.html` (таблица записей), `edit.html` (форма создания/правки),
`remove.html` (подтверждение удаления), `404.html` (с кнопкой возврата к списку).

---

## 6. Очистка перед сдачей

Если нужно сдать «чистый» проект — без git-истории, кэшей, локальной БД и следов
в терминале.

### 6.1. Удалить git и всю историю коммитов

```bash
rm -rf .git
```
После этого папка перестаёт быть git-репозиторием: история коммитов, ветки,
ссылки на remote и `git log` исчезают полностью. Проверка: `git status` →
«not a git repository».

> Если нужна чистая история «с нуля»:
> `rm -rf .git && git init && git add . && git commit -m "Итоговая версия"`.

### 6.2. Удалить служебные файлы и кэши

```bash
rm -rf .venv data.sqlite3 requests.log static_collected
find . -type d -name __pycache__ -prune -exec rm -rf {} +
find . -type f -name '*.pyc' -delete
```
- `.venv` — виртуальное окружение (пересоздаётся);
- `data.sqlite3` — локальная база (пересоздаётся `migrate`);
- `requests.log`, `static_collected/` — генерируются при работе;
- `__pycache__`, `*.pyc` — кэш Python.

### 6.3. Очистить историю команд в терминале

```bash
# zsh (этот терминал):
unset HISTFILE          # запретить дозапись истории при выходе из сессии
: > ~/.zsh_history      # очистить файл истории zsh

# bash (если используется он):
: > ~/.bash_history

# история интерактивного Python (если запускал shell/REPL):
: > ~/.python_history
```
Важно: `unset HISTFILE` нужен **до закрытия терминала** — иначе при выходе zsh
допишет команды текущей сессии обратно в файл. После очистки закрой окно.

### 6.4. Что оставить

`.env` оставляй — без него проект не запустится. Здесь он специально лежит
**в репозитории** (не в `.gitignore`), чтобы проект сразу работал у проверяющего.
Миграцию `main/migrations/0001_initial.py` тоже оставляй — это часть проекта.

### Одной строкой (проект + git, без истории терминала)

```bash
rm -rf .git .venv data.sqlite3 requests.log static_collected && find . -type d -name __pycache__ -prune -exec rm -rf {} +
```

В Django forms.py отвечает за то, как поля твоей модели будут отображаться на сайте (в виде HTML-тегов) и как они будут проверяться при отправке.

Поскольку в твоем новом проекте модель называется Record, давай разберем пошагово и подробно, что именно, где и в каких случаях тебе нужно менять в коде формы под требования любого билета.

ЧАСТЬ 1. Изменение списка полей (fields)
Это самый верхний уровень. Тебе нужно сказать форме, какие именно колонки из базы данных показывать пользователю для заполнения.

Случай А: В билете ровно те поля, что в коде
Оставляешь как есть: fields = ("name", "code", "price", "active", "on_date").

Случай Б: Появилось новое поле (например, описание description или количество quantity)
Просто дописываешь их имена в кортеж:

Python


fields = ("name", "code", "price", "active", "on_date", "description", "quantity")
Случай В: Какое-то поле убрали из задания (например, убрали артикул/код)
Удаляешь его из списка: fields = ("name", "price", "active", "on_date").

ЧАСТЬ 2. Настройка внешнего вида (widgets)
Словарь widgets связывает поле Django с реальным HTML-тегом на странице и вешает на него визуальные стили (классы Bootstrap form-control или form-check-input).

Вот готовые шаблоны виджетов для всех возможных типов данных, которые тебе могут дать. Если в билете появляется поле нужного типа, ты просто копируешь строку для него внутрь словаря widgets:

1. Для обычного текста или уникальных кодов (CharField)
Когда использовать: Для названий, артикулов, email, строк.

Что писать в widgets:

Python


"имя_поля": forms.TextInput(attrs={"class": "form-control"}),
2. Для больших текстов (TextField)
Когда использовать: Для описаний, биографий, текстов статей.

Что писать в widgets:

Python


"description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),  # rows задает высоту поля в строках
3. Для дробных чисел и денег (DecimalField, FloatField)
Когда использовать: Для цены, стоимости, зарплаты.

Что писать в widgets:

Python


"price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),  # step="0.01" разрешает копейки
4. Для целых чисел (IntegerField, PositiveIntegerField)
Когда использовать: Для количества, возраста, просмотров.

Что писать в widgets:

Python


"quantity": forms.NumberInput(attrs={"class": "form-control", "step": "1"}),  # step="1" запрещает дробные числа
5. Для галочек Да/Нет (BooleanField)
Когда использовать: Для статусов типа "Активен", "Опубликовано", "Доставлено".

Что писать в widgets:

Python


"active": forms.CheckboxInput(attrs={"class": "form-check-input"}),  # У чекбоксов в Bootstrap свой класс!
6. Для выбора даты без времени (DateField)
Когда использовать: Для дат рождения, дат событий.

Что писать в widgets:

Python


"on_date": forms.DateInput(
    attrs={"class": "form-control", "type": "date"}, 
    format="%Y-%m-%d"
),
7. Для выбора даты и времени одновременно (DateTimeField)
Когда использовать: Для точного времени старта мероприятий, дедлайнов.

Что писать в widgets:

Python


"start_at": forms.DateTimeInput(
    attrs={"class": "form-control", "type": "datetime-local"}, 
    format="%Y-%m-%dT%H:%M"
),
8. Для выпадающих списков (ChoiceField / поле с choices в модели)
Когда использовать: Для фиксированных статусов ("Новый", "В обработке", "Завершен").

Что писать в widgets:

Python


"status": forms.Select(attrs={"class": "form-control"}),
ЧАСТЬ 3. Валидация полей (clean_имя_поля)
В Django-формах методы валидации отдельных полей обязательно должны называться по шаблону: clean_<имя_твоего_поля>. Если ты назовешь метод по-другому, Django его проигнорирует.

Внутри метода ты берешь данные из self.cleaned_data.get("имя_поля"), проверяешь условие, и если оно нарушено — выбрасываешь forms.ValidationError("Текст ошибки"). В конце метода обязательно нужно вернуть проверенное значение (return value).

Вот разбор двух твоих текущих методов и правила для новых:

1. Валидация текста на пустоту (clean_name)
Python


def clean_name(self):
    # Извлекаем строку. Если там None (ничего не ввели), берем пустую строку ""
    # Метод .strip() обрезает пробелы по краям, чтобы нельзя было обмануть форму, введя одни пробелы
    value = (self.cleaned_data.get("name") or "").strip()
    
    if not value:
        raise forms.ValidationError("Название обязательно.")
    return value
Когда менять: Если в билете просят, например, чтобы поле code (код) или title (заголовок) не содержало пробелов и не было пустым — ты копируешь этот метод, переименовываешь в clean_code или clean_title и меняешь внутри "name" на новое имя.

2. Валидация чисел (clean_price)
Python


def clean_price(self):
    value = self.cleaned_data.get("price")
    
    # Проверяем, что число вообще ввели, и что оно меньше или равно 0
    if value is not None and value <= 0:
        raise forms.ValidationError("Сумма должна быть больше 0.")
    return value
Когда менять: Если в билете просят, чтобы количество quantity было больше нуля, ты создаешь метод:

Python


def clean_quantity(self):
    value = self.cleaned_data.get("quantity")
    if value is not None and value <= 0:
        raise forms.ValidationError("Количество должно быть больше 0.")
    return value
Если по билету число может быть нулем (например, >= 0), то знак проверки меняешь на value < 0.

3. Валидация дат (Например, нельзя в будущем)
Если в билете требуют проверить дату прямо в форме, пишется такой метод (не забудь импортировать утилиту времени from django.utils import timezone в самый верх файла):

Python


def clean_on_date(self):
    value = self.cleaned_data.get("on_date")
    
    # Если дата введена и она больше сегодняшнего дня
    if value and value > timezone.now().date():
        raise forms.ValidationError("Дата не может быть в будущем.")
    return value
💡 Пример: Как будет выглядеть forms.py, если в билет добавили поле «Количество» (quantity), а поле «Код» (code) убрали:
Python


from django import forms
from django.utils import timezone  # если нужна валидация дат
from .models import Record

class RecordForm(forms.ModelForm):
    class Meta:
        model = Record
        # 1. Изменили список полей: убрали code, добавили quantity
        fields = ("name", "price", "active", "on_date", "quantity")
        
        # 2. Настроили виджеты под актуальный список полей
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "on_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"
            ),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "step": "1"}), # новый виджет
        }

    # 3. Валидация полей
    def clean_name(self):
        value = (self.cleaned_data.get("name") or "").strip()
        if not value:
            raise forms.ValidationError("Название обязательно.")
        return value

    def clean_price(self):
        value = self.cleaned_data.get("price")
        if value is not None and value <= 0:
            raise forms.ValidationError("Сумма должна быть больше 0.")
        return value

    # Новый метод валидации для добавленного поля quantity
    def clean_quantity(self):
        value = self.cleaned_data.get("quantity")
        if value is not None and value < 0:
            raise forms.ValidationError("Количество не может быть отрицательным.")
        return value
