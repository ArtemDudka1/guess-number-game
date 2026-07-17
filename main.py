import pygame
import random
import math
import json
import os
import sys
import subprocess
from pathlib import Path

from constants import *

pygame.init()
pygame.key.set_repeat(500, 40)

DEBUG_MODE = os.environ.get(
    "NUMBER_TILES_DEBUG",
    ""
).lower() in {"1", "true", "yes", "on"}

DEBUG_ACHIEVEMENTS = DEBUG_MODE

# До полноценной версии developer-инструментов панель доступна постоянно.
# DEBUG_MODE отдельно управляет только диагностическими логами.
DEVELOPER_MODE = True

command_key_pressed = False

developer_queued_changes = None

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Угадай число")

# Шрифты
font = pygame.font.Font(None, 44)
big_font = pygame.font.Font(None, 68)
small_font = pygame.font.Font(None, 32)
title_font = pygame.font.SysFont("Arial", 44, bold=True)
achievement_popup_description_font = pygame.font.Font(
    None,
    27
)

current_screen = MENU

profile_back_button = None

started_all_in = False

current_popup = None
popup_title = ""
popup_text = ""

# ==========================================================
#                DEVELOPER PANEL STATE
# ==========================================================

# Состояние developer-панели всегда временное.
# Изменения применяются только после нажатия «Готово».

developer_pending_balance = 0
developer_pending_xp = 0

developer_grant_tags_scroll_x = 0
developer_reset_tags_scroll_x = 0

developer_grant_achievement_ids = []
developer_reset_achievement_ids = []

developer_grant_all = False
developer_reset_all = False

# Снимок состояний достижений на момент открытия панели.
# Понадобится для проверки полей выдачи и отката.
developer_initial_achievement_states = {}

developer_grant_input_error = ""
developer_reset_input_error = ""

# Достижения, открытые за текущую игру
newly_unlocked_achievements = []

# Настройки текущей игры
min_number = 1
max_number = 10
max_attempts = 3
difficulty_name = "Лёгкая"

secret_number = None
attempts_left = None
game_over = False
win = False
message = "Выбери число"
result_line_1 = ""
result_line_2 = ""
tiles = []

# Флаг: игрок уже сделал хотя бы один ход в текущей игре
game_started = False

# Статистика
score = 0
highest_balance = 0
games_played = 0
wins = 0
losses = 0
current_streak = 0
best_streak = 0

total_attempts_in_wins = 0
tracked_wins_for_attempts = 0

games_with_bet = 0
all_in_bets_count = 0

total_xp = 0
last_xp_gained = 0

# Профиль
player_name = "Player"

# Ставки
selected_bet = 0
current_bet = 0
bet_options = [10, 25, 50, 100]

# Ввод своей ставки
custom_bet_text = ""
custom_bet_active = False
custom_bet_error = ""

# Поп-ап сброса статистики
reset_popup_open = False

# ======================================================
#               ACHIEVEMENT STATISTICS
# ======================================================

achievement_stats = {

    # ---------- Bets ----------

    "total_bets": 0,
    "max_bet": 0,

    # ---------- Special ----------

    "first_try_win": 0,
    "big_win": 0,
    "no_bet_streak": 0,
    "no_bet_streak_progress": 0,
    "all_in_win": 0,
    "all_in_1000": 0,
    "last_chance_win": 0,
    "absolute_risk": 0,
    "absolute_risk_progress": 0,

    # ---------- Hidden ----------

    "trust_fate": 0,
    "trust_fate_streak": 0,
    "phoenix": 0,
    "phoenix_stage": 0,
    "perfect_balance": 0,
    "perfect_balance_progress": 0,
    "perfect_balance_last_result": 0,
    "everything_possible": 0,
    "everything_possible_easy": 0,
    "everything_possible_medium": 0,
    "everything_possible_hard": 0,
    "lose_streak": 0

}

# Хранит дополнительную статистику,
# необходимую только для системы достижений.


# ==========================================================
#                ACHIEVEMENT MANAGER
# ==========================================================

# ---------- Player Data ----------

def get_player_stats():
    """
    Возвращает всю текущую статистику игрока.
    """

    stats = {

        # ---------- General ----------

        "games": games_played,
        "highest_balance": highest_balance,
        "wins": wins,
        "losses": losses,
        "current_streak": current_streak,
        "best_streak": best_streak,
        "balance": score,

        # ---------- Progress ----------

        "level": get_player_level(),
        "total_xp": total_xp,

        # ---------- Future ----------

        "coins": 0,
        "quests_completed": 0,
        "achievements_completed": 0

    }

    stats.update(achievement_stats)

    return stats

def add_bonus_xp(amount):
    global total_xp, last_xp_gained

    old_level = get_player_level()

    total_xp += amount

    new_level = get_player_level()

    if new_level > old_level:
        level_up(new_level)

    last_xp_gained = amount

    save_progress()

# ---------- Achievement Manager ----------

def check_achievements(excluded_ids=None):
    """
    Проверяет выполнение всех достижений.

    Делает несколько проходов, потому что награда
    одного достижения может открыть другое достижение.
    """
    excluded_ids = set(excluded_ids or ())

    while True:
        unlocked_in_this_pass = False

        stats = get_player_stats()

        if DEBUG_ACHIEVEMENTS:
            print(stats)

        for category in ACHIEVEMENTS_DATA.values():
            for achievement in category:

                if (
                        achievement["id"] in excluded_ids
                        or achievement.get("completed", False)
                ):
                    continue

                stat_key = achievement.get(
                    "progress_stat",
                    achievement["stat"]
                )

                current_value = stats.get(stat_key, 0)

                goal = achievement["goal"]

                if DEBUG_ACHIEVEMENTS:
                    print(
                        f'{achievement["title"]}: '
                        f'{current_value} / {goal}'
                    )

                if current_value >= goal:
                    unlock_achievement(
                        achievement
                    )

                    unlocked_in_this_pass = True

        if not unlocked_in_this_pass:
            break


def unlock_achievement(achievement):
    """
    Выдаёт достижение игроку и добавляет его
    в список достижений, открытых за текущую игру.
    """
    if achievement.get("completed", False):
        return

    if DEBUG_MODE:
        print(
            "UNLOCK:",
            achievement["id"],
            achievement.get("type"),
            achievement["title"]
        )

    achievement["completed"] = True

    already_added = any(
        unlocked["id"] == achievement["id"]
        for unlocked in newly_unlocked_achievements
    )

    if not already_added:
        newly_unlocked_achievements.append(
            achievement
        )

    add_bonus_xp(
        achievement["reward_xp"]
    )


def print_newly_unlocked_achievements():
    if not DEBUG_MODE:
        return

    if not newly_unlocked_achievements:
        print("🏆 Новых достижений за игру нет")
        return

    total_reward_xp = sum(
        achievement["reward_xp"]
        for achievement in newly_unlocked_achievements
    )

    print("\n🏆 Новые достижения за игру:")

    sorted_achievements = (
        get_sorted_unlocked_achievements()
    )

    for index, achievement in enumerate(
        sorted_achievements,
        start=1
    ):
        achievement_type = achievement.get(
            "type",
            "обычное"
        )

        print(
            f"{index}. "
            f"{achievement['title']} — "
            f"+{achievement['reward_xp']} XP "
            f"[тип: {achievement_type}]"
        )

    print(
        f"Всего получено за достижения: "
        f"+{total_reward_xp} XP\n"
    )


def open_achievement_popup():
    """
    Открывает popup со списком достижений,
    полученных за последнюю игру.
    """
    global current_popup
    global reset_popup_open

    if not newly_unlocked_achievements:
        return

    reset_popup_open = False

    # Каждый новый popup открывается с начала списка
    achievement_popup_scroll["offset"] = 0
    achievement_popup_scroll["scroll_velocity"] = 0
    achievement_popup_scroll["bar_alpha"] = 0
    achievement_popup_scroll["bar_timer"] = 0

    current_popup = POPUP_ACHIEVEMENTS

    layout = get_achievement_popup_layout()

    configure_achievement_popup_scroll(
        layout
    )


def close_achievement_popup():
    global current_popup

    current_popup = None

    achievement_popup_scroll["offset"] = 0
    achievement_popup_scroll["scroll_velocity"] = 0
    achievement_popup_scroll["bar_alpha"] = 0
    achievement_popup_scroll["bar_timer"] = 0
    achievement_popup_scroll["enabled"] = False


def draw_center_text(text, font_obj, color, y):
    rendered_text = font_obj.render(text, True, color)
    x = WIDTH // 2 - rendered_text.get_width() // 2
    screen.blit(rendered_text, (x, y))


def draw_text(text, font_obj, color, x, y):
    rendered_text = font_obj.render(text, True, color)
    screen.blit(rendered_text, (x, y))


def draw_wrapped_text(text, font_obj, color, x, y, max_width, line_gap=4):
    words = text.split(" ")
    lines = []
    current_line = ""

    for word in words:
        test_line = word if current_line == "" else current_line + " " + word
        test_surface = font_obj.render(test_line, True, color)

        if test_surface.get_width() <= max_width:
            current_line = test_line
        else:
            if current_line != "":
                lines.append(current_line)
                current_line = word
            else:
                lines.append(word)
                current_line = ""

    if current_line != "":
        lines.append(current_line)

    line_height = font_obj.get_height()

    for index, line in enumerate(lines):
        line_surface = font_obj.render(line, True, color)
        screen.blit(line_surface, (x, y + index * (line_height + line_gap)))


def draw_button(button, font_obj):
    rect = button["rect"]
    text = button["text"]
    color = button["color"]

    pygame.draw.rect(screen, color, rect, border_radius=20)

    button_text = font_obj.render(text, True, BLACK)
    text_x = rect.centerx - button_text.get_width() // 2
    text_y = rect.centery - button_text.get_height() // 2

    screen.blit(button_text, (text_x, text_y))


def draw_text_input(text_input):

    color = BLUE if text_input["active"] else LIGHT_GRAY

    pygame.draw.rect(
        screen,
        WHITE,
        text_input["rect"],
        border_radius=8
    )

    pygame.draw.rect(
        screen,
        color,
        text_input["rect"],
        2,
        border_radius=8
    )

    if text_input["text"]:

        text_surface = font.render(
            text_input["text"],
            True,
            BLACK
        )

    else:

        text_surface = font.render(
            text_input["placeholder"],
            True,
            PLACEHOLDER_COLOR
        )

    screen.blit(
        text_surface,
        (
            text_input["rect"].x + 12,
            text_input["rect"].y + 12
        )
    )

    if text_input["active"] and text_input["cursor_visible"]:
        if text_input["text"]:

            cursor_surface = font.render(
                text_input["text"],
                True,
                BLACK
            )

            cursor_x = (
                    text_input["rect"].x
                    + 12
                    + cursor_surface.get_width()
            )

        else:

            cursor_x = text_input["rect"].x + 12

        cursor_y = text_input["rect"].y + 10

        pygame.draw.line(
            screen,
            BLACK,
            (cursor_x, cursor_y),
            (cursor_x, cursor_y + 28),
            2
        )


def draw_developer_text_input(
    text_input,
    error_text=""
):
    """
    Рисует поле developer-панели.

    При наличии ошибки рамка становится красной.
    """
    if error_text:
        border_color = RED

    elif text_input["active"]:
        border_color = BLUE

    else:
        border_color = LIGHT_GRAY

    pygame.draw.rect(
        screen,
        WHITE,
        text_input["rect"],
        border_radius=10
    )

    pygame.draw.rect(
        screen,
        border_color,
        text_input["rect"],
        2,
        border_radius=10
    )

    if text_input["text"]:
        visible_text = text_input["text"]
        text_color = BLACK

    else:
        visible_text = text_input["placeholder"]
        text_color = PLACEHOLDER_COLOR

    text_surface = font.render(
        visible_text,
        True,
        text_color
    )

    text_rect = text_surface.get_rect(
        left=text_input["rect"].x + 14,
        centery=text_input["rect"].centery
    )

    screen.blit(
        text_surface,
        text_rect
    )

    if (
        text_input["active"]
        and text_input["cursor_visible"]
    ):
        if text_input["text"]:
            typed_surface = font.render(
                text_input["text"],
                True,
                BLACK
            )

            cursor_x = (
                text_input["rect"].x
                + 14
                + typed_surface.get_width()
            )

        else:
            cursor_x = (
                text_input["rect"].x + 14
            )

        cursor_y = (
            text_input["rect"].centery
            - font.get_height() // 2
        )

        pygame.draw.line(
            screen,
            BLACK,
            (
                cursor_x,
                cursor_y
            ),
            (
                cursor_x,
                cursor_y
                + font.get_height()
            ),
            2
        )


def update_text_input(text_input):
    if not text_input["active"]:
        text_input["cursor_visible"] = True
        return

    current_time = pygame.time.get_ticks()

    if current_time - text_input["cursor_timer"] >= 500:

        text_input["cursor_visible"] = not text_input["cursor_visible"]
        text_input["cursor_timer"] = current_time


def handle_text_input_click(text_input, mouse_pos):

    if text_input["rect"].collidepoint(mouse_pos):
        text_input["active"] = True

    else:
        text_input["active"] = False

    text_input["cursor_visible"] = True
    text_input["cursor_timer"] = pygame.time.get_ticks()


def copy_text_to_clipboard(text):
    """
    Копирует текст в системный буфер обмена macOS.
    """
    try:
        process = subprocess.run(
            ["/usr/bin/pbcopy"],
            input=text,
            text=True,
            check=True
        )

        return process.returncode == 0

    except (
        FileNotFoundError,
        subprocess.SubprocessError,
        OSError
    ) as error:
        if DEBUG_MODE:
            print(
                "CLIPBOARD COPY ERROR:",
                repr(error)
            )
        return False


def get_text_from_clipboard():
    """
    Получает текст из системного буфера обмена macOS.
    """
    try:
        result = subprocess.run(
            ["/usr/bin/pbpaste"],
            capture_output=True,
            text=True,
            check=True
        )

        clipboard_text = result.stdout

        # Наши поля однострочные
        clipboard_text = (
            clipboard_text
            .replace("\x00", "")
            .replace("\r", " ")
            .replace("\n", " ")
            .replace("\t", " ")
        )

        return clipboard_text

    except (
        FileNotFoundError,
        subprocess.SubprocessError,
        OSError
    ) as error:
        if DEBUG_MODE:
            print(
                "CLIPBOARD PASTE ERROR:",
                repr(error)
            )
        return ""


def handle_text_input_keyboard(
    text_input,
    event,
    command_pressed=False
):

    if not text_input["active"]:
        return

    if event.key == pygame.K_BACKSPACE:
        text_input["text"] = text_input["text"][:-1]
        return

    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        text_input["active"] = False
        return

    allowed_symbols = (

        "abcdefghijklmnopqrstuvwxyz"

        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"

        "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"

        "0123456789"

        " _-"

    )

    if event.unicode not in allowed_symbols:
        return

    if len(text_input["text"]) >= text_input["max_length"]:
        return

    text_input["text"] += event.unicode

def create_button(x, y, width, height, text, color):
    rect = pygame.Rect(x, y, width, height)

    return {
        "rect": rect,
        "text": text,
        "color": color
    }


def create_text_input(x, y, width, height, placeholder="", max_length=16):

    return {
        "rect": pygame.Rect(x, y, width, height),
        "text": "",
        "placeholder": placeholder,
        "active": False,
        "max_length": max_length,

        "cursor_visible": True,
        "cursor_timer": pygame.time.get_ticks(),
    }


# ==========================================================
#                    SCROLL SYSTEM
# ==========================================================
#
# Назначение:
# Универсальная система прокрутки для любых экранов игры.
#
# Используется в:
# • Профиле
# • Достижениях
# • Настройках
#
# Возможности:
# • Вертикальная прокрутка
# • Ограничение прокрутки
# • Полоса прокрутки
# • Поддержка мыши и тачпада
#
# ==========================================================


def create_scroll_area(x, y, width, height, content_height):
    """
    Создает новую область прокрутки.

    Параметры:
        x, y            - положение области
        width, height   - размер видимой части
        content_height  - полная высота содержимого

    Возвращает:
        dict - объект ScrollArea
    """

    return {

        # Видимая область
        "rect": pygame.Rect(x, y, width, height),

        # Область, в которой работает прокрутка
        "active_rect": pygame.Rect(0, 0, WIDTH, HEIGHT),

        # Смещение содержимого
        "offset": 0,

        # Высота всего содержимого
        "content_height": content_height,

        # Скорость прокрутки
        "scroll_speed": SCROLL_ACCELERATION,

        # Текущая скорость прокрутки
        "scroll_velocity": 0.0,

        # Коэффициент затухания
        "scroll_friction": SCROLL_FRICTION,

        # Включена ли прокрутка
        "enabled": True,

        # ---------- ScrollBar ----------

        # Ширина полосы прокрутки
        "bar_width": 8,

        # Отступ полосы от края области
        "bar_padding": 4,

        # Минимальная высота ползунка
        "min_thumb_height": 40,

        # Расположение полосы прокрутки
        "bar_x": WIDTH - 25,

        # Верхний отступ контейнера полосы
        "bar_top": 25,

        # Нижний отступ контейнера полосы
        "bar_bottom": 25,

        # ---------- ScrollBar Animation ----------

        # Прозрачность полосы
        "bar_alpha": 0,

        # Таймер видимости
        "bar_timer": 0,

        # Сколько кадров полоса остается видимой
        "bar_visible_time": 240,

        # Скорость исчезновения
        "bar_fade_speed": 1.8,
    }


def clamp_scroll(scroll_area):
    """
    Ограничивает прокрутку.

    Не позволяет пользователю прокрутить
    содержимое выше верхней или ниже нижней
    границы.
    """

    # Максимально возможная прокрутка
    max_scroll = max(
        0,
        scroll_area["content_height"] - scroll_area["rect"].height
    )

    # Ограничиваем значение offset
    scroll_area["offset"] = max(
        0,
        min(scroll_area["offset"], max_scroll)
    )


def handle_scroll(scroll_area, direction):
    """
    Изменяет положение прокрутки.

    Параметры:
        scroll_area - объект ScrollArea
        direction   - направление прокрутки
                      (-1 вверх, 1 вниз)
    """

    if not scroll_area["enabled"]:
        return

    scroll_area["scroll_velocity"] += (
            direction *
            scroll_area["scroll_speed"] *
            2
    )

    # Показываем ScrollBar
    scroll_area["bar_timer"] = scroll_area["bar_visible_time"]

    scroll_area["scroll_velocity"] = max(
        -SCROLL_MAX_SPEED,
        min(
            SCROLL_MAX_SPEED,
            scroll_area["scroll_velocity"]
        )
    )


def update_scroll(scroll_area):
    """
    Обновляет плавную прокрутку.

    Выполняется каждый кадр.
    """

    if abs(scroll_area["scroll_velocity"]) < 0.1:
        scroll_area["scroll_velocity"] = 0

     # Постепенно уменьшаем скорость
    scroll_area["scroll_velocity"] *= scroll_area["scroll_friction"]

    # Перемещаем содержимое
    scroll_area["offset"] += scroll_area["scroll_velocity"]

    # Ограничиваем прокрутку
    clamp_scroll(scroll_area)

    # Если дошли до верхней границы
    if scroll_area["offset"] <= 0 and scroll_area["scroll_velocity"] < 0:
        scroll_area["scroll_velocity"] = 0

    # Если дошли до нижней границы
    max_offset = max(
        0,
        scroll_area["content_height"] - scroll_area["rect"].height
    )

    if (
            scroll_area["offset"] >= max_offset
            and scroll_area["scroll_velocity"] > 0
    ):
        scroll_area["scroll_velocity"] = 0

    # ---------- Анимация ScrollBar ----------

    if scroll_area["bar_timer"] > 0:

        # Пока пользователь недавно скроллил,
        # уменьшаем таймер.
        scroll_area["bar_timer"] -= 1

        # Постепенно увеличиваем прозрачность.
        scroll_area["bar_alpha"] = min(
            255,
            scroll_area["bar_alpha"] + 20
        )

    else:

        # После окончания таймера
        # постепенно исчезаем.
        scroll_area["bar_alpha"] = max(
            0,
            scroll_area["bar_alpha"] - scroll_area["bar_fade_speed"]
        )


def handle_scroll_event(scroll_area, event):
    """
    Обрабатывает события прокрутки.

    Поддерживает:
    • колесико мыши
    • тачпад
    • клавиатуру (будет добавлена позже)
    """

    if not scroll_area["enabled"]:
        return

    # Текущее положение курсора
    mouse_pos = pygame.mouse.get_pos()

    # Если курсор находится вне рабочей области — ничего не делаем
    if not scroll_area["active_rect"].collidepoint(mouse_pos):
        return

    if event.type == pygame.MOUSEWHEEL:
        handle_scroll(scroll_area, -event.y)


