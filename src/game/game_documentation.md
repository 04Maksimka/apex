# 🎮 AstraGeek Sky Quiz — Документация

Образовательная игровая платформа для изучения созвездий, именных звёзд и объектов каталога Мессье. Встроена в проект [AstraGeek](https://astrageek.ru/) и использует реальные астрономические данные — каталог Hipparcos, данные Мессье и карты созвездий.

---

## Содержание

1. [Быстрый старт](#быстрый-старт)
2. [Архитектура](#архитектура)
3. [Игровые режимы](#игровые-режимы)
4. [Система очков](#система-очков)
5. [API Reference](#api-reference)
6. [Структура файлов](#структура-файлов)
7. [Конфигурация](#конфигурация)
8. [Расширение игры](#расширение-игры)
9. [Известные ограничения](#известные-ограничения)

---

## Быстрый старт

### 1. Регистрация Blueprint в `app.py`

```python
from src.web.game_blueprint import game_bp
app.register_blueprint(game_bp)
```

### 2. Запуск

```bash
python -m flask --app src/web/app run
```

### 3. Открыть в браузере

```
http://localhost:5000/game/lobby
```

---

## Архитектура

```
src/
├── game/
│   ├── __init__.py
│   ├── session.py           # Управление игровыми сессиями (in-memory)
│   ├── question_factory.py  # Генерация вопросов для каждого режима
│   └── scoring.py           # Подсчёт очков, ранги, бонусы
└── web/
    ├── game_blueprint.py    # Flask Blueprint: /game/*
    └── public_html/
        ├── games.html
        ├── game_constellation.html
        ├── game_star.html
        ├── game_messier.html
        ├── game_draw.html
        └── game_trivia.html
```

### Поток данных

```
Браузер → POST /game/api/start    → создаёт GameSession
Браузер → GET  /game/api/question → QuestionFactory генерирует PNG (Pinhole/Stereo)
                                    → base64 + опции
Браузер → POST /game/api/answer   → scoring.calculate_score → результат
Браузер → GET  /game/api/hint     → подсказка (-50% очков)
```

---

## Игровые режимы

### Режим 1 — Угадай созвездие 🔭

Определить созвездие по снимку неба без подписей.

- `PinholeProjector` центрируется на случайном созвездии
- Линии видны (`add_constellations=True`), подписи скрыты
- 4 варианта: 1 правильный + 3 дистрактора

| Сложность | Созвездий | Лим. блеска |
|-----------|-----------|-------------|
| Легко     | 15        | 4.5m        |
| Средне    | ~37       | 5.5m        |
| Сложно    | Все 88    | 6.5m        |

---

### Режим 2 — Назови звезду ⭐

Определить именную звезду, выделенную красным кольцом в центре изображения.

- Данные из `lines_data.json`: `"HIP 32349": [{"english": "Sirius"}]`
- FOV = 30° (крупный план)
- Звезда всегда в центре кадра — кольцо рисуется в (0, 0) проекции
- 4 варианта: правильное имя + 3 других именных звезды

---

### Режим 3 — Объекты Мессье 🌌

Определить номер объекта Мессье (M1–M110) по описанию и изображению.

- Вопрос: тип объекта + созвездие, без номера
- FOV = 50°, 4 варианта с номерами M
- 110 объектов: галактики, туманности, скопления, остатки сверхновых

---

### Режим 4 — Нарисуй созвездие ✏️

Соединить звёзды линиями так, как они соединены на официальных картах.

**Управление:**
- `Клик` по звезде → выбрать
- `Клик` по другой → нарисовать линию
- `↩ Отменить` / `🗑 Очистить` / `✔ Проверить`

**Оценка:**
```
совпавшие_рёбра / всего_рёбер × 100%
≥ 50% → зачтено как правильный ответ
```

После проверки эталонное созвездие показывается зелёным пунктиром.

**Алгоритм проекции:** гномоническая проекция на касательную плоскость в центре созвездия → нормализация к `[-1, 1]`.

---

### Режим 5 — Trivia + Карта 🗺️

По текстовому описанию выбрать название созвездия. Карта неба (FOV = 120°) с подписями помогает ориентироваться.

Добавить вопросы в `TRIVIA_QUESTIONS`:
```python
{
    "question": "В этом созвездии...",
    "answer": "ORI",   # аббревиатура из CONSTELLATIONS_DATA
    "hint": "Подсказка...",
}
```

---

## Система очков

### Базовые очки

| Сложность | Очки |
|-----------|------|
| Легко     | 100  |
| Средне    | 200  |
| Сложно    | 350  |

### Множители

| Условие                  | Множитель |
|--------------------------|-----------|
| Серия 2+ правильных      | ×1.2      |
| Серия 3+                 | ×1.5      |
| Серия 5+                 | ×2.0      |
| Серия 10+                | ×3.0      |
| Ответ ≤ 8 секунд         | ×1.2      |
| Использована подсказка   | ×0.5 базовых |

### Ранги

| Очки  | Ранг                  |
|-------|-----------------------|
| 5000+ | 🌌 Galactic Explorer  |
| 3000+ | ⭐ Star Navigator     |
| 1500+ | 🔭 Sky Watcher        |
| 500+  | 🌙 Night Apprentice   |
| 0+    | 🌑 Beginner           |

---

## API Reference

### `POST /game/api/start`

```json
// Request
{ "mode": "constellation", "difficulty": "easy", "rounds": 10 }

// Response 201
{ "session_id": "uuid-...", "mode": "constellation", "score": 0, ... }
```

Допустимые значения `mode`: `constellation` | `star` | `messier` | `draw` | `trivia`  
Допустимые значения `difficulty`: `easy` | `medium` | `hard`

---

### `GET /game/api/question?session_id=<id>`

**Ответ (режимы с изображением):**
```json
{
  "session": { "round": 1, "score": 0, ... },
  "question_type": "constellation",
  "question": "Какое созвездие изображено?",
  "image": "<base64 PNG>",
  "options": ["Orion", "Leo", "Cygnus", "Cassiopeia"],
  "hint": "...",
  "round": 1
}
```

**Ответ (режим draw):**
```json
{
  "question_type": "draw",
  "stars": [
    { "hip_id": 27989, "x": 0.12, "y": -0.34, "v_mag": 0.45, "name": "Betelgeuse" }
  ],
  "round": 1
}
```

**Ответ (игра завершена):**
```json
{ "finished": true, "score": 1850, "rank": "⭐ Star Navigator" }
```

---

### `POST /game/api/answer`

**Режимы с выбором:**
```json
{ "session_id": "...", "answer": "Orion", "used_hint": false, "time_seconds": 6.3 }
```

**Режим draw:**
```json
{ "session_id": "...", "drawn_edges": [[27989, 24436], ...], "time_seconds": 42.1 }
```

**Ответ:**
```json
{
  "correct": true,
  "correct_answer": "Orion",
  "points_earned": 150,
  "total_score": 350,
  "streak": 2,
  "fun_fact": "Орион содержит...",
  "is_finished": false,
  "rank": "🌑 Beginner"
}
```

---

### `GET /game/api/hint?session_id=<id>`

```json
{ "hint": "Центр этого созвездия находится в направлении ORI" }
```

> Использование подсказки снижает базовые очки на 50%.

---

### `GET /game/api/score?session_id=<id>`

```json
{ "score": 450, "round": 4, "streak": 1, "accuracy": 75.0, "rank": "🌑 Beginner" }
```

---

### `POST /game/api/finish`

Закрывает сессию и возвращает финальный результат с историей.

```json
{ "session_id": "..." }
```

---

## Структура файлов

```
src/game/session.py
├── GameSession (dataclass)
│   ├── session_id, mode, difficulty
│   ├── score, round, total_rounds, streak, best_streak, correct_count
│   ├── used_objects: Set  — уже показанные объекты (без повторов)
│   ├── history: List      — история раундов
│   └── current_question   — текущий вопрос (для проверки ответа)
├── DIFFICULTY_CONSTELLATIONS — пулы созвездий по сложности
├── DIFFICULTY_MAGNITUDE      — лимиты блеска
└── create/get/delete_session()

src/game/question_factory.py
├── QuestionFactory
│   ├── make_constellation_question()
│   ├── make_star_question()
│   ├── make_messier_question()
│   ├── make_draw_question()
│   ├── check_draw_answer()     — edge-based matching
│   └── make_trivia_question()
├── CONSTELLATION_FACTS, STAR_FACTS, MESSIER_FACTS
└── TRIVIA_QUESTIONS

src/game/scoring.py
├── calculate_score(difficulty, correct, streak, used_hint, time_seconds)
├── get_rank(total_score)
└── build_result(...)

src/web/game_blueprint.py
└── Blueprint "game", prefix="/game"
    ├── Статические страницы: /lobby, /<mode>
    └── API: /api/start, /api/question, /api/answer, /api/hint, /api/score, /api/finish
```

---

## Конфигурация

### Пулы созвездий по сложности (`session.py`)

```python
DIFFICULTY_CONSTELLATIONS = {
    "easy": ["ORI", "UMA", "CAS", "CYG", ...],  # 15 самых известных
    "medium": [...],                               # ~37 созвездий
    "hard": None,                                  # None = все 88
}
```

### Лимиты блеска

```python
DIFFICULTY_MAGNITUDE = {
    "easy": 4.5, "medium": 5.5, "hard": 6.5,
}
```

### FOV изображений по режимам

| Режим         | FOV   | Назначение           |
|---------------|-------|---------------------|
| constellation | 60°   | Стандартный вид      |
| star          | 30°   | Крупный план звезды  |
| messier       | 50°   | Область вокруг M-объекта |
| trivia        | 120°  | Широкоугольная карта |

### Качество изображений

В `_camera_config()` в `question_factory.py`:
```python
height_pix=600  # увеличить до 900 для HD; замедлит генерацию
```

---

## Расширение игры

### Добавить новый режим

1. Метод `make_<mode>_question(session)` в `QuestionFactory`
2. `_generate_question()` в `game_blueprint.py` — добавить ветку
3. `VALID_MODES` — добавить строку
4. Новый HTML-файл `game_<mode>.html`
5. Карточка в `games.html`

### Добавить trivia-вопросы

```python
TRIVIA_QUESTIONS.append({
    "question": "Это созвездие содержит туманность M42...",
    "answer": "ORI",
    "hint": "Пояс из трёх звёзд",
})
```

### Подключить SQLite (production)

Замените `_sessions: Dict` на SQLAlchemy-модель с полями `session_id`, `user_id`, `created_at`, `data (JSON)`.

### Кэширование изображений

Для часто запрашиваемых созвездий кэшируйте PNG по ключу `(abbr, difficulty)` через `functools.lru_cache` или Redis.

---

## Известные ограничения

| Проблема | Описание | Решение |
|----------|----------|---------|
| Сессии in-memory | Теряются при перезапуске | Redis / SQLite |
| Генерация PNG | ~0.5–2с на вопрос | Кэш изображений |
| Нет авторизации | `session_id` не защищён | JWT / Flask-Login |
| Draw mode | Некоторые созвездия имеют мало ярких звёзд | Снизить лимит блеска |

---

*AstraGeek Game Module v1.0*