def draw_scrollbar(scroll_area):
    """
    Отрисовывает полосу прокрутки.

    Полоса автоматически скрывается,
    если весь контент помещается
    в видимую область.
    """

    # Если весь контент помещается,
    # полоса прокрутки не нужна.
    if scroll_area["content_height"] <= scroll_area["rect"].height:
        return

    # Высота контейнера полосы прокрутки
    track_height = (
            HEIGHT
            - scroll_area["bar_top"]
            - scroll_area["bar_bottom"]
    )

    thumb_height = (
            track_height
            * track_height
            / scroll_area["content_height"]
    )

    thumb_height = max(
        scroll_area["min_thumb_height"],
        thumb_height
    )

    scroll_progress = (
            scroll_area["offset"]
            /
            (
                    scroll_area["content_height"]
                    - scroll_area["rect"].height
            )
    )

    thumb_y = (
            scroll_area["bar_top"]
            +
            scroll_progress
            *
            (
                    track_height
                    - thumb_height
            )
    )

    track_rect = pygame.Rect(
        scroll_area["bar_x"],
        scroll_area["bar_top"],
        scroll_area["bar_width"],
        track_height
    )

    thumb_rect = pygame.Rect(
        track_rect.x,
        thumb_y,
        scroll_area["bar_width"],
        thumb_height
    )

    # Если ScrollBar полностью скрыт — не рисуем его
    if scroll_area["bar_alpha"] <= 0:
        return

    draw_fade_rect(
        screen,
        LIGHT_GRAY,
        track_rect,
        scroll_area["bar_alpha"],
        border_radius=5
    )

    draw_fade_rect(
        screen,
        GRAY,
        thumb_rect,
        scroll_area["bar_alpha"],
        border_radius=5
    )


def draw_fade_rect(surface, color, rect, alpha, border_radius=0):
    """
    Рисует прямоугольник с прозрачностью.

    Используется для ScrollBar и будущих UI-анимаций.
    """

    temp_surface = pygame.Surface(
        (rect.width, rect.height),
        pygame.SRCALPHA
    )

    pygame.draw.rect(
        temp_surface,
        color,
        temp_surface.get_rect(),
        border_radius=border_radius
    )

    temp_surface.set_alpha(alpha)

    surface.blit(
        temp_surface,
        rect.topleft
    )


name_input = create_text_input(
    WIDTH // 2 - 200,
    700,
    400,
    50,
    "Введите имя"
)

developer_grant_input = create_text_input(
    0,
    0,
    520,
    52,
    placeholder="Введите ID достижения",
    max_length=50
)

developer_reset_input = create_text_input(
    0,
    0,
    520,
    52,
    placeholder="Введите ID достижения",
    max_length=50
)

def save_progress():

    completed_achievements = {}

    for category in ACHIEVEMENTS_DATA.values():
        for achievement in category:
            completed_achievements[achievement["id"]] = achievement.get(
                "completed",
                False
            )

    data = {
        "score": score,
        "highest_balance": highest_balance,
        "games_played": games_played,
        "wins": wins,
        "losses": losses,
        "current_streak": current_streak,
        "best_streak": best_streak,
        "total_attempts_in_wins": total_attempts_in_wins,
        "tracked_wins_for_attempts": tracked_wins_for_attempts,
        "games_with_bet": games_with_bet,
        "all_in_bets_count": all_in_bets_count,
        "selected_bet": selected_bet,
        "total_xp": total_xp,
        "player_name": player_name,
        "completed_achievements": completed_achievements,
        "achievement_stats": achievement_stats,
    }

    save_path = Path(SAVE_FILE)
    temp_path = save_path.with_name(
        f"{save_path.name}.tmp"
    )

    save_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    try:
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=4
            )
            file.flush()
            os.fsync(file.fileno())

        temp_path.replace(save_path)

    finally:
        if temp_path.exists():
            temp_path.unlink()


def add_xp(victory, difficulty_name, streak):
    global total_xp, last_xp_gained
    old_level = get_player_level()

    xp = 0

    if victory:
        if difficulty_name == "Лёгкая":
            xp = 8
        elif difficulty_name == "Средняя":
            xp = 12
        elif difficulty_name == "Сложная":
            xp = 18
    else:
        xp = 2

    # Бонус за серию побед
    if streak >= 10:
        xp += 20
    elif streak >= 5:
        xp += 10
    elif streak >= 3:
        xp += 5

    total_xp += xp

    new_level = get_player_level()

    if new_level > old_level:
        level_up(new_level)

    last_xp_gained = xp

    save_progress()


def get_player_level():
    level = 0

    while total_xp >= get_level_required_xp(level + 1):
        level += 1

    return level


def get_level_required_xp(level):
    if level <= 0:
        return 0

    return 50 * level * (level + 1) // 2


def get_current_level_progress():
    level = get_player_level()

    next_level_xp = get_level_required_xp(level + 1)

    return total_xp, next_level_xp


def get_xp_to_next_level():
    level = get_player_level()

    return get_level_required_xp(level + 1) - total_xp


def level_up(new_level):
    if DEBUG_MODE:
        print(f"LEVEL UP -> {new_level}")

    global level_up_message
    global level_up_timer
    global level_up_alpha

    level_up_message = f"🎉 НОВЫЙ УРОВЕНЬ!\nУровень {new_level}"
    level_up_timer = 600
    level_up_alpha = 255


def move_invalid_save_aside():
    """Сохраняет повреждённый JSON рядом с новым файлом прогресса."""
    save_path = Path(SAVE_FILE)

    if not save_path.exists():
        return None

    backup_path = save_path.with_name(
        f"{save_path.name}.corrupt"
    )
    backup_index = 1

    while backup_path.exists():
        backup_path = save_path.with_name(
            f"{save_path.name}.corrupt.{backup_index}"
        )
        backup_index += 1

    save_path.replace(backup_path)
    return backup_path


def get_saved_int(data, key, default=0):
    value = data.get(key, default)

    if isinstance(value, bool) or not isinstance(value, int):
        return default

    return max(0, value)


def load_progress():
    global score, games_played, wins, losses, total_xp
    global current_streak, best_streak, selected_bet, current_bet
    global level_up_message, level_up_timer, level_up_alpha
    global player_name
    global highest_balance
    global total_attempts_in_wins, tracked_wins_for_attempts
    global games_with_bet, all_in_bets_count

    try:
        with Path(SAVE_FILE).open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Save root must be a JSON object")

        score = get_saved_int(data, "score")
        highest_balance = get_saved_int(data, "highest_balance")
        games_played = get_saved_int(data, "games_played")
        wins = get_saved_int(data, "wins")
        losses = get_saved_int(data, "losses")
        total_xp = get_saved_int(data, "total_xp")
        level_up_message = ""
        level_up_timer = 0
        level_up_alpha = 255
        current_streak = get_saved_int(data, "current_streak")
        best_streak = get_saved_int(data, "best_streak")
        total_attempts_in_wins = get_saved_int(
            data,
            "total_attempts_in_wins"
        )
        tracked_wins_for_attempts = get_saved_int(
            data,
            "tracked_wins_for_attempts"
        )
        games_with_bet = get_saved_int(data, "games_with_bet")
        all_in_bets_count = get_saved_int(data, "all_in_bets_count")
        selected_bet = get_saved_int(data, "selected_bet")

        saved_player_name = data.get("player_name", "Player")
        player_name = (
            saved_player_name
            if isinstance(saved_player_name, str)
            else "Player"
        )

        completed_achievements = data.get("completed_achievements", {})
        saved_achievement_stats = data.get("achievement_stats", {})

        if not isinstance(completed_achievements, dict):
            completed_achievements = {}

        if isinstance(saved_achievement_stats, dict):
            for stat_key in achievement_stats:
                saved_value = saved_achievement_stats.get(stat_key)

                if (
                        isinstance(saved_value, int)
                        and not isinstance(saved_value, bool)
                ):
                    achievement_stats[stat_key] = max(0, saved_value)

        for category in ACHIEVEMENTS_DATA.values():

            for achievement in category:
                achievement["completed"] = (
                    completed_achievements.get(
                        achievement["id"]
                    ) is True
                )

        if selected_bet > score:
            selected_bet = 0

        current_bet = selected_bet

    except FileNotFoundError:
        return

    except (json.JSONDecodeError, ValueError, TypeError):
        backup_path = move_invalid_save_aside()

        if DEBUG_MODE and backup_path is not None:
            print(
                "Повреждённое сохранение перемещено:",
                backup_path
            )

    except OSError as error:
        if DEBUG_MODE:
            print("Не удалось загрузить сохранение:", error)


def reset_progress():
    global score, games_played, wins, losses
    global current_streak, best_streak
    global selected_bet, current_bet
    global custom_bet_text, custom_bet_error, custom_bet_active
    global reset_popup_open
    global total_xp
    global level_up_message
    global level_up_timer
    global level_up_alpha
    global highest_balance
    global total_attempts_in_wins, tracked_wins_for_attempts
    global games_with_bet, all_in_bets_count

    score = 0
    highest_balance = 0
    games_played = 0
    wins = 0
    losses = 0
    current_streak = 0
    best_streak = 0

    total_attempts_in_wins = 0
    tracked_wins_for_attempts = 0

    games_with_bet = 0
    all_in_bets_count = 0

    total_xp = 0

    level_up_message = ""
    level_up_timer = 0
    level_up_alpha = 255

    selected_bet = 0
    current_bet = 0

    custom_bet_text = ""
    custom_bet_error = ""
    custom_bet_active = False

    reset_popup_open = False

    for category in ACHIEVEMENTS_DATA.values():

        for achievement in category:
            achievement["completed"] = False

    for key in achievement_stats:
        achievement_stats[key] = 0

    save_progress()


def get_menu_buttons():
    button_width = 320
    button_height = 65
    button_gap = 20

    button_data = [
        ("Играть", BLUE),
        ("Профиль", LIGHT_GRAY),
        ("Достижения", LIGHT_GRAY),
        ("Настройки", LIGHT_GRAY),
    ]

    if DEVELOPER_MODE:
        button_data.append(
            ("Developer-панель", YELLOW)
        )

    button_data.append(
        ("Выход", RED)
    )

    buttons_count = len(button_data)

    total_height = (
        buttons_count * button_height
        + (buttons_count - 1) * button_gap
    )

    start_x = (
        WIDTH // 2
        - button_width // 2
    )

    start_y = (
        HEIGHT // 2
        - total_height // 2
        + 40
    )

    buttons = []

    for index, (text, color) in enumerate(
        button_data
    ):
        button_y = (
            start_y
            + index * (
                button_height
                + button_gap
            )
        )

        buttons.append(
            create_button(
                start_x,
                button_y,
                button_width,
                button_height,
                text,
                color
            )
        )

    return buttons


def get_back_to_menu_button():
    return create_button(30, 30, 120, 45, "Меню", GRAY)


def get_restart_button():
    button_width = 180
    button_height = 55

    return create_button(
        get_game_area_center_x() - button_width // 2,
        HEIGHT - 95,
        button_width,
        button_height,
        "Заново",
        GRAY
    )


def get_stats_panel_position():
    total_width = PANEL_WIDTH * 2 + PANEL_GAP

    panel_x = WIDTH - total_width - SIDEBAR_MARGIN
    panel_y = (HEIGHT - STATS_PANEL_HEIGHT) // 2

    if panel_y < SIDEBAR_MARGIN:
        panel_y = SIDEBAR_MARGIN

    return panel_x, panel_y, PANEL_WIDTH, STATS_PANEL_HEIGHT


def get_bet_panel_position():
    stats_x, stats_y, stats_width, stats_height = get_stats_panel_position()

    panel_x = stats_x + PANEL_WIDTH + PANEL_GAP
    panel_y = stats_y

    return panel_x, panel_y, PANEL_WIDTH, BET_PANEL_HEIGHT


def get_reset_button():
    panel_x, panel_y, panel_width, panel_height = get_stats_panel_position()

    button_width = 180
    button_height = 36
    button_x = panel_x + (panel_width - button_width) // 2
    button_y = panel_y + 412

    return create_button(button_x, button_y, button_width, button_height, "Сброс", WHITE)


def get_menu_stats_panel_position():
    panel_width = 300
    panel_height = 340

    panel_x = WIDTH // 2 + 90
    panel_y = HEIGHT // 2 - panel_height // 2 + 70

    return panel_x, panel_y, panel_width, panel_height


def get_menu_reset_button():
    panel_x, panel_y, panel_width, panel_height = get_menu_stats_panel_position()

    button_width = 200
    button_height = 38

    button_x = panel_x + (panel_width - button_width) // 2
    button_y = panel_y + panel_height - button_height - 18

    return create_button(button_x, button_y, button_width, button_height, "Сброс статистики", WHITE)


def get_popup_rect():
    popup_width = 470
    popup_height = 230

    popup_x = WIDTH // 2 - popup_width // 2
    popup_y = HEIGHT // 2 - popup_height // 2

    return pygame.Rect(popup_x, popup_y, popup_width, popup_height)


def get_popup_cancel_button():
    popup_rect = get_popup_rect()

    button_width = 150
    button_height = 48

    button_x = popup_rect.x + 70
    button_y = popup_rect.bottom - 75

    return create_button(button_x, button_y, button_width, button_height, "Отмена", LIGHT_GRAY)


def get_popup_confirm_button():
    popup_rect = get_popup_rect()

    button_width = 150
    button_height = 48

    button_x = popup_rect.right - button_width - 70
    button_y = popup_rect.bottom - 75

    return create_button(button_x, button_y, button_width, button_height, "Сбросить", RED)


def get_game_area_right():
    panel_x, panel_y, panel_width, panel_height = get_stats_panel_position()
    return panel_x - 30


def get_game_area_center_x():
    game_area_left = 0
    game_area_right = get_game_area_right()
    return (game_area_left + game_area_right) // 2


def get_can_change_bet():
    return not game_started or game_over


def get_bet_buttons():
    panel_x, panel_y, panel_width, panel_height = get_bet_panel_position()

    button_width = 180
    button_height = 34
    button_gap = 7

    start_x = panel_x + (panel_width - button_width) // 2
    start_y = panel_y + 62

    buttons = []

    can_change_bet = get_can_change_bet()

    if selected_bet == 0:
        no_bet_color = ORANGE
    elif can_change_bet:
        no_bet_color = WHITE
    else:
        no_bet_color = GRAY

    no_bet_button = create_button(start_x, start_y, button_width, button_height, "Без ставки", no_bet_color)
    no_bet_button["bet"] = 0
    no_bet_button["active"] = can_change_bet
    buttons.append(no_bet_button)

    for index, bet in enumerate(bet_options):
        button_y = start_y + (index + 1) * (button_height + button_gap)

        if bet == selected_bet:
            color = ORANGE
        elif can_change_bet and bet <= score:
            color = WHITE
        else:
            color = GRAY

        button = create_button(start_x, button_y, button_width, button_height, str(bet), color)
        button["bet"] = bet
        button["active"] = can_change_bet and bet <= score

        buttons.append(button)

    return buttons


def get_custom_bet_input_rect():
    panel_x, panel_y, panel_width, panel_height = get_bet_panel_position()

    input_width = 115
    input_height = 40
    apply_button_width = 55
    gap_between = 10

    total_width = input_width + gap_between + apply_button_width

    input_x = panel_x + (panel_width - total_width) // 2
    input_y = panel_y + 312

    return pygame.Rect(input_x, input_y, input_width, input_height)


def get_custom_bet_apply_button():
    input_rect = get_custom_bet_input_rect()

    return create_button(
        input_rect.right + 10,
        input_rect.y,
        55,
        input_rect.height,
        "OK",
        LIGHT_GRAY
    )


def get_grid_area_top():
    return 295


def get_grid_area_bottom():
    return HEIGHT - 160


def get_points_multiplier():
    if difficulty_name == "Лёгкая":
        return 10

    if difficulty_name == "Средняя":
        return 15

    if difficulty_name == "Сложная":
        return 25

    return 10


def get_loss_penalty():
    if difficulty_name == "Лёгкая":
        return 10

    if difficulty_name == "Средняя":
        return 20

    if difficulty_name == "Сложная":
        return 35

    return 10


def get_streak_multiplier():
    if current_streak < 2:
        return 1.0

    if current_streak == 2:
        return 1.2

    if current_streak == 3:
        return 1.4

    if current_streak == 4:
        return 1.6

    return 2.0


def normalize_selected_bet():
    global selected_bet, current_bet

    if selected_bet > score:
        selected_bet = 0

    if not game_started or game_over:
        current_bet = selected_bet


def set_selected_bet(new_bet):
    global selected_bet, current_bet

    selected_bet = new_bet

    if not game_started and not game_over:
        current_bet = selected_bet

    save_progress()


def apply_custom_bet():
    global custom_bet_text, custom_bet_error

    if not get_can_change_bet():
        return

    if score <= 0:
        custom_bet_error = "Баланс 0, ставка недоступна"
        return

    if custom_bet_text == "":
        custom_bet_error = ""
        return

    custom_bet = int(custom_bet_text)

    if custom_bet <= score:
        set_selected_bet(custom_bet)
        custom_bet_text = ""
        custom_bet_error = ""
    else:
        custom_bet_error = f"Ставка не выше баланса: {score}"


def update_phoenix_achievement():
    """
    Обновляет этап скрытой ачивки "Феникс".

    Этапы:
    0 — ожидаем первый баланс 1000+
    1 — ожидаем падение до 10 или ниже
    2 — ожидаем возвращение к 1000+
    3 — ачивка выполнена
    """

    if achievement_stats["phoenix"]:
        return

    stage = achievement_stats["phoenix_stage"]

    # Первый раз достигли 1000 монет
    if stage == 0 and score >= 1000:
        achievement_stats["phoenix_stage"] = 1

    # После достижения 1000 опустились до 10 или ниже
    elif stage == 1 and score <= 10:
        achievement_stats["phoenix_stage"] = 2

    # После падения снова вернулись к 1000
    elif stage == 2 and score >= 1000:
        achievement_stats["phoenix_stage"] = 3
        achievement_stats["phoenix"] = 1


def finish_game(player_won):
    global score, games_played, wins, losses
    global current_streak, best_streak
    global highest_balance
    global balance_before_bet
    global achievement_stats
    global started_all_in
    global total_attempts_in_wins, tracked_wins_for_attempts
    global games_with_bet, all_in_bets_count

    games_played += 1

    # ---------- Bets ----------

    achievement_stats["total_bets"] += current_bet

    achievement_stats["max_bet"] = max(
        achievement_stats["max_bet"],
        current_bet
    )

    # Достижение требует сделать ставку всем балансом от 1000 монет.
    # Результат партии на выполнение этого условия не влияет.
    if started_all_in and balance_before_bet >= 1000:
        achievement_stats["all_in_1000"] = 1

    # ---------- Hidden: Unlucky ----------

    if achievement_stats["lose_streak"] < 5:

        if player_won:
            achievement_stats["lose_streak"] = 0

        else:
            achievement_stats["lose_streak"] = min(
                achievement_stats["lose_streak"] + 1,
                5
            )

    # ---------- Hidden: Perfect Balance ----------

    if achievement_stats["perfect_balance_progress"] < 10:

        current_result = 1 if player_won else -1
        last_result = achievement_stats["perfect_balance_last_result"]

        if last_result == 0:
            # Первая игра начинает последовательность
            achievement_stats["perfect_balance_progress"] = 1

        elif current_result != last_result:
            # Результат отличается от предыдущего — чередование продолжается
            achievement_stats["perfect_balance_progress"] = min(
                achievement_stats["perfect_balance_progress"] + 1,
                10
            )

        else:
            # Два одинаковых результата подряд:
            # текущая игра становится началом новой последовательности
            achievement_stats["perfect_balance_progress"] = 1

        achievement_stats["perfect_balance_last_result"] = current_result

        if achievement_stats["perfect_balance_progress"] >= 10:
            achievement_stats["perfect_balance"] = 1

    # ---------- Hidden: Trust Fate ----------

    if achievement_stats["trust_fate_streak"] < 3:

        trust_fate_game = (
                player_won
                and difficulty_name == "Сложная"
                and started_all_in
        )

        if trust_fate_game:
            achievement_stats["trust_fate_streak"] = min(
                achievement_stats["trust_fate_streak"] + 1,
                3
            )

        else:
            achievement_stats["trust_fate_streak"] = 0

        if achievement_stats["trust_fate_streak"] >= 3:
            achievement_stats["trust_fate"] = 1

    # ---------- Bet Profile Statistics ----------

    if current_bet > 0:
        games_with_bet += 1

    if started_all_in:
        all_in_bets_count += 1

    if player_won:
        wins += 1
        current_streak += 1
        add_xp(True, difficulty_name, current_streak)

        if current_streak > best_streak:
            best_streak = current_streak

        base_points = attempts_left * get_points_multiplier()
        streak_multiplier = get_streak_multiplier()
        earned_points = int(base_points * streak_multiplier)

        current_attempt = max_attempts - attempts_left + 1

        total_attempts_in_wins += current_attempt
        tracked_wins_for_attempts += 1

        bet_bonus = current_bet * 2
        total_earned = earned_points + bet_bonus

        score += total_earned

        # ---------- All In ----------

        if started_all_in:
            # Специальная ачивка "Ва-банк":
            # весь баланс при балансе от 5000 монет и победа.
            if balance_before_bet >= 5000:
                achievement_stats["all_in_win"] = 1

        # ---------- Absolute Risk ----------

        if (
                started_all_in
                and difficulty_name == "Средняя"
        ):
            if not achievement_stats["absolute_risk"]:

                achievement_stats["absolute_risk_progress"] += 1

                if achievement_stats["absolute_risk_progress"] >= 3:
                    achievement_stats["absolute_risk"] = 1

        else:
            if not achievement_stats["absolute_risk"]:
                achievement_stats["absolute_risk_progress"] = 0

        # ---------- First Try ----------

        if attempts_left == max_attempts:
            achievement_stats["first_try_win"] += 1

        # ---------- Hidden: Everything Possible ----------

        if current_attempt == 1:

            if difficulty_name == "Лёгкая":
                achievement_stats["everything_possible_easy"] = 1

            elif difficulty_name == "Средняя":
                achievement_stats["everything_possible_medium"] = 1

            elif difficulty_name == "Сложная":
                achievement_stats["everything_possible_hard"] = 1

            if (
                    achievement_stats["everything_possible_easy"] == 1
                    and achievement_stats["everything_possible_medium"] == 1
                    and achievement_stats["everything_possible_hard"] == 1
            ):
                achievement_stats["everything_possible"] = 1

        # ---------- Big Win ----------

        if total_earned > BIG_WIN_POINTS:
            achievement_stats["big_win"] = 1

        # ---------- Last Chance ----------

        if (
                started_all_in
                and current_attempt == max_attempts
        ):
            achievement_stats["last_chance_win"] = 1

        # ---------- No Bet Streak ----------

        if current_bet == 0:

            achievement_stats["no_bet_streak_progress"] += 1

            if achievement_stats["no_bet_streak_progress"] >= 10:
                achievement_stats["no_bet_streak"] = 1

        else:

            achievement_stats["no_bet_streak_progress"] = 0


        highest_balance = max(
            highest_balance,
            score
        )

        update_phoenix_achievement()

        save_progress()

        return {
            "total": total_earned,
            "base_points": base_points,
            "streak_multiplier": streak_multiplier,
            "earned_points": earned_points,
            "bet_bonus": bet_bonus
        }

    losses += 1
    current_streak = 0

    # ---------- No Bet Streak ----------

    achievement_stats["no_bet_streak_progress"] = 0

    # ---------- Absolute Risk ----------

    if not achievement_stats["absolute_risk"]:
        achievement_stats["absolute_risk_progress"] = 0

    add_xp(False, difficulty_name, 0)

    base_penalty = get_loss_penalty()
    bet_penalty = current_bet
    total_penalty = base_penalty + bet_penalty

    score -= total_penalty

    if score < 0:
        score = 0

    highest_balance = max(highest_balance, score)

    update_phoenix_achievement()

    normalize_selected_bet()
    save_progress()

    return {
        "total": total_penalty,
        "base_penalty": base_penalty,
        "bet_penalty": bet_penalty
    }


def get_tile_rect(tile_index):
    rows = math.ceil(max_number / columns)

    total_width = columns * TILE_SIZE + (columns - 1) * TILE_GAP
    total_height = rows * TILE_SIZE + (rows - 1) * TILE_GAP

    start_x = get_game_area_center_x() - total_width // 2

    grid_area_top = get_grid_area_top()
    grid_area_bottom = get_grid_area_bottom()
    available_grid_height = grid_area_bottom - grid_area_top

    start_y = grid_area_top + (available_grid_height - total_height) // 2

    row = tile_index // columns
    col = tile_index % columns

    tile_x = start_x + col * (TILE_SIZE + TILE_GAP)
    tile_y = start_y + row * (TILE_SIZE + TILE_GAP)

    return pygame.Rect(tile_x, tile_y, TILE_SIZE, TILE_SIZE)


def create_tiles():
    new_tiles = []

    for i in range(max_number):
        tile_rect = get_tile_rect(i)
        tile_number = i + 1

        new_tile = {
            "rect": tile_rect,
            "number": tile_number,
            "color": BLUE,
            "active": True
        }

        new_tiles.append(new_tile)

    return new_tiles


def update_tile_positions():
    for tile in tiles:
        tile_index = tile["number"] - 1
        tile["rect"] = get_tile_rect(tile_index)


def start_new_game():
    global current_bet, game_started
    global result_line_1, result_line_2
    global achievement_stats
    global balance_before_bet
    global started_all_in
    global newly_unlocked_achievements

    current_bet = selected_bet
    game_started = False

    balance_before_bet = 0
    started_all_in = False

    newly_unlocked_achievements.clear()

    result_line_1 = ""
    result_line_2 = ""

    new_secret_number = random.randint(min_number, max_number)

    if DEBUG_MODE:
        print(f"🎲 Загаданное число: {new_secret_number}")

    new_attempts_left = max_attempts
    new_game_over = False
    new_win = False
    new_message = "Выбери число"

    new_tiles = create_tiles()

    return (
        new_secret_number,
        new_attempts_left,
        new_game_over,
        new_win,
        new_message,
        new_tiles
    )


def set_difficulty(name):
    global max_number, max_attempts, difficulty_name
    global secret_number, attempts_left, game_over, win, message, tiles
    global current_screen, columns

    difficulty_name = name

    if name == "Лёгкая":
        max_number = 10
        max_attempts = 3
        columns = 5

    elif name == "Средняя":
        max_number = 25
        max_attempts = 5
        columns = 5

    elif name == "Сложная":
        max_number = 50
        max_attempts = 6
        columns = 10

    secret_number, attempts_left, game_over, win, message, tiles = start_new_game()
    current_screen = GAME


def draw_stats_panel():
    panel_x, panel_y, panel_width, panel_height = get_stats_panel_position()

    current_xp, max_xp = get_current_level_progress()

    panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
    pygame.draw.rect(screen, LIGHT_GRAY, panel_rect, border_radius=14)

    # Заголовок
    draw_text("Статистика", small_font, BLACK, panel_x + 22, panel_y + 20)

    # ===== Экономика =====
    draw_text(f"Очки: {score}", small_font, DARK_GRAY, panel_x + 22, panel_y + 70)
    # Уровень
    draw_text(f"Уровень: {get_player_level()}", small_font, DARK_GRAY, panel_x + 22, panel_y + 120)
    # XP
    draw_text("XP", small_font, DARK_GRAY, panel_x + 22, panel_y + 170)

    # Сам прогресс XP
    draw_text(
        f"{current_xp} / {max_xp}",
        small_font,
        BLACK,
        panel_x + 22,
        panel_y + 205
    )

    draw_xp_bar(
        panel_x + 22,
        panel_y + 240,
        panel_width - 44,
        18
    )
    #draw_text(f"Ставка: {selected_bet}", small_font, DARK_GRAY, panel_x + 22, panel_y + 128)
    #draw_text(f"Множитель: x{get_streak_multiplier():.1f}", small_font, DARK_GRAY, panel_x + 22, panel_y + 164)

    # Разделитель
    pygame.draw.line(
        screen,
        (190, 190, 190),
        (panel_x + 18, panel_y + 280),
        (panel_x + panel_width - 18, panel_y + 280),
        2
    )

    # ===== Игровая статистика =====
    #draw_text(f"Игры: {games_played}", small_font, DARK_GRAY, panel_x + 22, panel_y + 222)
    #draw_text(f"Победы: {wins}", small_font, DARK_GRAY, panel_x + 22, panel_y + 258)
    #draw_text(f"Поражения: {losses}", small_font, DARK_GRAY, panel_x + 22, panel_y + 294)
    draw_text(f"Серия: {current_streak}", small_font, DARK_GRAY, panel_x + 22, panel_y + 305)
    draw_text(f"Лучшая серия: {best_streak}", small_font, DARK_GRAY, panel_x + 22, panel_y + 355)

    # Разделитель
    pygame.draw.line(
        screen,
        (190, 190, 190),
        (panel_x + 18, panel_y + 402),
        (panel_x + panel_width - 18, panel_y + 402),
        2
    )

    reset_button = get_reset_button()
    draw_button(reset_button, small_font)


def draw_xp_bar(x, y, width, height):
    current_xp, max_xp = get_current_level_progress()

    progress = current_xp / max_xp if max_xp > 0 else 0

    # Фон
    pygame.draw.rect(
        screen,
        (205, 205, 205),
        (x, y, width, height),
        border_radius=8
    )

    # Заполнение
    pygame.draw.rect(
        screen,
        (100, 220, 130),
        (x, y, int(width * progress), height),
        border_radius=8
    )

    # Обводка
    pygame.draw.rect(
        screen,
        (150, 150, 150),
        (x, y, width, height),
        2,
        border_radius=8
    )


def draw_menu_stats_panel():
    panel_x, panel_y, panel_width, panel_height = get_menu_stats_panel_position()

    panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
    pygame.draw.rect(screen, LIGHT_GRAY, panel_rect, border_radius=14)

    title_text = small_font.render("Статистика", True, BLACK)
    title_x = panel_x + panel_width // 2 - title_text.get_width() // 2
    screen.blit(title_text, (title_x, panel_y + 18))

    draw_text(f"Очки: {score}", small_font, DARK_GRAY, panel_x + 35, panel_y + 60)
    draw_text(f"Множитель: x{get_streak_multiplier():.1f}", small_font, DARK_GRAY, panel_x + 35, panel_y + 92)
    draw_text(f"Игры: {games_played}", small_font, DARK_GRAY, panel_x + 35, panel_y + 124)
    draw_text(f"Победы: {wins}", small_font, DARK_GRAY, panel_x + 35, panel_y + 156)
    draw_text(f"Поражения: {losses}", small_font, DARK_GRAY, panel_x + 35, panel_y + 188)
    draw_text(f"Серия: {current_streak}", small_font, DARK_GRAY, panel_x + 35, panel_y + 220)
    draw_text(f"Лучшая серия: {best_streak}", small_font, DARK_GRAY, panel_x + 35, panel_y + 252)

    reset_button = get_menu_reset_button()
    draw_button(reset_button, small_font)


def draw_level_up_message():
    global level_up_timer
    global level_up_alpha

    if level_up_timer <= 0:
        return

    level_up_timer -= 1

    # Первые 180 кадров ничего не исчезает
    if level_up_timer > 180:
        level_up_alpha = 255
    else:
        level_up_alpha = int(255 * (level_up_timer / 180))

    lines = level_up_message.split("\n")

    y = 40

    for line in lines:
        text = big_font.render(line, True, (255, 215, 0))
        text.set_alpha(level_up_alpha)

        x = WIDTH // 2 - text.get_width() // 2

        screen.blit(text, (x, y))

        y += 50

def draw_custom_bet_input():
    panel_x, panel_y, panel_width, panel_height = get_bet_panel_position()

    label_y = panel_y + 278

    label_text = small_font.render("Своя ставка", True, BLACK)
    label_x = panel_x + panel_width // 2 - label_text.get_width() // 2
    screen.blit(label_text, (label_x, label_y))

    input_rect = get_custom_bet_input_rect()

    if get_can_change_bet() and score > 0:
        input_color = WHITE
    else:
        input_color = GRAY

    pygame.draw.rect(screen, input_color, input_rect, border_radius=10)

    if custom_bet_error != "":
        border_color = RED
        border_width = 3
    elif custom_bet_active:
        border_color = ORANGE
        border_width = 3
    else:
        border_color = DARK_GRAY
        border_width = 2

    pygame.draw.rect(screen, border_color, input_rect, width=border_width, border_radius=10)

    if custom_bet_text == "":
        visible_text = "0"
        text_color = DARK_GRAY
    else:
        visible_text = custom_bet_text
        text_color = BLACK

    input_text = small_font.render(visible_text, True, text_color)
    screen.blit(input_text, (input_rect.x + 12, input_rect.y + 8))

    apply_button = get_custom_bet_apply_button()

    if get_can_change_bet() and score > 0 and custom_bet_text != "":
        apply_button["color"] = WHITE
    else:
        apply_button["color"] = GRAY

    draw_button(apply_button, small_font)

    if custom_bet_error != "":
        error_x = panel_x + 22
        error_y = input_rect.bottom + 10
        error_max_width = panel_width - 44

        draw_wrapped_text(
            custom_bet_error,
            small_font,
            RED,
            error_x,
            error_y,
            error_max_width
        )


def draw_bet_panel():
    panel_x, panel_y, panel_width, panel_height = get_bet_panel_position()

    panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
    pygame.draw.rect(screen, LIGHT_GRAY, panel_rect, border_radius=14)

    if get_can_change_bet():
        title_text = small_font.render("Выбор ставки", True, BLACK)
    else:
        title_text = small_font.render("Ставка заблокирована", True, DARK_GRAY)

    title_x = panel_x + panel_width // 2 - title_text.get_width() // 2
    title_y = panel_y + 18
    screen.blit(title_text, (title_x, title_y))

    bet_buttons = get_bet_buttons()

    for button in bet_buttons:
        draw_button(button, small_font)

    pygame.draw.line(
        screen,
        (190, 190, 190),
        (panel_x + 18, panel_y + 260),
        (panel_x + panel_width - 18, panel_y + 260),
        2
    )

    draw_custom_bet_input()


def draw_reset_popup():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 120))
    screen.blit(overlay, (0, 0))

    popup_rect = get_popup_rect()
    pygame.draw.rect(screen, WHITE, popup_rect, border_radius=18)
    pygame.draw.rect(screen, DARK_GRAY, popup_rect, width=2, border_radius=18)

    title_text = font.render("Сброс статистики", True, BLACK)
    title_x = popup_rect.centerx - title_text.get_width() // 2
    screen.blit(title_text, (title_x, popup_rect.y + 35))

    warning_text = small_font.render("Точно стереть всю статистику?", True, DARK_GRAY)
    warning_x = popup_rect.centerx - warning_text.get_width() // 2
    screen.blit(warning_text, (warning_x, popup_rect.y + 95))

    cancel_button = get_popup_cancel_button()
    confirm_button = get_popup_confirm_button()

    draw_button(cancel_button, small_font)
    draw_button(confirm_button, small_font)


def draw_menu():
    screen.fill(WHITE)

    draw_center_text("Угадай число", big_font, BLACK, 110)

    subtitle = small_font.render(
        "Главное меню",
        True,
        DARK_GRAY
    )

    screen.blit(
        subtitle,
        (
            WIDTH // 2 - subtitle.get_width() // 2,
            190
        )
    )

    for button in get_menu_buttons():
        draw_button(button, font)


def draw_profile():
    global profile_back_button

    screen.fill(WHITE)

    # ======================================================
    #                  РАЗМЕРЫ ПРОФИЛЯ
    # ======================================================

    profile_width = min(
        PROFILE_CONTENT_WIDTH,
        WIDTH - PROFILE_CONTENT_SIDE_PADDING * 2
    )

    profile_left = WIDTH // 2 - profile_width // 2
    profile_right = profile_left + profile_width

    stats_label_x = (
        profile_left
        + PROFILE_STATS_SIDE_PADDING
    )

    stats_value_right = (
        profile_right
        - PROFILE_STATS_SIDE_PADDING
    )

    # Текущее смещение содержимого профиля
    scroll_y = profile_scroll["offset"]

    # Скролл работает только ниже фиксированного хедера
    profile_scroll["active_rect"] = pygame.Rect(
        0,
        PROFILE_HEADER_HEIGHT,
        WIDTH,
        HEIGHT - PROFILE_HEADER_HEIGHT
    )

    # Область, внутри которой можно рисовать
    # прокручиваемое содержимое
    profile_viewport = pygame.Rect(
        0,
        PROFILE_HEADER_HEIGHT,
        WIDTH,
        HEIGHT - PROFILE_HEADER_HEIGHT
    )

    screen.set_clip(profile_viewport)

    # ======================================================
    #                   АВАТАР И ИМЯ
    # ======================================================

    avatar_center = (
        WIDTH // 2,
        205 - scroll_y
    )

    pygame.draw.circle(
        screen,
        LIGHT_GRAY,
        avatar_center,
        75
    )

    pygame.draw.circle(
        screen,
        DARK_GRAY,
        avatar_center,
        75,
        2
    )

    name_surface = font.render(
        player_name,
        True,
        BLACK
    )

    player_title = get_player_title()

    title_surface = small_font.render(
        player_title.upper(),
        True,
        WHITE
    )

    title_width = (
        title_surface.get_width()
        + PROFILE_TITLE_PADDING_X * 2
    )

    group_width = (
        name_surface.get_width()
        + PROFILE_NAME_TITLE_GAP
        + title_width
    )

    group_start_x = (
        WIDTH // 2
        - group_width // 2
    )

    name_y = 300 - scroll_y

    screen.blit(
        name_surface,
        (
            group_start_x,
            name_y
        )
    )

    title_badge = pygame.Rect(
        (
            group_start_x
            + name_surface.get_width()
            + PROFILE_NAME_TITLE_GAP
        ),
        name_y - 1,
        title_width,
        PROFILE_TITLE_HEIGHT
    )

    pygame.draw.rect(
        screen,
        DARK_GRAY,
        title_badge,
        border_radius=PROFILE_TITLE_HEIGHT // 2
    )

    title_rect = title_surface.get_rect(
        center=title_badge.center
    )

    screen.blit(
        title_surface,
        title_rect
    )

    change_name_button = create_button(
        WIDTH // 2 - 115,
        345 - scroll_y,
        230,
        40,
        "Изменить имя",
        BLUE
    )

    draw_button(
        change_name_button,
        font
    )

    pygame.draw.line(
        screen,
        LIGHT_GRAY,
        (
            profile_left,
            400 - scroll_y
        ),
        (
            profile_right,
            400 - scroll_y
        ),
        2
    )

    # ======================================================
    #                 УРОВЕНЬ И ОПЫТ
    # ======================================================

    level = get_player_level()
    current_xp, max_xp = get_current_level_progress()

    draw_center_text(
        f"Уровень {level}",
        font,
        BLACK,
        420 - scroll_y
    )

    bar_width = 420
    bar_height = 22

    bar_x = (
        WIDTH // 2
        - bar_width // 2
    )

    bar_y = 460 - scroll_y

    pygame.draw.rect(
        screen,
        LIGHT_GRAY,
        (
            bar_x,
            bar_y,
            bar_width,
            bar_height
        ),
        border_radius=15
    )

    if max_xp > 0:
        fill_width = int(
            bar_width
            * current_xp
            / max_xp
        )
    else:
        fill_width = 0

    fill_width = max(
        0,
        min(fill_width, bar_width)
    )

    if fill_width > 0:
        pygame.draw.rect(
            screen,
            BLUE,
            (
                bar_x,
                bar_y,
                fill_width,
                bar_height
            ),
            border_radius=15
        )

    draw_center_text(
        f"{current_xp} / {max_xp} XP",
        small_font,
        DARK_GRAY,
        500 - scroll_y
    )

    xp_to_next = get_xp_to_next_level()

    draw_center_text(
        f"До следующего уровня: {xp_to_next} XP",
        small_font,
        DARK_GRAY,
        530 - scroll_y
    )

    # ======================================================
    #               ПРОГРЕСС ДОСТИЖЕНИЙ
    # ======================================================

    all_achievements = get_all_achievements()

    completed_achievements_count = sum(
        1
        for achievement in all_achievements
        if achievement.get("completed", False)
    )

    total_achievements_count = len(
        all_achievements
    )

    achievement_percent = (
        completed_achievements_count
        / total_achievements_count
        * 100
        if total_achievements_count > 0
        else 0
    )

    draw_center_text(
        (
            f"Достижения: "
            f"{completed_achievements_count} / "
            f"{total_achievements_count} "
            f"({achievement_percent:.0f}%)"
        ),
        small_font,
        DARK_GRAY,
        585 - scroll_y
    )

    pygame.draw.line(
        screen,
        LIGHT_GRAY,
        (
            profile_left,
            625 - scroll_y
        ),
        (
            profile_right,
            625 - scroll_y
        ),
        2
    )

    # ======================================================
    #                    СТАТИСТИКА
    # ======================================================

    draw_center_text(
        "Статистика",
        font,
        BLACK,
        650 - scroll_y
    )

    win_rate = (
        wins / games_played * 100
        if games_played > 0
        else 0
    )

    average_attempts = (
        total_attempts_in_wins
        / tracked_wins_for_attempts
        if tracked_wins_for_attempts > 0
        else 0
    )

    stats = [
        (
            "Текущий баланс",
            score
        ),
        (
            "Максимальный баланс",
            highest_balance
        ),
        (
            "Всего игр",
            games_played
        ),
        (
            "Победы",
            wins
        ),
        (
            "Поражения",
            losses
        ),
        (
            "Процент побед",
            f"{win_rate:.1f}%"
        ),
        (
            "Текущая серия",
            current_streak
        ),
        (
            "Лучшая серия",
            best_streak
        ),
        (
            "Среднее попыток за победу",
            f"{average_attempts:.2f}"
        ),
    ]

    y = 705 - scroll_y

    for title, value in stats:
        title_surface = font.render(
            title,
            True,
            DARK_GRAY
        )

        value_surface = font.render(
            str(value),
            True,
            BLACK
        )

        screen.blit(
            title_surface,
            (
                stats_label_x,
                y
            )
        )

        value_rect = value_surface.get_rect(
            right=stats_value_right,
            top=y
        )

        screen.blit(
            value_surface,
            value_rect
        )

        y += PROFILE_STAT_ROW_GAP

    # ======================================================
    #                СТАТИСТИКА СТАВОК
    # ======================================================

    y += PROFILE_SECTION_SPACING

    pygame.draw.line(
        screen,
        LIGHT_GRAY,
        (
            profile_left,
            y
        ),
        (
            profile_right,
            y
        ),
        2
    )

    y += 25

    draw_center_text(
        "Статистика ставок",
        font,
        BLACK,
        y
    )

    y += 55

    average_bet = (
        achievement_stats["total_bets"] / games_with_bet
        if games_with_bet > 0
        else 0
    )

    all_in_rate = (
        all_in_bets_count / games_with_bet * 100
        if games_with_bet > 0
        else 0
    )

    bet_stats = [
        (
            "Всего поставлено",
            achievement_stats["total_bets"]
        ),
        (
            "Максимальная ставка",
            achievement_stats["max_bet"]
        ),
        (
            "Игр со ставкой",
            games_with_bet
        ),
        (
            "Средняя ставка",
            f"{average_bet:.2f}"
        ),
        (
            "Ставок ва-банк",
            all_in_bets_count
        ),
        (
            "Процент ва-банков",
            f"{all_in_rate:.1f}%"
        ),
    ]

    for title, value in bet_stats:
        title_surface = font.render(
            title,
            True,
            DARK_GRAY
        )

        value_surface = font.render(
            str(value),
            True,
            BLACK
        )

        screen.blit(
            title_surface,
            (
                stats_label_x,
                y
            )
        )

        value_rect = value_surface.get_rect(
            right=stats_value_right,
            top=y
        )

        screen.blit(
            value_surface,
            value_rect
        )

        y += PROFILE_STAT_ROW_GAP

    # Прокручиваемое содержимое закончилось
    screen.set_clip(None)

    # ======================================================
    #                    СКРОЛЛБАР
    # ======================================================

    draw_scrollbar(profile_scroll)

    # ======================================================
    #                ФИКСИРОВАННЫЙ ХЕДЕР
    # ======================================================

    header_rect = pygame.Rect(
        0,
        0,
        WIDTH,
        PROFILE_HEADER_HEIGHT
    )

    pygame.draw.rect(
        screen,
        WHITE,
        header_rect
    )

    pygame.draw.line(
        screen,
        LIGHT_GRAY,
        (
            0,
            PROFILE_HEADER_HEIGHT - 1
        ),
        (
            WIDTH,
            PROFILE_HEADER_HEIGHT - 1
        ),
        2
    )

    draw_center_text(
        "Профиль",
        title_font,
        BLACK,
        35
    )

    profile_back_button = create_button(
        30,
        32,
        150,
        55,
        "Назад",
        LIGHT_GRAY
    )

    draw_button(
        profile_back_button,
        font
    )


# ---------- UI Components ----------

def draw_checkmark(x, y, color, size=CHECKMARK_SIZE):

    pygame.draw.line(
        screen,
        color,
        (x, y + size // 2),
        (x + size // 3, y + size),
        3
    )

    pygame.draw.line(
        screen,
        color,
        (x + size // 3, y + size),
        (x + size, y),
        3
    )


# ==========================================================
#                  ACHIEVEMENTS DATABASE
# ==========================================================

ACHIEVEMENTS_DATA = {

    # ======================================================
    #                        GAME
    # ======================================================

    "game": [

        {
            "id": "first_game",
            "title": "Первая игра",
            "description": "Сыграйте первую игру.",
            "stat": "games",
            "goal": 1,
            "reward_xp": 50,
            "rarity": "common"
        },

        {
            "id": "games_10",
            "title": "Новичок",
            "description": "Сыграйте 10 игр.",
            "stat": "games",
            "goal": 10,
            "reward_xp": 100,
            "rarity": "common"
        },

        {
            "id": "games_25",
            "title": "Не остановить",
            "description": "Сыграйте 25 игр.",
            "stat": "games",
            "goal": 25,
            "reward_xp": 175,
            "rarity": "rare"
        },

        {
            "id": "games_50",
            "title": "На опыте",
            "description": "Сыграйте 50 игр.",
            "stat": "games",
            "goal": 50,
            "reward_xp": 300,
            "rarity": "rare"
        },

        {
            "id": "games_100",
            "title": "Ветеран",
            "description": "Сыграйте 100 игр.",
            "stat": "games",
            "goal": 100,
            "reward_xp": 500,
            "rarity": "epic"
        },

        {
            "id": "games_250",
            "title": "Мастер плиток",
            "description": "Сыграйте 250 игр.",
            "stat": "games",
            "goal": 250,
            "reward_xp": 1000,
            "rarity": "epic"
        },

        {
            "id": "games_500",
            "title": "Чемпион плиток",
            "description": "Сыграйте 500 игр.",
            "stat": "games",
            "goal": 500,
            "reward_xp": 2000,
            "rarity": "legendary"
        },

        {
            "id": "games_1000",
            "title": "Легенда плиток",
            "description": "Сыграйте 1000 игр.",
            "stat": "games",
            "goal": 1000,
            "reward_xp": 5000,
            "rarity": "mythic"
        }

    ],

# ======================================================
#                        WINS
# ======================================================

    "wins": [

        {
            "id": "wins_1",
            "title": "Первая победа",
            "description": "Выиграйте первую игру.",
            "stat": "wins",
            "goal": 1,
            "reward_xp": 75,
            "rarity": "common"
        },

        {
            "id": "wins_10",
            "title": "Победитель",
            "description": "Выиграйте 10 игр.",
            "stat": "wins",
            "goal": 10,
            "reward_xp": 125,
            "rarity": "common"
        },

        {
            "id": "wins_25",
            "title": "На волне успеха",
            "description": "Выиграйте 25 игр.",
            "stat": "wins",
            "goal": 25,
            "reward_xp": 200,
            "rarity": "rare"
        },

        {
            "id": "wins_50",
            "title": "Профессионал",
            "description": "Выиграйте 50 игр.",
            "stat": "wins",
            "goal": 50,
            "reward_xp": 350,
            "rarity": "rare"
        },

        {
            "id": "wins_100",
            "title": "Мастер побед",
            "description": "Выиграйте 100 игр.",
            "stat": "wins",
            "goal": 100,
            "reward_xp": 600,
            "rarity": "epic"
        },

        {
            "id": "wins_250",
            "title": "Чемпион",
            "description": "Выиграйте 250 игр.",
            "stat": "wins",
            "goal": 250,
            "reward_xp": 1200,
            "rarity": "epic"
        },

        {
            "id": "wins_500",
            "title": "Непобедимый",
            "description": "Выиграйте 500 игр.",
            "stat": "wins",
            "goal": 500,
            "reward_xp": 2200,
            "rarity": "legendary"
        },

        {
            "id": "wins_1000",
            "title": "Абсолютный победитель",
            "description": "Выиграйте 1000 игр.",
            "stat": "wins",
            "goal": 1000,
            "reward_xp": 5000,
            "rarity": "mythic"
        }

    ],

# ======================================================
#                     STREAKS
# ======================================================

    "streaks": [

        {
            "id": "streak_3",
            "title": "На волне",
            "description": "Выиграйте 3 игры подряд.",
            "stat": "best_streak",
            "goal": 3,
            "reward_xp": 75,
            "rarity": "common"
        },

        {
            "id": "streak_5",
            "title": "Без поражений",
            "description": "Выиграйте 5 игр подряд.",
            "stat": "best_streak",
            "goal": 5,
            "reward_xp": 125,
            "rarity": "common"
        },

        {
            "id": "streak_10",
            "title": "Серия успеха",
            "description": "Выиграйте 10 игр подряд.",
            "stat": "best_streak",
            "goal": 10,
            "reward_xp": 200,
            "rarity": "rare"
        },

        {
            "id": "streak_25",
            "title": "Неудержимый",
            "description": "Выиграйте 25 игр подряд.",
            "stat": "best_streak",
            "goal": 25,
            "reward_xp": 350,
            "rarity": "rare"
        },

        {
            "id": "streak_50",
            "title": "Крепкий хват",
            "description": "Выиграйте 50 игр подряд.",
            "stat": "best_streak",
            "goal": 50,
            "reward_xp": 600,
            "rarity": "epic"
        },

        {
            "id": "streak_100",
            "title": "Живая легенда",
            "description": "Выиграйте 100 игр подряд.",
            "stat": "best_streak",
            "goal": 100,
            "reward_xp": 1200,
            "rarity": "legendary"
        },

        {
            "id": "streak_250",
            "title": "Абсолютное превосходство",
            "description": "Выиграйте 250 игр подряд.",
            "stat": "best_streak",
            "goal": 250,
            "reward_xp": 5000,
            "rarity": "mythic"
        }

    ],

# ======================================================
#                        BETS
# ======================================================

    "bets": [

        {
            "id": "bets_total_100",
            "title": "Первые ставки",
            "description": "Поставьте суммарно 100 монет.",
            "stat": "total_bets",
            "goal": 100,
            "reward_xp": 75,
            "rarity": "common"
        },

        {
            "id": "bets_single_50",
            "title": "Риск без риска",
            "description": "Поставьте 50 монет за одну игру.",
            "stat": "max_bet",
            "goal": 50,
            "reward_xp": 100,
            "rarity": "common"
        },

        {
            "id": "bets_total_1000",
            "title": "Любитель ставок",
            "description": "Поставьте суммарно 1000 монет.",
            "stat": "total_bets",
            "goal": 1000,
            "reward_xp": 125,
            "rarity": "common"
        },

        {
            "id": "bets_single_250",
            "title": "Идём на повышение",
            "description": "Поставьте 250 монет за одну игру.",
            "stat": "max_bet",
            "goal": 250,
            "reward_xp": 200,
            "rarity": "rare"
        },

        {
            "id": "bets_total_5000",
            "title": "Опытный ставочник",
            "description": "Поставьте суммарно 5000 монет.",
            "stat": "total_bets",
            "goal": 5000,
            "reward_xp": 300,
            "rarity": "rare"
        },

        {
            "id": "bets_all_in_1000",
            "title": "Рискованный ход",
            "description": "Поставьте весь баланс при балансе от 1000 монет.",
            "stat": "all_in_1000",
            "goal": 1,
            "reward_xp": 400,
            "rarity": "rare"
        },

        {
            "id": "bets_single_1000",
            "title": "Игра по крупному",
            "description": "Поставьте 1000 монет за одну игру.",
            "stat": "max_bet",
            "goal": 1000,
            "reward_xp": 600,
            "rarity": "epic"
        },

        {
            "id": "bets_total_25000",
            "title": "Крупный игрок",
            "description": "Поставьте суммарно 25000 монет.",
            "stat": "total_bets",
            "goal": 25000,
            "reward_xp": 800,
            "rarity": "epic"
        },

        {
            "id": "bets_single_5000",
            "title": "Без страха",
            "description": "Поставьте 5000 монет за одну игру.",
            "stat": "max_bet",
            "goal": 5000,
            "reward_xp": 1400,
            "rarity": "legendary"
        },

        {
            "id": "bets_total_50000",
            "title": "Ставочный король",
            "description": "Поставьте суммарно 50000 монет.",
            "stat": "total_bets",
            "goal": 50000,
            "reward_xp": 2000,
            "rarity": "legendary"
        },

        {
            "id": "bets_single_10000",
            "title": "Всё на кон",
            "description": "Поставьте 10000 монет за одну игру.",
            "stat": "max_bet",
            "goal": 10000,
            "reward_xp": 3500,
            "rarity": "mythic"
        },

        {
            "id": "bets_total_100000",
            "title": "Повелитель ставок",
            "description": "Поставьте суммарно 100000 монет.",
            "stat": "total_bets",
            "goal": 100000,
            "reward_xp": 5000,
            "rarity": "mythic"
        }

    ],

# ======================================================
#                      PROGRESS
# ======================================================

    "progress": [

        {
            "id": "level_5",
            "title": "Первые шаги",
            "description": "Достигните 5 уровня.",
            "stat": "level",
            "goal": 5,
            "reward_xp": 75,
            "rarity": "common",
            "player_title": "Новичок"
        },

        {
            "id": "xp_1000",
            "title": "Жажда знаний",
            "description": "Получите суммарно 1000 XP.",
            "stat": "total_xp",
            "goal": 1000,
            "reward_xp": 125,
            "rarity": "common"
        },

        {
            "id": "level_10",
            "title": "Опытный игрок",
            "description": "Достигните 10 уровня.",
            "stat": "level",
            "goal": 10,
            "reward_xp": 200,
            "rarity": "rare",
            "player_title": "Искатель чисел"
        },

        {
            "id": "xp_5000",
            "title": "В поисках совершенства",
            "description": "Получите суммарно 5000 XP.",
            "stat": "total_xp",
            "goal": 5000,
            "reward_xp": 350,
            "rarity": "rare"
        },

        {
            "id": "level_25",
            "title": "Профессор",
            "description": "Достигните 25 уровня.",
            "stat": "level",
            "goal": 25,
            "reward_xp": 600,
            "rarity": "epic",
            "player_title": "Знаток плиток"
        },

        {
            "id": "xp_25000",
            "title": "Источник опыта",
            "description": "Получите суммарно 25000 XP.",
            "stat": "total_xp",
            "goal": 25000,
            "reward_xp": 1000,
            "rarity": "epic"
        },

        {
            "id": "level_50",
            "title": "Мастер",
            "description": "Достигните 50 уровня.",
            "stat": "level",
            "goal": 50,
            "reward_xp": 2000,
            "rarity": "legendary",
            "player_title": "Повелитель чисел"
        },

        {
            "id": "xp_50000",
            "title": "Бесконечное развитие",
            "description": "Получите суммарно 50000 XP.",
            "stat": "total_xp",
            "goal": 50000,
            "reward_xp": 3000,
            "rarity": "legendary"
        },

        {
            "id": "level_100",
            "title": "Вершина мастерства",
            "description": "Достигните 100 уровня.",
            "stat": "level",
            "goal": 100,
            "reward_xp": 5000,
            "rarity": "mythic",
            "player_title": "Легенда чисел"
        },

        {
            "id": "xp_100000",
            "title": "Абсолютное развитие",
            "description": "Получите суммарно 100000 XP.",
            "stat": "total_xp",
            "goal": 100000,
            "reward_xp": 5000,
            "rarity": "mythic"
        }

    ],

# ======================================================
#                     SPECIAL
# ======================================================

    "special": [

        {
            "id": "first_try",
            "title": "Снайпер",
            "description": "Угадайте число с первой попытки 10 раз.",
            "stat": "first_try_win",
            "goal": 10,
            "reward_xp": 500,
            "rarity": "rare"
        },

        {
            "id": "big_win",
            "title": "Большой куш",
            "description": "Выиграйте за одну игру более 5000 очков.",
            "stat": "big_win",
            "goal": 1,
            "reward_xp": 1500,
            "rarity": "epic"
        },

        {
            "id": "streak_without_bets",
            "title": "Несокрушимый",
            "description": "Выиграйте 10 игр подряд без ставок.",
            "stat": "no_bet_streak",
            "progress_stat": "no_bet_streak_progress",
            "goal": 10,
            "reward_xp": 1800,
            "rarity": "legendary"
        },

        {
            "id": "all_in_win",
            "title": "Ва-банк",
            "description": "Поставьте весь баланс при балансе от 5000 монет и победите.",
            "stat": "all_in_win",
            "goal": 1,
            "reward_xp": 2000,
            "rarity": "legendary"
        },

        {
            "id": "last_chance",
            "title": "Последний шанс",
            "description": "Победите на последней попытке, поставив на кон всё.",
            "stat": "last_chance_win",
            "goal": 1,
            "reward_xp": 2500,
            "rarity": "legendary"
        },

        {
            "id": "absolute_risk",
            "title": "Абсолютный риск",
            "description": "Выиграйте 3 игры подряд на средней сложности, каждый раз ставя весь баланс.",
            "stat": "absolute_risk",
            "progress_stat": "absolute_risk_progress",
            "goal": 3,
            "reward_xp": 5000,
            "rarity": "mythic"
        }

    ],

# ======================================================
#                     HIDDEN
# ======================================================

    "hidden": [

        {
            "id": "trust_fate",
            "title": "Доверие судьбе",
            "description": "Выиграйте 3 игры подряд на сложной сложности, каждый раз ставя весь баланс.",
            "stat": "trust_fate",
            "goal": 1,
            "reward_xp": 5000,
            "type": "hidden"
        },

        {
            "id": "phoenix",
            "title": "Феникс",
            "description": "После 1000 монет опуститесь до 10 или ниже и снова вернитесь к 1000.",
            "stat": "phoenix",
            "goal": 1,
            "reward_xp": 4000,
            "type": "hidden"
        },

        {
            "id": "perfect_balance",
            "title": "Идеальный баланс",
            "description": "Чередуйте победы и поражения 10 игр подряд.",
            "stat": "perfect_balance",
            "goal": 1,
            "reward_xp": 3500,
            "type": "hidden"
        },

        {
            "id": "everything_possible",
            "title": "Всё возможно",
            "description": "Угадайте число с первой попытки на лёгкой, средней и сложной сложности.",
            "stat": "everything_possible",
            "goal": 1,
            "reward_xp": 3000,
            "type": "hidden"
        },

        {
            "id": "unlucky",
            "title": "Невезучий",
            "description": "Проиграйте 5 игр подряд.",
            "stat": "lose_streak",
            "goal": 5,
            "reward_xp": 1500,
            "type": "hidden"
        }

    ],

}


def initialize_achievement_states():
    """Гарантирует корректное состояние базы до любой загрузки/записи."""
    for achievement in get_all_achievements():
        achievement.setdefault("completed", False)


def get_all_achievements():
    """
    Возвращает единый список всех достижений.
    """

    all_achievements = []

    for category in ACHIEVEMENTS_DATA.values():
        all_achievements.extend(category)

    return all_achievements


def get_achievement_completion_counts():
    regular_achievements = [
        achievement
        for achievement in get_all_achievements()
        if achievement.get("type") != "hidden"
    ]
    hidden_achievements = [
        achievement
        for achievement in get_all_achievements()
        if achievement.get("type") == "hidden"
    ]

    regular_completed = sum(
        achievement.get("completed", False)
        for achievement in regular_achievements
    )
    hidden_completed = sum(
        achievement.get("completed", False)
        for achievement in hidden_achievements
    )

    return {
        "regular_completed": regular_completed,
        "regular_total": len(regular_achievements),
        "hidden_completed": hidden_completed,
        "hidden_total": len(hidden_achievements),
        "all_completed": regular_completed + hidden_completed,
        "all_total": len(regular_achievements) + len(hidden_achievements),
    }


def are_all_achievements_completed():
    """
    Проверяет, выполнены ли все достижения в игре.
    """

    all_achievements = get_all_achievements()

    if not all_achievements:
        return False

    return all(
        achievement.get("completed", False)
        for achievement in all_achievements
    )


def get_player_title():
    """
    Возвращает самый высокий разблокированный титул игрока.
    """

    if are_all_achievements_completed():
        return "Абсолютный коллекционер"

    title_levels = [
        ("level_100", "Легенда чисел"),
        ("level_50", "Повелитель чисел"),
        ("level_25", "Знаток плиток"),
        ("level_10", "Искатель чисел"),
        ("level_5", "Новичок"),
    ]

    completed_by_id = {
        achievement["id"]: achievement.get("completed", False)
        for achievement in get_all_achievements()
    }

    for achievement_id, player_title in title_levels:
        if completed_by_id.get(achievement_id, False):
            return player_title

    return "Без титула"


# ==========================================================
#                  ACHIEVEMENTS SCREEN
# ==========================================================

def get_achievement_counter_width(text):
    return (
        small_font.size(text)[0]
        + ACHIEVEMENT_COUNTER_PADDING_X * 2
    )


def draw_achievement_counter_badge(
    text,
    left,
    center_y,
    background_color,
    text_color
):
    counter_rect = pygame.Rect(
        left,
        center_y - ACHIEVEMENT_COUNTER_HEIGHT // 2,
        get_achievement_counter_width(text),
        ACHIEVEMENT_COUNTER_HEIGHT
    )

    pygame.draw.rect(
        screen,
        background_color,
        counter_rect,
        border_radius=ACHIEVEMENT_COUNTER_HEIGHT // 2
    )

    counter_surface = small_font.render(
        text,
        True,
        text_color
    )
    counter_text_rect = counter_surface.get_rect(
        center=counter_rect.center
    )
    screen.blit(counter_surface, counter_text_rect)

    return counter_rect


def draw_achievements_screen():
    # ---------- Background ----------
    screen.fill(WHITE)

    # ---------- Content ----------
    grid_width = (
            CARD_WIDTH * CARD_COLUMNS
            + CARD_COLUMN_SPACING * (CARD_COLUMNS - 1)
    )

    card_x = (WIDTH - grid_width) // 2

    scroll_y = achievement_scroll["offset"]

    achievement_scroll["active_rect"] = pygame.Rect(
        0,
        0,
        WIDTH,
        HEIGHT
    )

    card_y = (
            HEADER_HEIGHT
            + HEADER_BOTTOM_MARGIN
            - scroll_y
    )

    for category_name, category in ACHIEVEMENTS_DATA.items():

        all_category_achievements = category
        category_completed = sum(
            achievement.get("completed", False)
            for achievement in all_category_achievements
        )

        if category_name == "hidden":

            category = [
                achievement
                for achievement in all_category_achievements
                if achievement.get("completed", False)
            ]

            if not category:
                continue

        draw_category_header(
            card_y,
            ACHIEVEMENT_CATEGORIES[category_name]
        )

        card_y += CATEGORY_TITLE_HEIGHT + CATEGORY_HEADER_BOTTOM_MARGIN

        category_content_y = card_y

        card_y += CATEGORY_COUNTER_AREA_HEIGHT

        rows = (len(category) + CARD_COLUMNS - 1) // CARD_COLUMNS

        container_height = (
                CATEGORY_CONTAINER_PADDING_TOP
                + CATEGORY_CONTAINER_PADDING_BOTTOM
                + CATEGORY_COUNTER_AREA_HEIGHT
                + rows * CARD_HEIGHT
                + (rows - 1) * CARD_SPACING
        )

        container_rect = pygame.Rect(
            card_x - CATEGORY_CONTAINER_PADDING_LEFT,
            category_content_y - CATEGORY_CONTAINER_PADDING_TOP,
            grid_width
            + CATEGORY_CONTAINER_PADDING_LEFT
            + CATEGORY_CONTAINER_PADDING_RIGHT,
            container_height
        )

        pygame.draw.rect(
            screen,
            CATEGORY_CONTAINER_COLOR,
            container_rect,
            border_radius=CATEGORY_CONTAINER_RADIUS
        )

        category_counter_text = (
            f"Выполнено: {category_completed} / "
            f"{len(all_category_achievements)}"
        )
        category_counter_width = get_achievement_counter_width(
            category_counter_text
        )

        draw_achievement_counter_badge(
            category_counter_text,
            container_rect.right
            - CATEGORY_CONTAINER_PADDING_RIGHT
            - category_counter_width,
            category_content_y
            + CATEGORY_COUNTER_AREA_HEIGHT // 2,
            WHITE,
            DARK_GRAY
        )

        column = 0

        for achievement in category:

            current_x = card_x + (
                    CARD_WIDTH + CARD_COLUMN_SPACING
            ) * column

            draw_achievement_card(
                current_x,
                card_y,
                achievement
            )

            column += 1

            if column >= CARD_COLUMNS:
                column = 0

                card_y += CARD_HEIGHT + CARD_SPACING

        if column != 0:
            card_y += CARD_HEIGHT + CARD_SPACING

        card_y += CATEGORY_SPACING

    achievement_scroll["content_height"] = (
            card_y + scroll_y
    )

    draw_scrollbar(achievement_scroll)

    pygame.draw.rect(
        screen,
        HEADER_BACKGROUND,
        (
            0,
            0,
            WIDTH,
            HEADER_HEIGHT
        )
    )

    # ---------- Header ----------
    back_button = get_back_to_menu_button()
    draw_button(back_button, font)

    title_surface = title_font.render(
        "Достижения",
        True,
        BLACK
    )

    title_rect = title_surface.get_rect(
        center=(WIDTH // 2, HEADER_HEIGHT // 2)
    )

    screen.blit(
        title_surface,
        title_rect
    )

    completion_counts = get_achievement_completion_counts()

    if completion_counts["hidden_completed"] > 0:
        main_counter_text = (
            f"Получено: {completion_counts['all_completed']} / "
            f"{completion_counts['all_total']}"
        )
        hidden_counter_text = (
            f"Скрытые: {completion_counts['hidden_completed']} / "
            f"{completion_counts['hidden_total']}"
        )
    else:
        main_counter_text = (
            f"Получено: {completion_counts['regular_completed']} / "
            f"{completion_counts['regular_total']}"
        )
        hidden_counter_text = None

    counters_width = get_achievement_counter_width(
        main_counter_text
    )

    if hidden_counter_text is not None:
        counters_width += (
            ACHIEVEMENT_COUNTER_GAP
            + get_achievement_counter_width(hidden_counter_text)
        )

    counter_x = min(
        title_rect.right + 35,
        WIDTH - 30 - counters_width
    )

    main_counter_rect = draw_achievement_counter_badge(
        main_counter_text,
        counter_x,
        HEADER_HEIGHT // 2,
        LIGHT_GRAY,
        DARK_GRAY
    )

    if hidden_counter_text is not None:
        draw_achievement_counter_badge(
            hidden_counter_text,
            main_counter_rect.right + ACHIEVEMENT_COUNTER_GAP,
            HEADER_HEIGHT // 2,
            SECRET_BADGE_COLOR,
            WHITE
        )

    pygame.draw.line(
        screen,
        LIGHT_GRAY,
        (0, HEADER_HEIGHT),
        (WIDTH, HEADER_HEIGHT),
        HEADER_LINE_WIDTH
    )


def handle_achievements_click(mouse_pos):
    global current_screen

    back_button = get_back_to_menu_button()

    if back_button["rect"].collidepoint(mouse_pos):
        current_screen = MENU


# ==========================================================
#                  ACHIEVEMENT CARD
# ==========================================================

def draw_category_header(y, title):

    # ---------- Title ----------

    title_surface = font.render(
        title.upper(),
        True,
        BLACK
    )

    title_rect = title_surface.get_rect(
        center=(WIDTH // 2, y)
    )

    # ---------- Draw Title ----------

    screen.blit(
        title_surface,
        title_rect
    )

def draw_achievement_card(x, y, achievement):

    # ---------- Container ----------

    card_rect = pygame.Rect(
        x,
        y,
        CARD_WIDTH,
        CARD_HEIGHT
    )

    content_y = card_rect.centery - CONTENT_HEIGHT // 2

    card_color = WHITE

    if achievement.get("type") == "hidden":
        card_color = HIDDEN_CARD_COLOR

    pygame.draw.rect(
        screen,
        card_color,
        card_rect,
        border_radius=CARD_RADIUS
    )

    # ---------- Reward Badge ----------

    badge_gap = 8

    second_badge_text = None
    second_badge_color = None

    if achievement.get("type") == "hidden":
        second_badge_text = "SECRET"
        second_badge_color = SECRET_BADGE_COLOR

    elif achievement.get("player_title"):
        second_badge_text = achievement["player_title"].upper()
        second_badge_color = RARITY_COLORS[
            achievement["rarity"]
        ]

    second_badge_width = 0

    if second_badge_text:
        rendered_second_badge = small_font.render(
            second_badge_text,
            True,
            WHITE
        )

        second_badge_width = max(
            BADGE_WIDTH,
            rendered_second_badge.get_width() + 24
        )

    total_width = BADGE_WIDTH

    if second_badge_text:
        total_width += badge_gap + second_badge_width

    start_x = card_rect.centerx - total_width // 2

    badge_rect = pygame.Rect(
        0,
        0,
        BADGE_WIDTH,
        BADGE_HEIGHT
    )

    badge_rect.left = start_x
    badge_rect.centery = card_rect.top

    pygame.draw.rect(
        screen,
        (46, 204, 113),
        badge_rect,
        border_radius=BADGE_RADIUS
    )

    reward_surface = small_font.render(
        f"+{achievement['reward_xp']} XP",
        True,
        WHITE
    )

    reward_rect = reward_surface.get_rect(
        center=badge_rect.center
    )

    screen.blit(
        reward_surface,
        reward_rect
    )

    if second_badge_text:
        second_badge = pygame.Rect(
            0,
            0,
            second_badge_width,
            BADGE_HEIGHT
        )

        second_badge.left = badge_rect.right + badge_gap
        second_badge.centery = badge_rect.centery

        pygame.draw.rect(
            screen,
            second_badge_color,
            second_badge,
            border_radius=BADGE_RADIUS
        )

        second_badge_surface = small_font.render(
            second_badge_text,
            True,
            WHITE
        )

        second_badge_rect = second_badge_surface.get_rect(
            center=second_badge.center
        )

        screen.blit(
            second_badge_surface,
            second_badge_rect
        )

    # ---------- Icon ----------

    icon_x = x + ICON_X
    icon_y = content_y + ICON_Y

    pygame.draw.circle(
        screen,
        DARK_GRAY,
        (icon_x, icon_y),
        ICON_SIZE // 2
    )

    # ---------- Title ----------

    title = achievement["title"]

    title_color = BLACK
    description_color = DARK_GRAY

    if achievement.get("type") == "hidden":
        title_color = WHITE
        description_color = LIGHT_GRAY

    title_surface = font.render(
        achievement["title"],
        True,
        title_color
    )

    screen.blit(
        title_surface,
        (
            card_rect.left + TITLE_X,
            content_y + TITLE_Y
        )
    )

    # ---------- Progress ----------

    stats = get_player_stats()

    # Если у достижения есть отдельная статистика прогресса —
    # используем её.
    if "progress_stat" in achievement:
        progress = stats.get(
            achievement["progress_stat"],
            0
        )
    else:
        progress = stats.get(
            achievement["stat"],
            0
        )

    goal = achievement["goal"]

    # Статус завершения берём из самого достижения.
    # Это важно для ручной выдачи и отката
    # через developer-панель.
    completed = achievement.get(
        "completed",
        False
    )

    # Полученное достижение всегда визуально
    # показывает полностью заполненный прогресс.
    if completed:
        displayed_progress = goal
    else:
        displayed_progress = progress

    # ---------- Progress Text ----------

    progress_surface = small_font.render(
        f"{displayed_progress}/{goal}",
        True,
        DARK_GRAY
    )

    progress_rect = progress_surface.get_rect(
        midright=(
            card_rect.right - PROGRESS_TEXT_RIGHT,
            content_y + PROGRESS_TEXT_Y
        )
    )

    screen.blit(
        progress_surface,
        progress_rect
    )

    # ---------- Description ----------

    draw_wrapped_text(
        achievement["description"],
        small_font,
        description_color,
        x + DESCRIPTION_X,
        content_y + DESCRIPTION_Y,
        CARD_WIDTH
        - DESCRIPTION_X
        - CARD_RARITY_WIDTH
        - 20
    )

    # ---------- Progress Bar ----------

    bar_x = card_rect.left + PROGRESS_BAR_X
    bar_y = content_y + PROGRESS_BAR_Y

    bar_width = (
            CARD_WIDTH
            - PROGRESS_BAR_X
            - PROGRESS_BAR_RIGHT
    )
    bar_height = PROGRESS_BAR_HEIGHT

    progress_percent = min(
        displayed_progress / goal,
        1
    )

    fill_width = int(
        bar_width * progress_percent
    )

    pygame.draw.rect(
        screen,
        GRAY,
        (bar_x, bar_y, bar_width, bar_height),
        border_radius=5
    )

    progress_color = GREEN if completed else BLUE

    pygame.draw.rect(
        screen,
        progress_color,
        (bar_x, bar_y, fill_width, bar_height),
        border_radius=5
    )

    if completed:
        draw_checkmark(
            bar_x + bar_width + CHECKMARK_OFFSET,
            bar_y + CHECKMARK_Y_OFFSET,
            DARK_GRAY
        )

    # ---------- Rarity ----------

    if achievement.get("type") != "hidden":

        rarity_color = RARITY_COLORS[
            achievement["rarity"]
        ]

        rarity_width = CARD_RARITY_WIDTH

        rarity_rect = pygame.Rect(
            card_rect.right - rarity_width,
            card_rect.top,
            rarity_width,
            card_rect.height
        )

        pygame.draw.rect(
            screen,
            rarity_color,
            rarity_rect,
            border_top_right_radius=CARD_RADIUS,
            border_bottom_right_radius=CARD_RADIUS
        )


def get_achievement_popup_buttons(footer_rect):
    """
    Создаёт кнопки popup достижений.

    Ширина зависит от текста, а обе кнопки
    центрируются как единая группа.
    """
    close_text = "Закрыть"
    achievements_text = "К достижениям"

    close_text_width = font.size(close_text)[0]
    achievements_text_width = font.size(
        achievements_text
    )[0]

    close_width = max(
        ACHIEVEMENT_POPUP_BUTTON_MIN_WIDTH,
        close_text_width
        + ACHIEVEMENT_POPUP_BUTTON_PADDING_X * 2
    )

    achievements_width = max(
        ACHIEVEMENT_POPUP_BUTTON_MIN_WIDTH,
        achievements_text_width
        + ACHIEVEMENT_POPUP_BUTTON_PADDING_X * 2
    )

    group_width = (
        close_width
        + ACHIEVEMENT_POPUP_BUTTON_GAP
        + achievements_width
    )

    group_start_x = (
        footer_rect.centerx
        - group_width // 2
    )

    button_y = (
        footer_rect.centery
        - ACHIEVEMENT_POPUP_BUTTON_HEIGHT // 2
    )

    close_button = create_button(
        group_start_x,
        button_y,
        close_width,
        ACHIEVEMENT_POPUP_BUTTON_HEIGHT,
        close_text,
        LIGHT_GRAY
    )

    achievements_button = create_button(
        (
            group_start_x
            + close_width
            + ACHIEVEMENT_POPUP_BUTTON_GAP
        ),
        button_y,
        achievements_width,
        ACHIEVEMENT_POPUP_BUTTON_HEIGHT,
        achievements_text,
        BLUE
    )

    return close_button, achievements_button


def get_achievement_popup_summary():
    """
    Возвращает общую информацию о достижениях,
    открытых за последнюю игру.
    """
    achievements_count = len(
        newly_unlocked_achievements
    )

    total_reward_xp = sum(
        achievement["reward_xp"]
        for achievement in newly_unlocked_achievements
    )

    secret_count = sum(
        1
        for achievement in newly_unlocked_achievements
        if achievement.get("type") == "hidden"
    )

    title_achievements = [
        achievement
        for achievement in newly_unlocked_achievements
        if achievement.get("player_title")
    ]

    new_player_title = None

    if title_achievements:
        highest_title_achievement = max(
            title_achievements,
            key=lambda achievement: achievement.get(
                "goal",
                0
            )
        )

        new_player_title = highest_title_achievement[
            "player_title"
        ]

    # Финальный титул не привязан к отдельной
    # уровневой ачивке, поэтому проверяем его отдельно.
    if (
        newly_unlocked_achievements
        and are_all_achievements_completed()
    ):
        new_player_title = (
            "Абсолютный коллекционер"
        )

    return {
        "achievements_count": achievements_count,
        "total_reward_xp": total_reward_xp,
        "secret_count": secret_count,
        "new_player_title": new_player_title,
    }


def get_achievement_popup_layout():
    """
    Рассчитывает размеры popup достижений.
    """
    achievements_count = len(
        newly_unlocked_achievements
    )

    summary = get_achievement_popup_summary()

    header_height = ACHIEVEMENT_POPUP_HEADER_HEIGHT

    if summary["new_player_title"]:
        header_height += (
            ACHIEVEMENT_POPUP_TITLE_EXTRA_HEIGHT
        )

    cards_height = (
        achievements_count
        * ACHIEVEMENT_POPUP_CARD_HEIGHT
    )

    cards_gaps_height = (
        max(0, achievements_count - 1)
        * ACHIEVEMENT_POPUP_CARD_GAP
    )

    cards_content_height = (
        ACHIEVEMENT_POPUP_CARD_GAP
        + cards_height
        + cards_gaps_height
        + ACHIEVEMENT_POPUP_CARD_GAP
    )

    max_visible_cards = min(
        achievements_count,
        ACHIEVEMENT_POPUP_MAX_VISIBLE_CARDS
    )

    max_cards_visible_height = (
            ACHIEVEMENT_POPUP_CARD_GAP
            + max_visible_cards
            * ACHIEVEMENT_POPUP_CARD_HEIGHT
            + max(0, max_visible_cards - 1)
            * ACHIEVEMENT_POPUP_CARD_GAP
            + ACHIEVEMENT_POPUP_CARD_GAP
    )

    visible_cards_height = min(
        cards_content_height,
        max_cards_visible_height
    )

    popup_height = (
        header_height
        + visible_cards_height
        + ACHIEVEMENT_POPUP_FOOTER_HEIGHT
    )

    popup_height = max(
        popup_height,
        ACHIEVEMENT_POPUP_MIN_HEIGHT
    )

    popup_rect = pygame.Rect(
        WIDTH // 2
        - ACHIEVEMENT_POPUP_WIDTH // 2,
        HEIGHT // 2
        - popup_height // 2,
        ACHIEVEMENT_POPUP_WIDTH,
        popup_height
    )

    header_rect = pygame.Rect(
        popup_rect.x,
        popup_rect.y,
        popup_rect.width,
        header_height
    )

    footer_rect = pygame.Rect(
        popup_rect.x,
        popup_rect.bottom
        - ACHIEVEMENT_POPUP_FOOTER_HEIGHT,
        popup_rect.width,
        ACHIEVEMENT_POPUP_FOOTER_HEIGHT
    )

    cards_viewport = pygame.Rect(
        popup_rect.x,
        header_rect.bottom,
        popup_rect.width,
        footer_rect.top - header_rect.bottom
    )

    return {
        "popup_rect": popup_rect,
        "header_rect": header_rect,
        "footer_rect": footer_rect,
        "cards_viewport": cards_viewport,
        "cards_content_height": cards_content_height,
        "visible_cards_height": visible_cards_height,
        "summary": summary,
        "scroll_needed": (
                achievements_count
                > ACHIEVEMENT_POPUP_MAX_VISIBLE_CARDS
        ),
    }


def configure_achievement_popup_scroll(layout):
    """
    Настраивает универсальный ScrollArea
    под текущий popup достижений.
    """
    cards_viewport = layout["cards_viewport"]
    cards_content_height = layout["cards_content_height"]
    scroll_needed = layout["scroll_needed"]

    achievement_popup_scroll["rect"] = cards_viewport.copy()
    achievement_popup_scroll["active_rect"] = cards_viewport.copy()

    achievement_popup_scroll["content_height"] = (
        cards_content_height
    )

    achievement_popup_scroll["enabled"] = scroll_needed

    # Полоса находится внутри правой части popup
    achievement_popup_scroll["bar_x"] = (
        cards_viewport.right - 18
    )

    achievement_popup_scroll["bar_top"] = (
        cards_viewport.top
        + ACHIEVEMENT_POPUP_CARD_GAP
    )

    achievement_popup_scroll["bar_bottom"] = (
        HEIGHT
        - cards_viewport.bottom
        + ACHIEVEMENT_POPUP_CARD_GAP
    )

    # Если скролл не нужен, всегда держим список наверху
    if not scroll_needed:
        achievement_popup_scroll["offset"] = 0
        achievement_popup_scroll["scroll_velocity"] = 0
        achievement_popup_scroll["bar_alpha"] = 0
        achievement_popup_scroll["bar_timer"] = 0

    clamp_scroll(
        achievement_popup_scroll
    )


ACHIEVEMENT_POPUP_RARITY_ORDER = {
    "common": 0,
    "rare": 1,
    "epic": 2,
    "legendary": 3,
    "mythic": 4,
    "hidden": 5,
}


def get_sorted_unlocked_achievements():
    """
    Сортирует достижения для popup:

    1. По редкости:
       обычные, редкие, эпические,
       легендарные, мифические, скрытые.

    2. Внутри одной редкости сохраняет порядок,
       заданный в базе ACHIEVEMENTS_DATA.
    """

    achievement_database_order = {}

    database_index = 0

    for category_achievements in ACHIEVEMENTS_DATA.values():
        for achievement in category_achievements:
            achievement_database_order[
                achievement["id"]
            ] = database_index

            database_index += 1

    def get_sort_key(achievement):
        is_hidden = (
            achievement.get("type") == "hidden"
        )

        if is_hidden:
            rarity_order = (
                ACHIEVEMENT_POPUP_RARITY_ORDER[
                    "hidden"
                ]
            )
        else:
            rarity = achievement.get(
                "rarity",
                "common"
            )

            rarity_order = (
                ACHIEVEMENT_POPUP_RARITY_ORDER.get(
                    rarity,
                    0
                )
            )

        database_order = (
            achievement_database_order.get(
                achievement["id"],
                999999
            )
        )

        return (
            rarity_order,
            database_order
        )

    return sorted(
        newly_unlocked_achievements,
        key=get_sort_key
    )


def wrap_achievement_popup_text(
    text,
    text_font,
    max_width,
    max_lines=2
):
    """
    Разбивает описание на строки,
    не выходящие за ширину карточки.
    """
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = (
            f"{current_line} {word}".strip()
        )

        if text_font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)

            current_line = word

            if len(lines) >= max_lines:
                break

    if (
        current_line
        and len(lines) < max_lines
    ):
        lines.append(current_line)

    if len(lines) == max_lines:
        joined_text = " ".join(lines)

        if joined_text != text:
            last_line = lines[-1]

            while (
                last_line
                and text_font.size(
                    last_line + "..."
                )[0] > max_width
            ):
                last_line = last_line[:-1]

            lines[-1] = last_line.rstrip() + "..."

    return lines


def draw_achievement_popup_card(
    achievement,
    card_rect
):
    """
    Рисует завершённое достижение
    внутри popup уведомления.
    """
    is_hidden = (
        achievement.get("type") == "hidden"
    )

    if is_hidden:
        card_color = HIDDEN_CARD_COLOR
        title_color = WHITE
        description_color = (185, 185, 185)
        reward_color = WHITE
        rarity_color = SECRET_BADGE_COLOR
        rarity_text = "СЕКРЕТНОЕ"

    else:
        card_color = VERY_LIGHT_GRAY
        title_color = BLACK
        description_color = DARK_GRAY
        reward_color = (46, 160, 90)

        rarity = achievement.get(
            "rarity",
            "common"
        )

        rarity_color = RARITY_COLORS.get(
            rarity,
            DARK_GRAY
        )

        rarity_text = (
            ACHIEVEMENT_RARITY_NAMES.get(
                rarity,
                rarity.upper()
            )
        )

    rarity_strip_width = 8

    if is_hidden:
        pygame.draw.rect(
            screen,
            card_color,
            card_rect,
            border_radius=ACHIEVEMENT_POPUP_CARD_RADIUS
        )

        rarity_strip = pygame.Rect(
            card_rect.x + 1,
            card_rect.y + 1,
            rarity_strip_width,
            card_rect.height - 2
        )

        pygame.draw.rect(
            screen,
            rarity_color,
            rarity_strip,
            border_top_left_radius=ACHIEVEMENT_POPUP_CARD_RADIUS,
            border_bottom_left_radius=ACHIEVEMENT_POPUP_CARD_RADIUS
        )

        pygame.draw.rect(
            screen,
            card_color,
            card_rect,
            2,
            border_radius=ACHIEVEMENT_POPUP_CARD_RADIUS
        )

    else:
        # Для обычных карточек цветная подложка
        pygame.draw.rect(
            screen,
            rarity_color,
            card_rect,
            border_radius=ACHIEVEMENT_POPUP_CARD_RADIUS
        )

        # Светлый фон поверх со сдвигом вправо
        card_inner_rect = pygame.Rect(
            card_rect.x + rarity_strip_width,
            card_rect.y,
            card_rect.width - rarity_strip_width,
            card_rect.height
        )

        pygame.draw.rect(
            screen,
            card_color,
            card_inner_rect,
            border_top_right_radius=ACHIEVEMENT_POPUP_CARD_RADIUS,
            border_bottom_right_radius=ACHIEVEMENT_POPUP_CARD_RADIUS
        )

        # Обводка только у обычных достижений
        pygame.draw.rect(
            screen,
            rarity_color,
            card_rect,
            2,
            border_radius=ACHIEVEMENT_POPUP_CARD_RADIUS
        )

    content_left = (
        card_rect.x
        + ACHIEVEMENT_POPUP_CARD_PADDING_X
    )

    content_right = (
        card_rect.right
        - ACHIEVEMENT_POPUP_CARD_PADDING_X
    )

    # Название
    title_surface = font.render(
        achievement["title"],
        True,
        title_color
    )

    screen.blit(
        title_surface,
        (
            content_left,
            card_rect.y + 14
        )
    )

    # Описание
    description_max_width = (
        card_rect.width
        - ACHIEVEMENT_POPUP_CARD_PADDING_X * 2
        - 20
    )

    description_lines = (
        wrap_achievement_popup_text(
            achievement["description"],
            achievement_popup_description_font,
            description_max_width,
            max_lines=2
        )
    )

    description_y = card_rect.y + 52

    for line in description_lines:
        description_surface = (
            achievement_popup_description_font.render(
                line,
                True,
                description_color
            )
        )

        screen.blit(
            description_surface,
            (
                content_left,
                description_y
            )
        )

        description_y += 23

    # Редкость снизу слева
    rarity_surface = (
        achievement_popup_description_font.render(
            rarity_text,
            True,
            rarity_color
        )
    )

    rarity_rect = rarity_surface.get_rect(
        left=content_left,
        bottom=card_rect.bottom - 12
    )

    screen.blit(
        rarity_surface,
        rarity_rect
    )

    # Полученный XP снизу справа
    reward_surface = small_font.render(
        f"+{achievement['reward_xp']} XP",
        True,
        reward_color
    )

    reward_rect = reward_surface.get_rect(
        right=content_right,
        bottom=card_rect.bottom - 10
    )

    screen.blit(
        reward_surface,
        reward_rect
    )


def draw_achievement_unlock_popup():
    layout = get_achievement_popup_layout()

    configure_achievement_popup_scroll(
        layout
    )

    popup_rect = layout["popup_rect"]
    header_rect = layout["header_rect"]
    footer_rect = layout["footer_rect"]
    cards_viewport = layout["cards_viewport"]
    summary = layout["summary"]

    # Основной контейнер
    pygame.draw.rect(
        screen,
        WHITE,
        popup_rect,
        border_radius=ACHIEVEMENT_POPUP_BORDER_RADIUS
    )

    pygame.draw.rect(
        screen,
        LIGHT_GRAY,
        popup_rect,
        2,
        border_radius=ACHIEVEMENT_POPUP_BORDER_RADIUS
    )

    # ======================================================
    #                    ФИКСИРОВАННЫЙ HEADER
    # ======================================================

    achievements_count = summary[
        "achievements_count"
    ]

    total_reward_xp = summary[
        "total_reward_xp"
    ]

    secret_count = summary[
        "secret_count"
    ]

    new_player_title = summary[
        "new_player_title"
    ]

    if achievements_count == 1:
        header_title = "Вы открыли новое достижение!"
    else:
        header_title = "Вы открыли новые достижения!"

    draw_center_text(
        header_title,
        title_font,
        BLACK,
        header_rect.y + 25
    )

    summary_parts = [
        f"Получено: +{total_reward_xp} XP",
        f"Достижений: {achievements_count}",
    ]

    if secret_count > 0:
        summary_parts.append(
            f"Секретных: {secret_count}"
        )

    summary_text = "  •  ".join(
        summary_parts
    )

    draw_center_text(
        summary_text,
        small_font,
        DARK_GRAY,
        header_rect.y + 83
    )

    if new_player_title:
        title_label_surface = small_font.render(
            "Получен новый титул:",
            True,
            DARK_GRAY
        )

        player_title_surface = small_font.render(
            new_player_title,
            True,
            BLUE
        )

        title_gap = 8

        title_group_width = (
                title_label_surface.get_width()
                + title_gap
                + player_title_surface.get_width()
        )

        title_group_x = (
                header_rect.centerx
                - title_group_width // 2
        )

        title_y = header_rect.y + 118

        screen.blit(
            title_label_surface,
            (
                title_group_x,
                title_y
            )
        )

        screen.blit(
            player_title_surface,
            (
                title_group_x
                + title_label_surface.get_width()
                + title_gap,
                title_y
            )
        )

    pygame.draw.line(
        screen,
        LIGHT_GRAY,
        (
            popup_rect.x
            + ACHIEVEMENT_POPUP_SIDE_PADDING,
            header_rect.bottom - 1
        ),
        (
            popup_rect.right
            - ACHIEVEMENT_POPUP_SIDE_PADDING,
            header_rect.bottom - 1
        ),
        2
    )

    # ======================================================
    #                ВРЕМЕННЫЕ КАРТОЧКИ
    # ======================================================

    screen.set_clip(cards_viewport)

    card_x = (
        popup_rect.x
        + ACHIEVEMENT_POPUP_SIDE_PADDING
    )

    scrollbar_space = (
        24
        if layout["scroll_needed"]
        else 0
    )

    card_width = (
            popup_rect.width
            - ACHIEVEMENT_POPUP_SIDE_PADDING * 2
            - scrollbar_space
    )

    card_y = (
            cards_viewport.y
            + ACHIEVEMENT_POPUP_CARD_GAP
            - achievement_popup_scroll["offset"]
    )

    sorted_achievements = (
        get_sorted_unlocked_achievements()
    )

    for achievement in sorted_achievements:
        card_rect = pygame.Rect(
            card_x,
            card_y,
            card_width,
            ACHIEVEMENT_POPUP_CARD_HEIGHT
        )

        draw_achievement_popup_card(
            achievement,
            card_rect
        )

        card_y += (
            ACHIEVEMENT_POPUP_CARD_HEIGHT
            + ACHIEVEMENT_POPUP_CARD_GAP
        )

    screen.set_clip(None)

    if layout["scroll_needed"]:
        draw_scrollbar(
            achievement_popup_scroll
        )

    # ======================================================
    #                    ФИКСИРОВАННЫЙ FOOTER
    # ======================================================

    pygame.draw.line(
        screen,
        LIGHT_GRAY,
        (
            popup_rect.x
            + ACHIEVEMENT_POPUP_SIDE_PADDING,
            footer_rect.y
        ),
        (
            popup_rect.right
            - ACHIEVEMENT_POPUP_SIDE_PADDING,
            footer_rect.y
        ),
        2
    )

    close_button, achievements_button = (
        get_achievement_popup_buttons(
            footer_rect
        )
    )

    draw_button(
        close_button,
        font
    )

    draw_button(
        achievements_button,
        font
    )


def get_achievement_by_id(achievement_id):
    """
    Возвращает достижение по его ID.

    Если такого ID нет, возвращает None.
    """
    for category in ACHIEVEMENTS_DATA.values():
        for achievement in category:
            if achievement["id"] == achievement_id:
                return achievement

    return None


def get_achievement_title_by_id(achievement_id):
    """
    Возвращает название достижения по его ID.
    """
    achievement = get_achievement_by_id(
        achievement_id
    )

    if achievement is None:
        return achievement_id

    return achievement["title"]


def clear_developer_input_error(input_mode):
    """
    Очищает ошибку нужного поля.
    """
    global developer_grant_input_error
    global developer_reset_input_error

    if input_mode == "grant":
        developer_grant_input_error = ""

    elif input_mode == "reset":
        developer_reset_input_error = ""


def add_developer_grant_achievement():
    """
    Проверяет ID из поля выдачи и добавляет
    достижение во временный список.
    """
    global developer_grant_input_error
    global developer_grant_tags_scroll_x

    if developer_grant_all or developer_reset_all:
        return

    achievement_id = (
        developer_grant_input["text"]
        .strip()
        .lower()
    )

    if not achievement_id:
        developer_grant_input_error = (
            "Введите ID достижения."
        )
        return

    achievement = get_achievement_by_id(
        achievement_id
    )

    if achievement is None:
        developer_grant_input_error = (
            "Достижение с таким ID не найдено."
        )
        return

    if achievement_id in developer_grant_achievement_ids:
        developer_grant_input_error = (
            "Это достижение уже добавлено для выдачи."
        )
        return

    if achievement_id in developer_reset_achievement_ids:
        developer_grant_input_error = (
            "Это достижение уже добавлено для отката."
        )
        return

    was_completed = (
        developer_initial_achievement_states.get(
            achievement_id,
            False
        )
    )

    if was_completed:
        developer_grant_input_error = (
            "Это достижение уже было получено."
        )
        return

    developer_grant_achievement_ids.append(
        achievement_id
    )

    developer_grant_input["text"] = ""
    developer_grant_input_error = ""

    layout = get_developer_popup_layout()

    developer_grant_tags_scroll_x = 10 ** 9

    developer_grant_tags_scroll_x = (
        clamp_developer_tags_scroll(
            developer_grant_achievement_ids,
            layout["grant_tags_rect"],
            developer_grant_tags_scroll_x
        )
    )

    developer_grant_input["active"] = True
    developer_grant_input["cursor_visible"] = True
    developer_grant_input["cursor_timer"] = (
        pygame.time.get_ticks()
    )


def add_developer_reset_achievement():
    """
    Проверяет ID из поля отката и добавляет
    достижение во временный список.
    """
    global developer_reset_input_error
    global developer_reset_tags_scroll_x

    if developer_grant_all or developer_reset_all:
        return

    achievement_id = (
        developer_reset_input["text"]
        .strip()
        .lower()
    )

    if not achievement_id:
        developer_reset_input_error = (
            "Введите ID достижения."
        )
        return

    achievement = get_achievement_by_id(
        achievement_id
    )

    if achievement is None:
        developer_reset_input_error = (
            "Достижение с таким ID не найдено."
        )
        return

    if achievement_id in developer_reset_achievement_ids:
        developer_reset_input_error = (
            "Это достижение уже добавлено для отката."
        )
        return

    if achievement_id in developer_grant_achievement_ids:
        developer_reset_input_error = (
            "Это достижение уже добавлено для выдачи."
        )
        return

    was_completed = (
        developer_initial_achievement_states.get(
            achievement_id,
            False
        )
    )

    if not was_completed:
        developer_reset_input_error = (
            "Это достижение ещё не было получено."
        )
        return

    developer_reset_achievement_ids.append(
        achievement_id
    )

    developer_reset_input["text"] = ""
    developer_reset_input_error = ""

    layout = get_developer_popup_layout()

    developer_reset_tags_scroll_x = 10 ** 9

    developer_reset_tags_scroll_x = (
        clamp_developer_tags_scroll(
            developer_reset_achievement_ids,
            layout["reset_tags_rect"],
            developer_reset_tags_scroll_x
        )
    )

    developer_reset_input["active"] = True
    developer_reset_input["cursor_visible"] = True
    developer_reset_input["cursor_timer"] = (
        pygame.time.get_ticks()
    )


def reset_developer_pending_state():
    """
    Полностью очищает все изменения,
    подготовленные в developer-панели.
    """
    global developer_pending_balance
    global developer_pending_xp

    global developer_grant_achievement_ids
    global developer_reset_achievement_ids

    global developer_grant_all
    global developer_reset_all

    global developer_initial_achievement_states

    global developer_grant_input_error
    global developer_reset_input_error

    global developer_grant_tags_scroll_x
    global developer_reset_tags_scroll_x

    developer_pending_balance = 0
    developer_pending_xp = 0

    developer_grant_tags_scroll_x = 0
    developer_reset_tags_scroll_x = 0

    developer_grant_achievement_ids = []
    developer_reset_achievement_ids = []

    developer_grant_all = False
    developer_reset_all = False

    developer_initial_achievement_states = {}

    developer_grant_input["text"] = ""
    developer_grant_input["active"] = False
    developer_grant_input["cursor_visible"] = True
    developer_grant_input["cursor_timer"] = pygame.time.get_ticks()

    developer_reset_input["text"] = ""
    developer_reset_input["active"] = False
    developer_reset_input["cursor_visible"] = True
    developer_reset_input["cursor_timer"] = pygame.time.get_ticks()

    developer_grant_input_error = ""
    developer_reset_input_error = ""


def open_developer_popup():
    """
    Открывает developer-панель и создаёт снимок
    текущего состояния достижений.

    Никакие игровые данные при открытии не изменяются.
    """
    global current_popup
    global developer_initial_achievement_states
    global reset_popup_open

    reset_developer_pending_state()

    developer_initial_achievement_states = {
        achievement["id"]: achievement.get(
            "completed",
            False
        )
        for category in ACHIEVEMENTS_DATA.values()
        for achievement in category
    }

    reset_popup_open = False
    current_popup = POPUP_DEVELOPER


def close_developer_popup():
    """
    Закрывает developer-панель без применения изменений.
    """
    global current_popup

    reset_developer_pending_state()
    current_popup = None


def apply_developer_changes():
    """
    Применяет изменения сразу либо ставит их
    в очередь до завершения текущей игры.
    """
    global current_popup
    global developer_queued_changes

    changes = get_developer_changes_snapshot()

    has_changes = any(
        (
            changes["grant_ids"],
            changes["reset_ids"],
            changes["grant_all"],
            changes["reset_all"],
            changes["xp"],
            changes["balance"],
        )
    )

    if not has_changes:
        close_developer_popup()
        return

    game_is_active = (
        current_screen == GAME
        and game_started
        and not game_over
    )

    reset_developer_pending_state()
    current_popup = None

    if game_is_active:
        developer_queued_changes = changes
        return

    achievements_unlocked = (
        execute_developer_changes(
            changes,
            clear_unlocked_queue=True
        )
    )

    if achievements_unlocked:
        open_achievement_popup()


def apply_queued_developer_changes():
    """
    Применяет пакет developer-действий,
    который ждал окончания партии.
    """
    global developer_queued_changes

    if developer_queued_changes is None:
        return False

    changes = developer_queued_changes
    developer_queued_changes = None

    return execute_developer_changes(
        changes,
        clear_unlocked_queue=False
    )


def get_developer_popup_layout():
    """
    Возвращает размеры основных частей
    developer-панели.
    """
    popup_width = min(
        DEVELOPER_POPUP_WIDTH,
        WIDTH - 80
    )

    popup_height = min(
        DEVELOPER_POPUP_HEIGHT,
        HEIGHT - 80
    )

    popup_rect = pygame.Rect(
        WIDTH // 2 - popup_width // 2,
        HEIGHT // 2 - popup_height // 2,
        popup_width,
        popup_height
    )

    header_rect = pygame.Rect(
        popup_rect.x,
        popup_rect.y,
        popup_rect.width,
        DEVELOPER_POPUP_HEADER_HEIGHT
    )

    footer_rect = pygame.Rect(
        popup_rect.x,
        popup_rect.bottom
        - DEVELOPER_POPUP_FOOTER_HEIGHT,
        popup_rect.width,
        DEVELOPER_POPUP_FOOTER_HEIGHT
    )

    content_rect = pygame.Rect(
        popup_rect.x
        + DEVELOPER_POPUP_SIDE_PADDING,
        header_rect.bottom,
        popup_rect.width
        - DEVELOPER_POPUP_SIDE_PADDING * 2,
        footer_rect.top - header_rect.bottom
    )

    section_gap = 34
    section_height = 156

    grant_section_rect = pygame.Rect(
        content_rect.x,
        content_rect.y + 28,
        content_rect.width,
        section_height
    )

    reset_section_rect = pygame.Rect(
        content_rect.x,
        grant_section_rect.bottom + section_gap,
        content_rect.width,
        section_height
    )

    mass_button_width = 245
    mass_button_height = 42

    grant_all_button = create_button(
        grant_section_rect.right - mass_button_width,
        grant_section_rect.y - 3,
        mass_button_width,
        mass_button_height,
        "Выдать все",
        (210, 242, 218)
    )

    reset_all_button = create_button(
        reset_section_rect.right - mass_button_width,
        reset_section_rect.y - 3,
        mass_button_width,
        mass_button_height,
        "Откатить все",
        (252, 220, 220)
    )

    if developer_grant_all:
        grant_all_button["color"] = GREEN
        grant_all_button["text"] = "✓ Выдать все"

    if developer_reset_all:
        reset_all_button["color"] = RED
        reset_all_button["text"] = "✓ Откатить все"

    input_width = content_rect.width
    input_height = 52

    developer_grant_input["rect"] = pygame.Rect(
        grant_section_rect.x,
        grant_section_rect.y + 46,
        input_width,
        input_height
    )

    developer_reset_input["rect"] = pygame.Rect(
        reset_section_rect.x,
        reset_section_rect.y + 46,
        input_width,
        input_height
    )

    tags_area_height = (
            DEVELOPER_TAG_HEIGHT + 14
    )

    grant_tags_rect = pygame.Rect(
        grant_section_rect.x,
        developer_grant_input["rect"].bottom + 12,
        grant_section_rect.width,
        tags_area_height
    )

    reset_tags_rect = pygame.Rect(
        reset_section_rect.x,
        developer_reset_input["rect"].bottom + 12,
        reset_section_rect.width,
        tags_area_height
    )

    quick_actions_y = reset_tags_rect.bottom + 28

    quick_button_gap = 14
    quick_button_height = 44
    quick_button_width = (
                                 content_rect.width - quick_button_gap * 3
                         ) // 4

    add_1000_xp_button = create_button(
        content_rect.x,
        quick_actions_y,
        quick_button_width,
        quick_button_height,
        "+1 000 XP",
        LIGHT_GRAY
    )

    add_10000_xp_button = create_button(
        content_rect.x
        + quick_button_width
        + quick_button_gap,
        quick_actions_y,
        quick_button_width,
        quick_button_height,
        "+10 000 XP",
        LIGHT_GRAY
    )

    add_10000_score_button = create_button(
        content_rect.x
        + (quick_button_width + quick_button_gap) * 2,
        quick_actions_y,
        quick_button_width,
        quick_button_height,
        "+10 000 очков",
        LIGHT_GRAY
    )

    add_100000_score_button = create_button(
        content_rect.x
        + (quick_button_width + quick_button_gap) * 3,
        quick_actions_y,
        quick_button_width,
        quick_button_height,
        "+100 000 очков",
        LIGHT_GRAY
    )

    buttons_group_width = (
        DEVELOPER_POPUP_BUTTON_WIDTH * 2
        + DEVELOPER_POPUP_BUTTON_GAP
    )

    buttons_start_x = (
        popup_rect.centerx
        - buttons_group_width // 2
    )

    buttons_y = (
        footer_rect.centery
        - DEVELOPER_POPUP_BUTTON_HEIGHT // 2
    )

    cancel_button = create_button(
        buttons_start_x,
        buttons_y,
        DEVELOPER_POPUP_BUTTON_WIDTH,
        DEVELOPER_POPUP_BUTTON_HEIGHT,
        "Отмена",
        LIGHT_GRAY
    )

    done_button = create_button(
        buttons_start_x
        + DEVELOPER_POPUP_BUTTON_WIDTH
        + DEVELOPER_POPUP_BUTTON_GAP,
        buttons_y,
        DEVELOPER_POPUP_BUTTON_WIDTH,
        DEVELOPER_POPUP_BUTTON_HEIGHT,
        "Готово",
        BLUE
    )

    return {
        "popup_rect": popup_rect,
        "header_rect": header_rect,
        "content_rect": content_rect,
        "footer_rect": footer_rect,

        "grant_section_rect": grant_section_rect,
        "reset_section_rect": reset_section_rect,

        "grant_tags_rect": grant_tags_rect,
        "reset_tags_rect": reset_tags_rect,

        "cancel_button": cancel_button,
        "done_button": done_button,

        "grant_all_button": grant_all_button,
        "reset_all_button": reset_all_button,

        "add_1000_xp_button": add_1000_xp_button,
        "add_10000_xp_button": add_10000_xp_button,
        "add_10000_score_button": add_10000_score_button,
        "add_100000_score_button": add_100000_score_button,
    }


def get_developer_tag_layout(
    achievement_ids,
    area_rect,
    tag_font,
    scroll_x=0
):
    """
    Раскладывает плашки в одну горизонтальную строку.

    Ширина каждой плашки зависит от полного названия.
    scroll_x задаёт горизонтальное смещение содержимого.
    """
    tags = []

    current_x = area_rect.x - scroll_x

    for achievement_id in achievement_ids:
        title = get_achievement_title_by_id(
            achievement_id
        )

        title_width = tag_font.size(title)[0]

        tag_width = (
            DEVELOPER_TAG_PADDING_X
            + title_width
            + 8
            + DEVELOPER_TAG_CLOSE_SIZE
            + DEVELOPER_TAG_PADDING_X
        )

        tag_rect = pygame.Rect(
            current_x,
            area_rect.y,
            tag_width,
            DEVELOPER_TAG_HEIGHT
        )

        close_rect = pygame.Rect(
            tag_rect.right
            - DEVELOPER_TAG_PADDING_X
            - DEVELOPER_TAG_CLOSE_SIZE,
            tag_rect.centery
            - DEVELOPER_TAG_CLOSE_SIZE // 2,
            DEVELOPER_TAG_CLOSE_SIZE,
            DEVELOPER_TAG_CLOSE_SIZE
        )

        tags.append(
            {
                "id": achievement_id,
                "title": title,
                "tag_rect": tag_rect,
                "close_rect": close_rect,
            }
        )

        current_x = (
            tag_rect.right
            + DEVELOPER_TAG_GAP
        )

    content_width = 0

    if tags:
        content_width = (
            tags[-1]["tag_rect"].right
            - tags[0]["tag_rect"].x
        )

    return tags, content_width


def draw_developer_achievement_tag(
    tag_data,
    fill_color,
    border_color,
    text_color
):
    """
    Рисует плашку выбранного достижения.
    """
    tag_rect = tag_data["tag_rect"]
    close_rect = tag_data["close_rect"]

    pygame.draw.rect(
        screen,
        fill_color,
        tag_rect,
        border_radius=DEVELOPER_TAG_RADIUS
    )

    pygame.draw.rect(
        screen,
        border_color,
        tag_rect,
        2,
        border_radius=DEVELOPER_TAG_RADIUS
    )

    text_left = (
        tag_rect.x
        + DEVELOPER_TAG_PADDING_X
    )

    text_max_width = (
        close_rect.x
        - text_left
        - 8
    )

    title_surface = small_font.render(
        tag_data["title"],
        True,
        text_color
    )

    title_rect = title_surface.get_rect(
        left=text_left,
        centery=tag_rect.centery
    )

    screen.blit(
        title_surface,
        title_rect
    )

    # Крестик
    cross_padding = 5

    pygame.draw.line(
        screen,
        border_color,
        (
            close_rect.x + cross_padding,
            close_rect.y + cross_padding
        ),
        (
            close_rect.right - cross_padding,
            close_rect.bottom - cross_padding
        ),
        2
    )

    pygame.draw.line(
        screen,
        border_color,
        (
            close_rect.right - cross_padding,
            close_rect.y + cross_padding
        ),
        (
            close_rect.x + cross_padding,
            close_rect.bottom - cross_padding
        ),
        2
    )


def clamp_developer_tags_scroll(
    achievement_ids,
    area_rect,
    current_scroll
):
    """
    Ограничивает горизонтальный скролл,
    чтобы содержимое не прокручивалось за границы.
    """
    _, content_width = get_developer_tag_layout(
        achievement_ids,
        area_rect,
        small_font,
        0
    )

    max_scroll = max(
        0,
        content_width - area_rect.width
    )

    return max(
        0,
        min(current_scroll, max_scroll)
    )


def draw_developer_tags_scrollbar(
    area_rect,
    content_width,
    scroll_x
):
    """
    Рисует горизонтальный scrollbar
    под строкой плашек.
    """
    if content_width <= area_rect.width:
        return

    track_height = 5

    track_rect = pygame.Rect(
        area_rect.x,
        area_rect.bottom - track_height,
        area_rect.width,
        track_height
    )

    max_scroll = (
        content_width - area_rect.width
    )

    thumb_width = max(
        45,
        area_rect.width
        * area_rect.width
        / content_width
    )

    available_track_width = (
        track_rect.width - thumb_width
    )

    scroll_progress = (
        scroll_x / max_scroll
        if max_scroll > 0
        else 0
    )

    thumb_x = (
        track_rect.x
        + available_track_width
        * scroll_progress
    )

    thumb_rect = pygame.Rect(
        thumb_x,
        track_rect.y,
        thumb_width,
        track_height
    )

    pygame.draw.rect(
        screen,
        LIGHT_GRAY,
        track_rect,
        border_radius=3
    )

    pygame.draw.rect(
        screen,
        GRAY,
        thumb_rect,
        border_radius=3
    )


def draw_developer_tags_row(
    achievement_ids,
    area_rect,
    scroll_x,
    fill_color,
    border_color,
    text_color
):
    """
    Рисует горизонтальную строку плашек
    с обрезкой по границам области.
    """
    tags, content_width = get_developer_tag_layout(
        achievement_ids,
        area_rect,
        small_font,
        scroll_x
    )

    tags_clip_rect = pygame.Rect(
        area_rect.x,
        area_rect.y,
        area_rect.width,
        DEVELOPER_TAG_HEIGHT
    )

    previous_clip = screen.get_clip()
    screen.set_clip(tags_clip_rect)

    for tag_data in tags:
        draw_developer_achievement_tag(
            tag_data,
            fill_color,
            border_color,
            text_color
        )

    screen.set_clip(previous_clip)

    draw_developer_tags_scrollbar(
        area_rect,
        content_width,
        scroll_x
    )

    return tags, content_width


def draw_developer_popup():
    """
    Рисует каркас developer-панели.
    """
    layout = get_developer_popup_layout()

    grant_section_rect = layout[
        "grant_section_rect"
    ]

    reset_section_rect = layout[
        "reset_section_rect"
    ]

    grant_tags_rect = layout[
        "grant_tags_rect"
    ]

    reset_tags_rect = layout[
        "reset_tags_rect"
    ]

    popup_rect = layout["popup_rect"]
    header_rect = layout["header_rect"]
    content_rect = layout["content_rect"]
    footer_rect = layout["footer_rect"]

    cancel_button = layout["cancel_button"]
    done_button = layout["done_button"]

    grant_all_button = layout["grant_all_button"]
    reset_all_button = layout["reset_all_button"]

    add_1000_xp_button = layout["add_1000_xp_button"]
    add_10000_xp_button = layout["add_10000_xp_button"]
    add_10000_score_button = layout["add_10000_score_button"]
    add_100000_score_button = layout["add_100000_score_button"]

    # Основной фон popup
    pygame.draw.rect(
        screen,
        WHITE,
        popup_rect,
        border_radius=DEVELOPER_POPUP_BORDER_RADIUS
    )

    # Заголовок
    title_surface = title_font.render(
        "Developer-панель",
        True,
        BLACK
    )

    title_rect = title_surface.get_rect(
        centerx=header_rect.centerx,
        y=header_rect.y + 23
    )

    screen.blit(
        title_surface,
        title_rect
    )

    subtitle_surface = small_font.render(
        "Изменения применятся только после нажатия «Готово»",
        True,
        DARK_GRAY
    )

    subtitle_rect = subtitle_surface.get_rect(
        centerx=header_rect.centerx,
        y=header_rect.y + 72
    )

    screen.blit(
        subtitle_surface,
        subtitle_rect
    )

    # Линия под header
    pygame.draw.line(
        screen,
        LIGHT_GRAY,
        (
            popup_rect.x
            + DEVELOPER_POPUP_SIDE_PADDING,
            header_rect.bottom
        ),
        (
            popup_rect.right
            - DEVELOPER_POPUP_SIDE_PADDING,
            header_rect.bottom
        ),
        2
    )

    developer_grant_input["disabled"] = (
            developer_grant_all
            or developer_reset_all
    )

    developer_reset_input["disabled"] = (
            developer_grant_all
            or developer_reset_all
    )

    # ======================================================
    #                 ВЫДАЧА ДОСТИЖЕНИЙ
    # ======================================================

    grant_title_surface = font.render(
        "Выдать достижения",
        True,
        GREEN
    )

    draw_button(
        grant_all_button,
        small_font
    )

    screen.blit(
        grant_title_surface,
        (
            grant_section_rect.x,
            grant_section_rect.y
        )
    )

    update_text_input(
        developer_grant_input
    )

    draw_developer_text_input(
        developer_grant_input,
        developer_grant_input_error
    )

    if developer_grant_input_error:
        grant_error_surface = small_font.render(
            developer_grant_input_error,
            True,
            RED
        )

        screen.blit(
            grant_error_surface,
            (
                grant_tags_rect.x,
                grant_tags_rect.y
            )
        )


    elif developer_grant_achievement_ids:
        draw_developer_tags_row(
            developer_grant_achievement_ids,
            grant_tags_rect,
            developer_grant_tags_scroll_x,
            DEVELOPER_GRANT_TAG_COLOR,
            DEVELOPER_GRANT_TAG_BORDER_COLOR,
            DEVELOPER_GRANT_TAG_TEXT_COLOR
        )

    else:
        grant_hint_surface = small_font.render(
            "Введите ID и нажмите Enter",
            True,
            DARK_GRAY
        )

        screen.blit(
            grant_hint_surface,
            (
                grant_tags_rect.x,
                grant_tags_rect.y
            )
        )

    # ======================================================
    #                 ОТКАТ ДОСТИЖЕНИЙ
    # ======================================================

    reset_title_surface = font.render(
        "Откатить достижения",
        True,
        RED
    )

    draw_button(
        reset_all_button,
        small_font
    )

    screen.blit(
        reset_title_surface,
        (
            reset_section_rect.x,
            reset_section_rect.y
        )
    )

    update_text_input(
        developer_reset_input
    )

    draw_developer_text_input(
        developer_reset_input,
        developer_reset_input_error
    )

    if developer_reset_input_error:
        reset_error_surface = small_font.render(
            developer_reset_input_error,
            True,
            RED
        )

        screen.blit(
            reset_error_surface,
            (
                reset_tags_rect.x,
                reset_tags_rect.y
            )
        )


    elif developer_reset_achievement_ids:
        draw_developer_tags_row(
            developer_reset_achievement_ids,
            reset_tags_rect,
            developer_reset_tags_scroll_x,
            DEVELOPER_RESET_TAG_COLOR,
            DEVELOPER_RESET_TAG_BORDER_COLOR,
            DEVELOPER_RESET_TAG_TEXT_COLOR
        )

    else:
        reset_hint_surface = small_font.render(
            "Введите ID и нажмите Enter",
            True,
            DARK_GRAY
        )

        screen.blit(
            reset_hint_surface,
            (
                reset_tags_rect.x,
                reset_tags_rect.y
            )
        )

    quick_title_surface = small_font.render(
        (
            f"Подготовлено: "
            f"+{developer_pending_xp} XP · "
            f"+{developer_pending_balance} очков"
        ),
        True,
        DARK_GRAY
    )

    screen.blit(
        quick_title_surface,
        (
            content_rect.x,
            add_1000_xp_button["rect"].y - 30
        )
    )

    draw_button(
        add_1000_xp_button,
        small_font
    )

    draw_button(
        add_10000_xp_button,
        small_font
    )

    draw_button(
        add_10000_score_button,
        small_font
    )

    draw_button(
        add_100000_score_button,
        small_font
    )

    # Линия над footer
    pygame.draw.line(
        screen,
        LIGHT_GRAY,
        (
            popup_rect.x
            + DEVELOPER_POPUP_SIDE_PADDING,
            footer_rect.y
        ),
        (
            popup_rect.right
            - DEVELOPER_POPUP_SIDE_PADDING,
            footer_rect.y
        ),
        2
    )

    draw_button(
        cancel_button,
        font
    )

    draw_button(
        done_button,
        font
    )


def toggle_developer_grant_all():
    global developer_grant_all
    global developer_reset_all
    global developer_grant_input_error
    global developer_reset_input_error
    global developer_grant_tags_scroll_x
    global developer_reset_tags_scroll_x

    developer_grant_all = not developer_grant_all

    if developer_grant_all:
        developer_reset_all = False

        developer_grant_achievement_ids.clear()
        developer_reset_achievement_ids.clear()

        developer_grant_tags_scroll_x = 0
        developer_reset_tags_scroll_x = 0

        developer_grant_input["text"] = ""
        developer_reset_input["text"] = ""

        developer_grant_input["active"] = False
        developer_reset_input["active"] = False

        developer_grant_input_error = ""
        developer_reset_input_error = ""


def toggle_developer_reset_all():
    global developer_grant_all
    global developer_reset_all
    global developer_grant_input_error
    global developer_reset_input_error
    global developer_grant_tags_scroll_x
    global developer_reset_tags_scroll_x

    developer_reset_all = not developer_reset_all

    if developer_reset_all:
        developer_grant_all = False

        developer_grant_achievement_ids.clear()
        developer_reset_achievement_ids.clear()

        developer_grant_tags_scroll_x = 0
        developer_reset_tags_scroll_x = 0

        developer_grant_input["text"] = ""
        developer_reset_input["text"] = ""

        developer_grant_input["active"] = False
        developer_reset_input["active"] = False

        developer_grant_input_error = ""
        developer_reset_input_error = ""


def get_developer_changes_snapshot():
    """
    Создаёт независимую копию всех подготовленных действий.
    """
    return {
        "grant_ids": list(
            developer_grant_achievement_ids
        ),
        "reset_ids": list(
            developer_reset_achievement_ids
        ),
        "grant_all": developer_grant_all,
        "reset_all": developer_reset_all,
        "xp": developer_pending_xp,
        "balance": developer_pending_balance,
    }


def developer_reset_achievement(
    achievement
):
    """
    Снимает статус получения достижения.

    XP и общая игровая статистика
    при этом не откатываются.
    """
    if achievement is None:
        return False

    if not achievement.get(
        "completed",
        False
    ):
        return False

    achievement["completed"] = False

    return True


def execute_developer_changes(
    changes,
    clear_unlocked_queue=True
):
    """
    Применяет подготовленный пакет действий.

    Возвращает True, если были выданы
    новые достижения.
    """
    global score
    global highest_balance
    global total_xp
    global last_xp_gained

    if changes is None:
        return False

    if clear_unlocked_queue:
        newly_unlocked_achievements.clear()

    # ------------------------------
    # Очки
    # ------------------------------

    added_balance = changes.get(
        "balance",
        0
    )

    if added_balance:
        score += added_balance

        highest_balance = max(
            highest_balance,
            score
        )

        update_phoenix_achievement()

    # ------------------------------
    # XP
    # ------------------------------

    added_xp = changes.get(
        "xp",
        0
    )

    if added_xp:
        old_level = get_player_level()

        total_xp += added_xp
        last_xp_gained = added_xp

        new_level = get_player_level()

        if new_level > old_level:
            level_up(new_level)

    # ------------------------------
    # Откат достижений
    # ------------------------------

    if changes.get("reset_all", False):
        for category in ACHIEVEMENTS_DATA.values():
            for achievement in category:
                achievement["completed"] = False

    else:
        for achievement_id in changes.get(
            "reset_ids",
            []
        ):
            achievement = get_achievement_by_id(
                achievement_id
            )

            developer_reset_achievement(
                achievement
            )

    # ------------------------------
    # Выдача достижений
    # ------------------------------

    unlocked_before = len(
        newly_unlocked_achievements
    )

    if changes.get("grant_all", False):
        for category in ACHIEVEMENTS_DATA.values():
            for achievement in category:
                unlock_achievement(
                    achievement
                )

    else:
        for achievement_id in changes.get(
            "grant_ids",
            []
        ):
            achievement = get_achievement_by_id(
                achievement_id
            )

            if achievement is not None:
                unlock_achievement(
                    achievement
                )

    # XP, баланс и ручные награды могут выполнить другие условия.
    # Явно откатываемые в этом же пакете ID исключаются, чтобы developer-
    # команда отката не отменялась немедленной ретроактивной проверкой.
    if changes.get("reset_all", False):
        excluded_ids = {
            achievement["id"]
            for achievement in get_all_achievements()
        }
    else:
        excluded_ids = set(
            changes.get("reset_ids", [])
        )

    should_recheck = any(
        (
            added_balance,
            added_xp,
            changes.get("grant_all", False),
            changes.get("grant_ids", []),
        )
    )

    if should_recheck:
        check_achievements(
            excluded_ids=excluded_ids
        )

    unlocked_after = len(
        newly_unlocked_achievements
    )

    save_progress()

    return unlocked_after > unlocked_before


def draw_popup():

    if current_popup is None:
        return

    # Затемнение
    overlay = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )

    overlay.fill(
        (0, 0, 0, 120)
    )

    screen.blit(
        overlay,
        (0, 0)
    )

    if current_popup == POPUP_ACHIEVEMENTS:
        draw_achievement_unlock_popup()
        return

    if current_popup == POPUP_DEVELOPER:
        draw_developer_popup()
        return

    popup_width = 500
    popup_height = 420

    popup_rect = pygame.Rect(
        WIDTH // 2 - popup_width // 2,
        HEIGHT // 2 - popup_height // 2,
        popup_width,
        popup_height
    )

    button_width = 260
    button_height = 55
    button_gap = 18

    start_x = WIDTH // 2 - button_width // 2
    start_y = popup_rect.y + 110

    pygame.draw.rect(
        screen,
        WHITE,
        popup_rect,
        border_radius=20
    )

    if current_popup == POPUP_DIFFICULTY:

        draw_center_text(
            "Выберите сложность",
            font,
            BLACK,
            popup_rect.y + 45
        )

        easy_button = create_button(
            start_x,
            start_y,
            button_width,
            button_height,
            "Лёгкая",
            BLUE
        )

        medium_button = create_button(
            start_x,
            start_y + button_height + button_gap,
            button_width,
            button_height,
            "Средняя",
            YELLOW
        )

        hard_button = create_button(
            start_x,
            start_y + 2 * (button_height + button_gap),
            button_width,
            button_height,
            "Сложная",
            RED
        )

        cancel_button = create_button(
            start_x,
            start_y + 3 * (button_height + button_gap),
            button_width,
            button_height,
            "Отмена",
            LIGHT_GRAY
        )

        draw_button(easy_button, font)
        draw_button(medium_button, font)
        draw_button(hard_button, font)
        draw_button(cancel_button, font)

    elif current_popup == POPUP_INFO:

        draw_center_text(
            popup_title,
            font,
            BLACK,
            popup_rect.y + 45
        )

        lines = popup_text.split("\n")

        for i, line in enumerate(lines):
            draw_center_text(
                line,
                small_font,
                DARK_GRAY,
                popup_rect.y + 140 + i * 35
            )

        ok_button = create_button(
            popup_rect.centerx - 80,
            popup_rect.bottom - 90,
            160,
            50,
            "OK",
            BLUE
        )

        draw_button(ok_button, font)



    elif current_popup == POPUP_INPUT:

        draw_center_text(
            "Изменение имени",
            title_font,
            BLACK,
            popup_rect.y + 45
        )

        name_input["rect"].centerx = popup_rect.centerx
        name_input["rect"].y = popup_rect.y + 120

        update_text_input(name_input)
        draw_text_input(name_input)

        save_button = create_button(
            popup_rect.centerx - 165,
            popup_rect.bottom - 90,
            180,
            50,
            "Сохранить",
            BLUE
        )

        cancel_button = create_button(
            popup_rect.centerx + 35,
            popup_rect.bottom - 90,
            120,
            50,
            "Отмена",
            LIGHT_GRAY
        )

        draw_button(save_button, font)
        draw_button(cancel_button, font)


def handle_achievement_popup_click(mouse_pos):
    global current_popup
    global current_screen

    layout = get_achievement_popup_layout()
    footer_rect = layout["footer_rect"]

    close_button, achievements_button = (
        get_achievement_popup_buttons(
            footer_rect
        )
    )

    if close_button["rect"].collidepoint(
        mouse_pos
    ):
        close_achievement_popup()
        return

    if achievements_button["rect"].collidepoint(
            mouse_pos
    ):
        close_achievement_popup()
        current_screen = ACHIEVEMENTS_SCREEN

        achievement_scroll["offset"] = 0

        if "target_offset" in achievement_scroll:
            achievement_scroll["target_offset"] = 0

        return


def handle_developer_input_click(mouse_pos):
    """
    Активирует только одно из двух полей.
    """
    grant_clicked = (
        developer_grant_input["rect"]
        .collidepoint(mouse_pos)
    )

    reset_clicked = (
        developer_reset_input["rect"]
        .collidepoint(mouse_pos)
    )

    developer_grant_input["active"] = (
        grant_clicked
    )

    developer_reset_input["active"] = (
        reset_clicked
    )

    for text_input in (
        developer_grant_input,
        developer_reset_input
    ):
        text_input["cursor_visible"] = True
        text_input["cursor_timer"] = (
            pygame.time.get_ticks()
        )


def is_command_key(event):
    """
    Проверяет, относится ли событие
    к левой или правой клавише Command.
    """
    command_keys = {
        getattr(pygame, "K_LGUI", pygame.K_LMETA),
        getattr(pygame, "K_RGUI", pygame.K_RMETA),
        pygame.K_LMETA,
        pygame.K_RMETA,
    }

    return event.key in command_keys


def handle_developer_popup_keyboard(
    event,
    command_pressed=False
):
    """
    Обрабатывает ввод в двух полях developer-панели.
    """
    global developer_grant_input_error
    global developer_reset_input_error

    if (
            command_pressed
            and event.scancode == MAC_SCANCODE_V
    ):
        clipboard_text = get_text_from_clipboard()

    if (
        command_pressed
        and event.scancode == MAC_SCANCODE_1
    ):
        return

    active_input = None
    input_mode = None

    if developer_grant_input["active"]:
        active_input = developer_grant_input
        input_mode = "grant"

    elif developer_reset_input["active"]:
        active_input = developer_reset_input
        input_mode = "reset"

    if active_input is None:
        return

    # Cmd + V — вставка из системного буфера macOS
    if (
        command_pressed
        and event.scancode == MAC_SCANCODE_V
    ):
        clipboard_text = get_text_from_clipboard()

        if clipboard_text:
            max_length = active_input.get(
                "max_length",
                1000
            )

            available_length = (
                max_length
                - len(active_input["text"])
            )

            if available_length > 0:
                active_input["text"] += (
                    clipboard_text[
                        :available_length
                    ]
                )

                active_input["cursor_visible"] = True
                active_input["cursor_timer"] = (
                    pygame.time.get_ticks()
                )

                clear_developer_input_error(
                    input_mode
                )

        return

    # Cmd + C — копирование всего содержимого поля
    if (
        command_pressed
        and event.scancode == MAC_SCANCODE_C
    ):
        copy_text_to_clipboard(
            active_input["text"]
        )

        return

    if event.key in (
        pygame.K_RETURN,
        pygame.K_KP_ENTER
    ):
        if input_mode == "grant":
            add_developer_grant_achievement()
        else:
            add_developer_reset_achievement()

        return

    previous_text = active_input["text"]

    handle_text_input_keyboard(
        active_input,
        event,
        command_pressed
    )

    if active_input["text"] != previous_text:
        clear_developer_input_error(
            input_mode
        )


def handle_developer_tag_click(
    mouse_pos,
    achievement_ids,
    tags_rect,
    scroll_x
):
    """
    Удаляет достижение по нажатию на крестик.
    """
    tags, _ = get_developer_tag_layout(
        achievement_ids,
        tags_rect,
        small_font,
        scroll_x
    )

    for tag_data in tags:
        visible_close_rect = (
            tag_data["close_rect"].clip(
                tags_rect
            )
        )

        if (
            visible_close_rect.width > 0
            and visible_close_rect.height > 0
            and tag_data["close_rect"].collidepoint(
                mouse_pos
            )
        ):
            achievement_ids.remove(
                tag_data["id"]
            )
            return True

    return False


def handle_developer_tags_scroll(
    mouse_pos,
    scroll_direction
):
    """
    Прокручивает строку плашек под курсором.
    """
    global developer_grant_tags_scroll_x
    global developer_reset_tags_scroll_x

    layout = get_developer_popup_layout()

    grant_tags_rect = layout[
        "grant_tags_rect"
    ]

    reset_tags_rect = layout[
        "reset_tags_rect"
    ]

    scroll_step = 70

    if grant_tags_rect.collidepoint(mouse_pos):
        developer_grant_tags_scroll_x -= (
            scroll_direction * scroll_step
        )

        developer_grant_tags_scroll_x = (
            clamp_developer_tags_scroll(
                developer_grant_achievement_ids,
                grant_tags_rect,
                developer_grant_tags_scroll_x
            )
        )

        return True

    if reset_tags_rect.collidepoint(mouse_pos):
        developer_reset_tags_scroll_x -= (
            scroll_direction * scroll_step
        )

        developer_reset_tags_scroll_x = (
            clamp_developer_tags_scroll(
                developer_reset_achievement_ids,
                reset_tags_rect,
                developer_reset_tags_scroll_x
            )
        )

        return True

    return False


def handle_developer_popup_click(mouse_pos):
    """
    Обрабатывает клики внутри developer-панели.
    """
    global developer_pending_xp
    global developer_pending_balance

    layout = get_developer_popup_layout()

    grant_tags_rect = layout[
        "grant_tags_rect"
    ]

    reset_tags_rect = layout[
        "reset_tags_rect"
    ]

    grant_all_button = layout[
        "grant_all_button"
    ]

    reset_all_button = layout[
        "reset_all_button"
    ]

    add_1000_xp_button = layout[
        "add_1000_xp_button"
    ]

    add_10000_xp_button = layout[
        "add_10000_xp_button"
    ]

    add_10000_score_button = layout[
        "add_10000_score_button"
    ]

    add_100000_score_button = layout[
        "add_100000_score_button"
    ]

    cancel_button = layout[
        "cancel_button"
    ]

    done_button = layout[
        "done_button"
    ]

    # Удаление зелёных плашек
    if handle_developer_tag_click(
        mouse_pos,
        developer_grant_achievement_ids,
        grant_tags_rect,
        developer_grant_tags_scroll_x
    ):
        return

    # Удаление красных плашек
    if handle_developer_tag_click(
        mouse_pos,
        developer_reset_achievement_ids,
        reset_tags_rect,
        developer_reset_tags_scroll_x
    ):
        return

    # Массовая выдача достижений
    if grant_all_button["rect"].collidepoint(
        mouse_pos
    ):
        toggle_developer_grant_all()
        return

    # Массовый откат достижений
    if reset_all_button["rect"].collidepoint(
        mouse_pos
    ):
        toggle_developer_reset_all()
        return

    # Добавление XP
    if add_1000_xp_button["rect"].collidepoint(
        mouse_pos
    ):
        developer_pending_xp += 1000
        return

    if add_10000_xp_button["rect"].collidepoint(
        mouse_pos
    ):
        developer_pending_xp += 10000
        return

    # Добавление очков
    if add_10000_score_button["rect"].collidepoint(
        mouse_pos
    ):
        developer_pending_balance += 10000
        return

    if add_100000_score_button["rect"].collidepoint(
        mouse_pos
    ):
        developer_pending_balance += 100000
        return

    # Переключение активного поля ввода
    handle_developer_input_click(
        mouse_pos
    )

    # Отмена всех подготовленных изменений
    if cancel_button["rect"].collidepoint(
        mouse_pos
    ):
        close_developer_popup()
        return

    # Применение подготовленных изменений
    if done_button["rect"].collidepoint(
        mouse_pos
    ):
        apply_developer_changes()
        return


def handle_popup_click(mouse_pos):
    global current_popup
    global player_name

    if current_popup is None:
        return

    if current_popup == POPUP_ACHIEVEMENTS:
        handle_achievement_popup_click(
            mouse_pos
        )
        return

    if current_popup == POPUP_DEVELOPER:
        handle_developer_popup_click(
            mouse_pos
        )
        return

    popup_width = 500
    popup_height = 420

    popup_rect = pygame.Rect(
        WIDTH // 2 - popup_width // 2,
        HEIGHT // 2 - popup_height // 2,
        popup_width,
        popup_height
    )

    if current_popup == POPUP_INFO:

        ok_button = create_button(
            popup_rect.centerx - 80,
            popup_rect.bottom - 90,
            160,
            50,
            "OK",
            BLUE
        )

        if ok_button["rect"].collidepoint(mouse_pos):
            current_popup = None

        return

    button_width = 260
    button_height = 55
    button_gap = 18

    popup_width = 500
    popup_height = 420

    popup_rect = pygame.Rect(
        WIDTH // 2 - popup_width // 2,
        HEIGHT // 2 - popup_height // 2,
        popup_width,
        popup_height
    )

    start_x = popup_rect.centerx - button_width // 2
    start_y = popup_rect.y + 110

    easy_button = create_button(
        start_x,
        start_y,
        button_width,
        button_height,
        "Лёгкая",
        BLUE
    )

    medium_button = create_button(
        start_x,
        start_y + button_height + button_gap,
        button_width,
        button_height,
        "Средняя",
        YELLOW
    )

    hard_button = create_button(
        start_x,
        start_y + 2 * (button_height + button_gap),
        button_width,
        button_height,
        "Сложная",
        RED
    )

    cancel_button = create_button(
        start_x,
        start_y + 3 * (button_height + button_gap),
        button_width,
        button_height,
        "Отмена",
        LIGHT_GRAY
    )

    if current_popup == POPUP_INPUT:
        handle_text_input_click(name_input, mouse_pos)

        save_button = create_button(
            popup_rect.centerx - 135,
            popup_rect.bottom - 90,
            120,
            50,
            "Сохранить",
            BLUE
        )

        cancel_button = create_button(
            popup_rect.centerx + 15,
            popup_rect.bottom - 90,
            120,
            50,
            "Отмена",
            LIGHT_GRAY
        )

        if save_button["rect"].collidepoint(mouse_pos):
            global player_name

            if name_input["text"].strip():
                player_name = name_input["text"]
                save_progress()

            current_popup = None

        elif cancel_button["rect"].collidepoint(mouse_pos):
            current_popup = None

        return

    if easy_button["rect"].collidepoint(mouse_pos):
        current_popup = None
        set_difficulty("Лёгкая")

    elif medium_button["rect"].collidepoint(mouse_pos):
        current_popup = None
        set_difficulty("Средняя")

    elif hard_button["rect"].collidepoint(mouse_pos):
        current_popup = None
        set_difficulty("Сложная")

    elif cancel_button["rect"].collidepoint(mouse_pos):
        current_popup = None


def draw_game():
    screen.fill(WHITE)

    back_to_menu_button = get_back_to_menu_button()

    draw_button(back_to_menu_button, small_font)
    draw_stats_panel()
    draw_bet_panel()

    center_x = get_game_area_center_x()

    title_text = big_font.render("Угадай число", True, BLACK)
    screen.blit(title_text, (center_x - title_text.get_width() // 2, 60))

    info_text = small_font.render(f"Сложность: {difficulty_name} | Числа: {min_number}-{max_number}", True, DARK_GRAY)
    screen.blit(info_text, (center_x - info_text.get_width() // 2, 140))

    if game_over:
        if win:
            result_color = GREEN
        else:
            result_color = RED

        result_text_1 = font.render(result_line_1, True, result_color)
        screen.blit(result_text_1, (center_x - result_text_1.get_width() // 2, 185))

        result_text_2 = small_font.render(result_line_2, True, DARK_GRAY)
        screen.blit(result_text_2, (center_x - result_text_2.get_width() // 2, 235))
    else:
        message_text = font.render(message, True, BLACK)
        screen.blit(message_text, (center_x - message_text.get_width() // 2, 190))

        attempts_text = small_font.render(f"Попытки: {attempts_left}/{max_attempts}", True, DARK_GRAY)
        screen.blit(attempts_text, (center_x - attempts_text.get_width() // 2, 245))

    for tile in tiles:
        rect = tile["rect"]
        number = tile["number"]
        color = tile["color"]

        pygame.draw.rect(screen, color, rect, border_radius=12)

        number_text = small_font.render(str(number), True, BLACK)
        text_x = rect.centerx - number_text.get_width() // 2
        text_y = rect.centery - number_text.get_height() // 2

        screen.blit(number_text, (text_x, text_y))

    if game_over:
        bottom_text = small_font.render("Выбери ставку и нажми «Заново»", True, DARK_GRAY)
        screen.blit(bottom_text, (center_x - bottom_text.get_width() // 2, HEIGHT - 140))

        restart_button = get_restart_button()
        draw_button(restart_button, small_font)

    if reset_popup_open:
        draw_reset_popup()

    draw_level_up_message()


def handle_reset_popup_click(mouse_pos):
    global reset_popup_open

    cancel_button = get_popup_cancel_button()
    confirm_button = get_popup_confirm_button()

    if cancel_button["rect"].collidepoint(mouse_pos):
        reset_popup_open = False
        return

    if confirm_button["rect"].collidepoint(mouse_pos):
        reset_progress()
        return


def handle_menu_click(mouse_pos):
    global current_popup, popup_title, popup_text, current_screen

    for button in get_menu_buttons():

        if button["rect"].collidepoint(mouse_pos):

            if button["text"] == "Играть":
                current_popup = POPUP_DIFFICULTY


            elif button["text"] == "Профиль":
                current_screen = PROFILE



            elif button["text"] == "Достижения":
                current_screen = ACHIEVEMENTS_SCREEN
                return

            elif button["text"] == "Настройки":
                current_popup = POPUP_INFO
                popup_title = "Настройки"
                popup_text = "Раздел находится\nв разработке."

            elif button["text"] == "Developer-панель":
                open_developer_popup()
                return

            elif button["text"] == "Выход":
                pygame.quit()
                sys.exit()


def handle_profile_click(mouse_pos):
    global current_screen, current_popup

    back_button = create_button(
        30,
        32,
        150,
        55,
        "Назад",
        LIGHT_GRAY
    )

    change_name_button = create_button(
        WIDTH // 2 - 115,
        345 - profile_scroll["offset"],
        230,
        40,
        "Изменить имя",
        BLUE
    )

    handle_text_input_click(
        name_input,
        mouse_pos
    )

    if back_button["rect"].collidepoint(mouse_pos):
        current_screen = MENU
        return

    if change_name_button["rect"].collidepoint(mouse_pos):
        name_input["text"] = player_name
        name_input["active"] = False
        current_popup = POPUP_INPUT


def handle_game_click(mouse_pos):
    global secret_number, attempts_left, game_over, win, message, tiles
    global current_screen, selected_bet, current_bet, game_started
    global custom_bet_active, custom_bet_error, reset_popup_open
    global result_line_1, result_line_2
    global balance_before_bet, started_all_in

    if reset_popup_open:
        handle_reset_popup_click(mouse_pos)
        return

    back_to_menu_button = get_back_to_menu_button()
    restart_button = get_restart_button()
    bet_buttons = get_bet_buttons()
    input_rect = get_custom_bet_input_rect()
    apply_button = get_custom_bet_apply_button()
    reset_button = get_reset_button()

    if reset_button["rect"].collidepoint(mouse_pos):
        custom_bet_active = False
        reset_popup_open = True
        return

    if back_to_menu_button["rect"].collidepoint(mouse_pos):
        custom_bet_active = False
        save_progress()
        current_screen = MENU
        return

    if get_can_change_bet() and score > 0 and input_rect.collidepoint(mouse_pos):
        custom_bet_active = True

        if custom_bet_text == "":
            custom_bet_error = ""

        return
    else:
        custom_bet_active = False

    if get_can_change_bet() and apply_button["rect"].collidepoint(mouse_pos):
        apply_custom_bet()
        return

    if get_can_change_bet():
        for button in bet_buttons:
            if button["rect"].collidepoint(mouse_pos) and button["active"]:
                set_selected_bet(button["bet"])
                custom_bet_error = ""
                return

    if game_over and restart_button["rect"].collidepoint(mouse_pos):
        secret_number, attempts_left, game_over, win, message, tiles = start_new_game()
        return

    if game_over:
        return

    for tile in tiles:
        if tile["rect"].collidepoint(mouse_pos) and tile["active"]:
            custom_bet_active = False

            if not game_started:
                current_bet = selected_bet
                balance_before_bet = score

                started_all_in = (
                        current_bet > 0
                        and current_bet == balance_before_bet
                )

                game_started = True

            chosen_number = tile["number"]

            if chosen_number == secret_number:
                tile["color"] = GREEN

                result = finish_game(True)

                result_line_1 = f"Победа! +{result['total']} очков"
                result_line_2 = (
                    f"База: {result['base_points']} × x{result['streak_multiplier']:.1f} = "
                    f"{result['earned_points']} | Ставка: +{result['bet_bonus']}"
                )

                message = result_line_1
                game_over = True
                win = True

                check_achievements()

                apply_queued_developer_changes()

                save_progress()

                print_newly_unlocked_achievements()
                open_achievement_popup()

            elif chosen_number < secret_number:
                attempts_left -= 1
                message = f"Загаданное число больше {chosen_number}"

                for other_tile in tiles:
                    if other_tile["number"] <= chosen_number:
                        other_tile["color"] = GRAY
                        other_tile["active"] = False

                tile["color"] = RED

            else:
                attempts_left -= 1
                message = f"Загаданное число меньше {chosen_number}"

                for other_tile in tiles:
                    if other_tile["number"] >= chosen_number:
                        other_tile["color"] = GRAY
                        other_tile["active"] = False

                tile["color"] = RED

            if attempts_left == 0 and not win:
                result = finish_game(False)

                result_line_1 = f"Поражение! -{result['total']} очков"
                result_line_2 = (
                    f"Штраф: {result['base_penalty']} | "
                    f"Ставка: -{result['bet_penalty']} | "
                    f"Число было {secret_number}"
                )

                message = result_line_1
                game_over = True

                check_achievements()

                apply_queued_developer_changes()

                save_progress()

                print_newly_unlocked_achievements()
                open_achievement_popup()

                for other_tile in tiles:
                    other_tile["active"] = False

                    if other_tile["number"] == secret_number:
                        other_tile["color"] = GREEN

            break


def handle_custom_bet_typing(event):
    global custom_bet_text, custom_bet_error

    if reset_popup_open:
        return

    if not custom_bet_active:
        return

    if not get_can_change_bet():
        return

    if score <= 0:
        return

    if event.key == pygame.K_RETURN:
        apply_custom_bet()
        return

    if event.key == pygame.K_BACKSPACE:
        custom_bet_text = custom_bet_text[:-1]

        if custom_bet_text == "":
            custom_bet_error = ""
        elif int(custom_bet_text) > score:
            custom_bet_error = f"Ставка не выше баланса: {score}"
        else:
            custom_bet_error = ""

        return

    if event.unicode.isdigit():
        new_text = custom_bet_text + event.unicode

        if len(new_text) > 1 and new_text[0] == "0":
            new_text = new_text.lstrip("0")

        if new_text == "":
            new_text = "0"

        custom_bet_text = new_text

        if int(custom_bet_text) > score:
            custom_bet_error = f"Ставка не выше баланса: {score}"
        else:
            custom_bet_error = ""


def handle_debug_keys(
    event,
    command_pressed=False
):
    """
    Обрабатывает временные developer-команды.

    Глобальный вызов developer-панели через Cmd + 1.
    """
    if not DEVELOPER_MODE:
        return

    if (
            command_pressed
            and event.scancode == MAC_SCANCODE_1
    ):
        if current_popup is None:
            open_developer_popup()


initialize_achievement_states()
load_progress()

# Кумулятивные условия из старого сохранения выдаются сразу после миграции.
# Уже завершённые достижения пропускаются, поэтому повторной награды XP нет.
check_achievements()

profile_scroll = create_scroll_area(
    WIDTH - 25,
    150,
    8,
    400,
    1100
)

achievement_scroll = create_scroll_area(
    WIDTH - 25,
    105,
    8,
    HEIGHT - 150,
    5000
)

achievement_popup_scroll = create_scroll_area(
    0,
    0,
    1,
    1,
    1
)

achievement_popup_scroll["enabled"] = False

if newly_unlocked_achievements:
    open_achievement_popup()

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_progress()
            running = False

        if event.type == pygame.VIDEORESIZE:
            WIDTH = max(event.w, MIN_WIDTH)
            HEIGHT = max(event.h, MIN_HEIGHT)

            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            update_tile_positions()

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_position = event.pos

            if event.button != 1:
                continue

            if current_popup is not None:
                handle_popup_click(mouse_position)
                continue

            if current_screen == MENU:
                handle_menu_click(mouse_position)

            elif current_screen == GAME:
                handle_game_click(mouse_position)

            elif current_screen == PROFILE:
                handle_profile_click(mouse_position)

            elif current_screen == ACHIEVEMENTS_SCREEN:
                handle_achievements_click(mouse_position)

        if event.type == pygame.KEYDOWN and is_command_key(event):
            command_key_pressed = True

        if event.type == pygame.KEYUP and is_command_key(event):
            command_key_pressed = False

        if event.type == pygame.KEYDOWN:

            if (
                    event.key == pygame.K_ESCAPE
                    and current_popup is not None
            ):
                if current_popup == POPUP_ACHIEVEMENTS:
                    close_achievement_popup()

                elif current_popup == POPUP_DEVELOPER:
                    close_developer_popup()

                else:
                    current_popup = None

                continue

            # Глобальные developer-команды
            handle_debug_keys(
                event,
                command_key_pressed
            )

            # После открытия панели этот же KEYDOWN
            # больше никуда не передаём.
            if current_popup == POPUP_DEVELOPER:
                handle_developer_popup_keyboard(
                    event,
                    command_key_pressed
                )
                continue

            if current_popup == POPUP_INPUT:
                handle_text_input_keyboard(
                    name_input,
                    event,
                    command_key_pressed
                )

            elif current_screen == PROFILE:
                handle_text_input_keyboard(
                    name_input,
                    event,
                    command_key_pressed
                )

            if current_screen == GAME:
                handle_custom_bet_typing(event)

        if (
                event.type == pygame.MOUSEWHEEL
                and current_popup == POPUP_DEVELOPER
        ):
            handle_developer_tags_scroll(
                pygame.mouse.get_pos(),
                event.y
            )
            continue

        if current_popup == POPUP_ACHIEVEMENTS:
            handle_scroll_event(
                achievement_popup_scroll,
                event
            )

        elif current_popup is None:

            if current_screen == PROFILE:
                handle_scroll_event(
                    profile_scroll,
                    event
                )

            elif current_screen == ACHIEVEMENTS_SCREEN:
                handle_scroll_event(
                    achievement_scroll,
                    event
                )

    if current_popup == POPUP_ACHIEVEMENTS:
        update_scroll(
            achievement_popup_scroll
        )

    elif current_popup is None:

        if current_screen == PROFILE:
            update_scroll(
                profile_scroll
            )

        elif current_screen == ACHIEVEMENTS_SCREEN:
            update_scroll(
                achievement_scroll
            )

    if current_screen == MENU:
        draw_menu()

    elif current_screen == GAME:
        draw_game()

    elif current_screen == PROFILE:
        draw_profile()

    elif current_screen == ACHIEVEMENTS_SCREEN:
        draw_achievements_screen()

    draw_popup()

    pygame.display.flip()

pygame.quit()
