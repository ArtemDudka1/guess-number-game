import pygame
import random
import math
import json
import copy
import os
import sys
import subprocess
from pathlib import Path

from constants import *

pygame.init()
pygame.key.set_repeat(500, 40)

def initialize_audio_system():
    """
    Безопасно подготавливает pygame Mixer.

    Отсутствие аудиоустройства не должно
    мешать запуску игры.
    """

    # pygame.init() уже мог успешно
    # инициализировать Mixer.
    if pygame.mixer.get_init() is not None:
        return True

    try:
        pygame.mixer.init()
        return True

    except pygame.error:
        return False


audio_available = initialize_audio_system()

DEBUG_MODE = os.environ.get(
    "NUMBER_TILES_DEBUG",
    ""
).lower() in {"1", "true", "yes", "on"}

DEBUG_ACHIEVEMENTS = DEBUG_MODE

# До полноценной версии developer-инструментов панель доступна постоянно.
# DEBUG_MODE отдельно управляет только диагностическими логами.
DEVELOPER_MODE = True

# ==========================================================
#                    SETTINGS SYSTEM
# ==========================================================

SETTINGS_SCHEMA_VERSION = 1

DEFAULT_PLAYER_NAME = "Player"

# ==========================================================
#               ДОПУСТИМЫЕ ЗНАЧЕНИЯ
# ==========================================================

VALID_START_DIFFICULTIES = (
    "ask",
    "easy",
    "medium",
    "hard",
)

VALID_WINDOW_MODES = (
    "windowed",
    "fullscreen",
)

MIN_VOLUME = 0
MAX_VOLUME = 100

MIN_SAVED_WINDOW_WIDTH = MIN_WIDTH
MIN_SAVED_WINDOW_HEIGHT = MIN_HEIGHT

MAX_SAVED_WINDOW_WIDTH = 10000
MAX_SAVED_WINDOW_HEIGHT = 10000

# ==========================================================
#                 НАСТРОЙКИ ПО УМОЛЧАНИЮ
# ==========================================================

DEFAULT_SETTINGS = {
    "schema_version": SETTINGS_SCHEMA_VERSION,

    "game": {
        "start_difficulty": "ask",
        "confirm_unfinished_exit": True,
    },

    "interface": {
        "window_mode": "windowed",

        "windowed_width": MIN_WIDTH,
        "windowed_height": MIN_HEIGHT,

        "show_result_details": True,
        "show_achievement_popups": True,
        "show_level_up_notification": True,
        "smooth_scroll": True,
    },

    "audio": {
        "enabled": True,
        "master_volume": 100,
        "effects_volume": 100,
        "music_volume": 100,
    },

    "developer": {
        "enabled": False,
    },
}

# Текущие настройки всегда хранятся отдельно
# от неизменяемого шаблона DEFAULT_SETTINGS.
settings = copy.deepcopy(
    DEFAULT_SETTINGS
)


def get_effect_volume():
    """
    Возвращает итоговую громкость эффектов
    в формате pygame от 0.0 до 1.0.
    """

    if not settings[
        "audio"
    ][
        "enabled"
    ]:
        return 0.0

    master_volume = (
        settings[
            "audio"
        ][
            "master_volume"
        ]
        / 100
    )

    effects_volume = (
        settings[
            "audio"
        ][
            "effects_volume"
        ]
        / 100
    )

    return master_volume * effects_volume


def get_music_volume():
    """
    Возвращает итоговую громкость музыки
    в формате pygame от 0.0 до 1.0.
    """

    if not settings[
        "audio"
    ][
        "enabled"
    ]:
        return 0.0

    master_volume = (
        settings[
            "audio"
        ][
            "master_volume"
        ]
        / 100
    )

    music_volume = (
        settings[
            "audio"
        ][
            "music_volume"
        ]
        / 100
    )

    return master_volume * music_volume


def create_default_settings():
    return copy.deepcopy(
        DEFAULT_SETTINGS
    )

def get_valid_bool(
    data,
    key,
    default
):
    value = data.get(
        key,
        default
    )

    if isinstance(value, bool):
        return value

    return default


def get_valid_choice(
    data,
    key,
    valid_values,
    default
):
    value = data.get(
        key,
        default
    )

    if value in valid_values:
        return value

    return default


def get_valid_volume(
    data,
    key,
    default
):
    value = data.get(
        key,
        default
    )

    if (
        isinstance(value, bool)
        or not isinstance(value, int)
    ):
        return default

    return max(
        MIN_VOLUME,
        min(
            value,
            MAX_VOLUME
        )
    )


def get_valid_window_size(
    data,
    key,
    default,
    minimum,
    maximum
):
    value = data.get(
        key,
        default
    )

    if (
        isinstance(value, bool)
        or not isinstance(value, int)
    ):
        return default

    if not minimum <= value <= maximum:
        return default

    return value


def validate_settings(
    saved_settings
):
    validated = create_default_settings()

    if not isinstance(
        saved_settings,
        dict
    ):
        return validated

    # ======================================================
    #                       GAME
    # ======================================================

    saved_game = saved_settings.get(
        "game",
        {}
    )

    if isinstance(saved_game, dict):
        validated["game"]["start_difficulty"] = (
            get_valid_choice(
                saved_game,
                "start_difficulty",
                VALID_START_DIFFICULTIES,
                DEFAULT_SETTINGS[
                    "game"
                ][
                    "start_difficulty"
                ]
            )
        )

        validated[
            "game"
        ][
            "confirm_unfinished_exit"
        ] = get_valid_bool(
            saved_game,
            "confirm_unfinished_exit",
            DEFAULT_SETTINGS[
                "game"
            ][
                "confirm_unfinished_exit"
            ]
        )

    # ======================================================
    #                    INTERFACE
    # ======================================================

    saved_interface = saved_settings.get(
        "interface",
        {}
    )

    if isinstance(saved_interface, dict):
        validated[
            "interface"
        ][
            "window_mode"
        ] = get_valid_choice(
            saved_interface,
            "window_mode",
            VALID_WINDOW_MODES,
            DEFAULT_SETTINGS[
                "interface"
            ][
                "window_mode"
            ]
        )

        validated[
            "interface"
        ][
            "windowed_width"
        ] = get_valid_window_size(
            saved_interface,
            "windowed_width",
            DEFAULT_SETTINGS[
                "interface"
            ][
                "windowed_width"
            ],
            MIN_SAVED_WINDOW_WIDTH,
            MAX_SAVED_WINDOW_WIDTH
        )

        validated[
            "interface"
        ][
            "windowed_height"
        ] = get_valid_window_size(
            saved_interface,
            "windowed_height",
            DEFAULT_SETTINGS[
                "interface"
            ][
                "windowed_height"
            ],
            MIN_SAVED_WINDOW_HEIGHT,
            MAX_SAVED_WINDOW_HEIGHT
        )

        interface_boolean_keys = (
            "show_result_details",
            "show_achievement_popups",
            "show_level_up_notification",
            "smooth_scroll",
        )

        for key in interface_boolean_keys:
            validated[
                "interface"
            ][key] = get_valid_bool(
                saved_interface,
                key,
                DEFAULT_SETTINGS[
                    "interface"
                ][key]
            )

    # ======================================================
    #                       AUDIO
    # ======================================================

    saved_audio = saved_settings.get(
        "audio",
        {}
    )

    if isinstance(saved_audio, dict):
        validated[
            "audio"
        ][
            "enabled"
        ] = get_valid_bool(
            saved_audio,
            "enabled",
            DEFAULT_SETTINGS[
                "audio"
            ][
                "enabled"
            ]
        )

        volume_keys = (
            "master_volume",
            "effects_volume",
            "music_volume",
        )

        for key in volume_keys:
            validated[
                "audio"
            ][key] = get_valid_volume(
                saved_audio,
                key,
                DEFAULT_SETTINGS[
                    "audio"
                ][key]
            )

    # ======================================================
    #                     DEVELOPER
    # ======================================================

    saved_developer = saved_settings.get(
        "developer",
        {}
    )

    if isinstance(saved_developer, dict):
        validated[
            "developer"
        ][
            "enabled"
        ] = get_valid_bool(
            saved_developer,
            "enabled",
            DEFAULT_SETTINGS[
                "developer"
            ][
                "enabled"
            ]
        )

    # Загруженные настройки всегда преобразуются
    # в актуальную версию схемы.
    validated["schema_version"] = (
        SETTINGS_SCHEMA_VERSION
    )

    return validated


def apply_window_mode(
    mode,
    remember_current_size=True,
    save_after=True
):
    """
    Применяет оконный или полноэкранный режим.

    При переходе в fullscreen сохраняет последний
    нормальный размер обычного окна.
    """

    global screen
    global WIDTH
    global HEIGHT

    if mode not in VALID_WINDOW_MODES:
        mode = DEFAULT_SETTINGS[
            "interface"
        ][
            "window_mode"
        ]

    # ======================================================
    #                   ПОЛНЫЙ ЭКРАН
    # ======================================================

    if mode == "fullscreen":
        currently_fullscreen = bool(
            screen.get_flags()
            & pygame.FULLSCREEN
        )

        if (
            remember_current_size
            and not currently_fullscreen
        ):
            # Запоминаем размер до пересоздания окна.
            settings[
                "interface"
            ][
                "windowed_width"
            ] = WIDTH

            settings[
                "interface"
            ][
                "windowed_height"
            ] = HEIGHT

        screen = pygame.display.set_mode(
            (
                0,
                0
            ),
            pygame.FULLSCREEN
        )

        WIDTH, HEIGHT = (
            screen.get_size()
        )

    # ======================================================
    #                    ОКОННЫЙ РЕЖИМ
    # ======================================================

    else:
        windowed_width = settings[
            "interface"
        ][
            "windowed_width"
        ]

        windowed_height = settings[
            "interface"
        ][
            "windowed_height"
        ]

        # Повторная защита нужна на случай прямого
        # изменения settings внутри работающей игры.
        windowed_width = max(
            MIN_WIDTH,
            min(
                windowed_width,
                MAX_SAVED_WINDOW_WIDTH
            )
        )

        windowed_height = max(
            MIN_HEIGHT,
            min(
                windowed_height,
                MAX_SAVED_WINDOW_HEIGHT
            )
        )

        screen = pygame.display.set_mode(
            (
                windowed_width,
                windowed_height
            ),
            pygame.RESIZABLE
        )

        WIDTH, HEIGHT = (
            screen.get_size()
        )

    settings[
        "interface"
    ][
        "window_mode"
    ] = mode

    # Плитки хранят pygame.Rect, поэтому после изменения
    # геометрии окна их нужно пересчитать отдельно.
    update_tile_positions()

    if save_after:
        save_progress()


def apply_saved_window_mode():
    """
    Восстанавливает сохранённый режим при запуске.

    Текущий временный размер окна не запоминается,
    потому что настоящий оконный размер уже загружен из JSON.
    """

    saved_mode = settings[
        "interface"
    ][
        "window_mode"
    ]

    apply_window_mode(
        saved_mode,
        remember_current_size=False,
        save_after=False
    )

command_key_pressed = False

# Resize может создавать много событий подряд.
# Время последнего изменения используется для одной
# отложенной записи размера после завершения Resize.
window_resize_save_deadline = None

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

# Действие, подтверждение которого сейчас
# отображает Popup управления данными.
pending_data_action = None

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

# Состояние уведомления о новом уровне.
# Значения должны существовать даже при первом запуске
# без файла сохранения.
level_up_message = ""
level_up_timer = 0
level_up_alpha = 255

# Профиль
player_name = DEFAULT_PLAYER_NAME

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
    Открывает Popup достижений, если уведомления разрешены.

    Сама выдача достижения и награды выполняется раньше
    и от этой визуальной настройки не зависит.
    """

    global current_popup
    global reset_popup_open

    # Настройка блокирует только визуальный Popup.
    if not settings[
        "interface"
    ][
        "show_achievement_popups"
    ]:
        return

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


def fit_text_with_ellipsis(text, font_obj, max_width):
    """
    Сокращает текст многоточием, если он не помещается
    в переданную ширину.
    """

    if font_obj.size(text)[0] <= max_width:
        return text

    ellipsis = "..."

    # Убираем символы с конца, пока строка
    # вместе с многоточием не войдёт в доступную ширину.
    shortened_text = text

    while (
        shortened_text
        and font_obj.size(shortened_text + ellipsis)[0] > max_width
    ):
        shortened_text = shortened_text[:-1]

    return shortened_text.rstrip() + ellipsis


def draw_wrapped_text_limited(
    text,
    font_obj,
    color,
    x,
    y,
    max_width,
    max_lines=2,
    line_gap=4
):
    """
    Рисует текст с переносом строк и ограничивает
    максимальное количество отображаемых строк.
    """

    words = text.split()
    lines = []

    # ======================================================
    #                  ФОРМИРОВАНИЕ СТРОК
    # ======================================================

    while words and len(lines) < max_lines:
        current_line = ""

        while words:
            test_line = (
                words[0]
                if current_line == ""
                else current_line + " " + words[0]
            )

            if font_obj.size(test_line)[0] <= max_width:
                current_line = test_line
                words.pop(0)
            else:
                break

        # Защита для одного слишком длинного слова.
        if current_line == "" and words:
            current_line = fit_text_with_ellipsis(
                words.pop(0),
                font_obj,
                max_width
            )

        # Если это последняя разрешённая строка,
        # добавляем к ней оставшийся текст и сокращаем.
        if len(lines) == max_lines - 1 and words:
            remaining_text = " ".join(
                [current_line] + words
            )

            current_line = fit_text_with_ellipsis(
                remaining_text,
                font_obj,
                max_width
            )

            words.clear()

        lines.append(current_line)

    # ======================================================
    #                    ОТРИСОВКА СТРОК
    # ======================================================

    line_height = font_obj.get_height()

    for index, line in enumerate(lines):
        line_surface = font_obj.render(
            line,
            True,
            color
        )

        screen.blit(
            line_surface,
            (
                x,
                y + index * (line_height + line_gap)
            )
        )


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


def handle_scroll(
    scroll_area,
    direction
):
    """
    Принимает одно событие прокрутки.

    Плавный режим накапливает скорость,
    а прямой сразу изменяет положение контента.
    """

    if not scroll_area["enabled"]:
        return

    smooth_scroll_enabled = settings[
        "interface"
    ][
        "smooth_scroll"
    ]

    # ======================================================
    #                    ПРЯМОЙ РЕЖИМ
    # ======================================================

    if not smooth_scroll_enabled:
        # В прямом режиме не используем ограничение скорости:
        # оно делало одиночный шаг слишком маленьким.
        scroll_area["offset"] += (
            direction
            * SCROLL_DIRECT_STEP
        )

        scroll_area[
            "scroll_velocity"
        ] = 0

        clamp_scroll(
            scroll_area
        )

        scroll_area["bar_timer"] = (
            scroll_area[
                "bar_visible_time"
            ]
        )

        return

    # ======================================================
    #                    ПЛАВНЫЙ РЕЖИМ
    # ======================================================

    scroll_area["scroll_velocity"] += (
        direction
        * scroll_area["scroll_speed"]
        * 2
    )

    scroll_area["bar_timer"] = (
        scroll_area[
            "bar_visible_time"
        ]
    )

    scroll_area["scroll_velocity"] = max(
        -SCROLL_MAX_SPEED,
        min(
            SCROLL_MAX_SPEED,
            scroll_area[
                "scroll_velocity"
            ]
        )
    )


def update_scroll(
    scroll_area
):
    """
    Обновляет положение и анимацию ScrollArea.

    При включённой плавности скорость постепенно затухает.
    При выключенной применяется один раз и сразу обнуляется.
    """

    # ======================================================
    #                   ОБНОВЛЕНИЕ СКОРОСТИ
    # ======================================================

    if abs(
        scroll_area["scroll_velocity"]
    ) < 0.1:
        scroll_area[
            "scroll_velocity"
        ] = 0

    smooth_scroll_enabled = settings[
        "interface"
    ][
        "smooth_scroll"
    ]

    if smooth_scroll_enabled:
        scroll_area[
            "scroll_velocity"
        ] *= scroll_area[
            "scroll_friction"
        ]

    # Скорость сначала применяется к позиции.
    # В неплавном режиме она будет обнулена сразу после этого.
    scroll_area[
        "offset"
    ] += scroll_area[
        "scroll_velocity"
    ]

    if not smooth_scroll_enabled:
        scroll_area[
            "scroll_velocity"
        ] = 0

    clamp_scroll(
        scroll_area
    )

    # ======================================================
    #                 ПРОВЕРКА ГРАНИЦ
    # ======================================================

    if (
        scroll_area["offset"] <= 0
        and scroll_area["scroll_velocity"] < 0
    ):
        scroll_area[
            "scroll_velocity"
        ] = 0

    max_offset = max(
        0,
        (
            scroll_area["content_height"]
            - scroll_area["rect"].height
        )
    )

    if (
        scroll_area["offset"] >= max_offset
        and scroll_area["scroll_velocity"] > 0
    ):
        scroll_area[
            "scroll_velocity"
        ] = 0

    # ======================================================
    #                  АНИМАЦИЯ SCROLLBAR
    # ======================================================

    if scroll_area["bar_timer"] > 0:
        scroll_area["bar_timer"] -= 1

        scroll_area["bar_alpha"] = min(
            255,
            (
                scroll_area["bar_alpha"]
                + 20
            )
        )

    else:
        scroll_area["bar_alpha"] = max(
            0,
            (
                scroll_area["bar_alpha"]
                - scroll_area[
                    "bar_fade_speed"
                ]
            )
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

        "settings": copy.deepcopy(
            settings
        ),
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
    """
    Подготавливает визуальное уведомление о новом уровне.

    Сам уровень рассчитывается через total_xp,
    поэтому отключение сообщения не отменяет повышение.
    """

    global level_up_message
    global level_up_timer
    global level_up_alpha

    if DEBUG_MODE:
        print(
            f"LEVEL UP -> {new_level}"
        )

    # ======================================================
    #                УВЕДОМЛЕНИЕ ОТКЛЮЧЕНО
    # ======================================================

    if not settings[
        "interface"
    ][
        "show_level_up_notification"
    ]:
        # Удаляем возможное старое сообщение,
        # чтобы оно не появилось после смены настройки.
        level_up_message = ""
        level_up_timer = 0
        level_up_alpha = 255
        return

    # ======================================================
    #                УВЕДОМЛЕНИЕ ВКЛЮЧЕНО
    # ======================================================

    level_up_message = (
        f"🎉 НОВЫЙ УРОВЕНЬ!\n"
        f"Уровень {new_level}"
    )

    level_up_timer = (
        LEVEL_UP_TOAST_DURATION
    )
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
    global settings

    try:
        with Path(SAVE_FILE).open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Save root must be a JSON object")

        settings = validate_settings(
            data.get(
                "settings"
            )
        )

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

        saved_player_name = data.get(
            "player_name",
            DEFAULT_PLAYER_NAME
        )

        if (
                isinstance(saved_player_name, str)
                and saved_player_name.strip()
        ):
            player_name = saved_player_name

        else:
            player_name = DEFAULT_PLAYER_NAME

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
        settings = create_default_settings()
        return

    except (json.JSONDecodeError, ValueError, TypeError):
        settings = create_default_settings()
        backup_path = move_invalid_save_aside()

        if DEBUG_MODE and backup_path is not None:
            print(
                "Повреждённое сохранение перемещено:",
                backup_path
            )

    except OSError as error:
        if DEBUG_MODE:
            print("Не удалось загрузить сохранение:", error)


def reset_progress(
    save_after=True
):
    global score
    global highest_balance

    global games_played
    global wins
    global losses

    global current_streak
    global best_streak

    global total_attempts_in_wins
    global tracked_wins_for_attempts

    global games_with_bet
    global all_in_bets_count

    global total_xp
    global last_xp_gained

    global level_up_message
    global level_up_timer
    global level_up_alpha

    global selected_bet
    global current_bet

    global custom_bet_text
    global custom_bet_error
    global custom_bet_active

    global secret_number
    global attempts_left
    global game_over
    global win
    global message
    global tiles
    global game_started

    global result_line_1
    global result_line_2

    global balance_before_bet
    global started_all_in

    global reset_popup_open

    # ======================================================
    #                  ОСНОВНАЯ СТАТИСТИКА
    # ======================================================

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

    # ======================================================
    #                      XP И УРОВЕНЬ
    # ======================================================

    total_xp = 0
    last_xp_gained = 0

    level_up_message = ""
    level_up_timer = 0
    level_up_alpha = 255

    # ======================================================
    #                         СТАВКИ
    # ======================================================

    selected_bet = 0
    current_bet = 0

    custom_bet_text = ""
    custom_bet_error = ""
    custom_bet_active = False

    balance_before_bet = 0
    started_all_in = False

    # ======================================================
    #                   ТЕКУЩАЯ ПАРТИЯ
    # ======================================================

    secret_number = None
    attempts_left = None

    game_over = False
    win = False
    game_started = False

    message = "Выбери число"

    result_line_1 = ""
    result_line_2 = ""

    tiles = []

    # ======================================================
    #                      ДОСТИЖЕНИЯ
    # ======================================================

    for category in ACHIEVEMENTS_DATA.values():
        for achievement in category:
            achievement["completed"] = False

    for key in achievement_stats:
        achievement_stats[key] = 0

    newly_unlocked_achievements.clear()

    reset_popup_open = False

    if save_after:
        save_progress()


def reset_settings(
    save_after=True
):
    """
    Возвращает настройки и данные профиля
    к стандартным значениям.
    """

    global settings
    global player_name

    settings = create_default_settings()

    player_name = DEFAULT_PLAYER_NAME

    # Стандартный оконный режим применяется сразу.
    # Текущий увеличенный размер при этом не запоминается.
    apply_window_mode(
        "windowed",
        remember_current_size=False,
        save_after=False
    )

    if save_after:
        save_progress()


def reset_all_data():
    global current_screen
    global current_popup

    global popup_title
    global popup_text

    reset_progress(
        save_after=False
    )

    reset_settings(
        save_after=False
    )

    current_screen = MENU
    current_popup = None

    popup_title = ""
    popup_text = ""

    save_progress()


def get_menu_buttons():
    """
    Формирует актуальный набор кнопок главного меню.

    Developer Panel добавляется только при разрешении
    соответствующей пользовательской настройки.
    """

    button_width = 320
    button_height = 65
    button_gap = 20

    button_data = [
        ("Играть", BLUE),
        ("Профиль", LIGHT_GRAY),
        ("Достижения", LIGHT_GRAY),
        ("Настройки", LIGHT_GRAY),
    ]

    if settings[
        "developer"
    ][
        "enabled"
    ]:
        button_data.append(
            (
                "Developer-панель",
                YELLOW
            )
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
    return create_button(
        30,
        32,
        150,
        55,
        "Меню",
        LIGHT_GRAY
    )


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
    panel_x = (
        WIDTH
        - PANEL_WIDTH
        - SIDEBAR_MARGIN
    )

    content_height = (
        HEIGHT
        - GAME_HEADER_HEIGHT
    )

    panel_y = (
        GAME_HEADER_HEIGHT
        + (
            content_height
            - BET_PANEL_HEIGHT
        ) // 2
    )

    minimum_panel_y = (
        GAME_HEADER_HEIGHT
        + SIDEBAR_MARGIN
    )

    panel_y = max(
        panel_y,
        minimum_panel_y
    )

    return (
        panel_x,
        panel_y,
        PANEL_WIDTH,
        BET_PANEL_HEIGHT
    )


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
    panel_x, panel_y, panel_width, panel_height = (
        get_bet_panel_position()
    )

    return panel_x - SIDEBAR_MARGIN


def get_game_area_center_x():
    game_area_left = 0
    game_area_right = get_game_area_right()
    return (game_area_left + game_area_right) // 2


def should_confirm_unfinished_exit():
    return (
        settings[
            "game"
        ][
            "confirm_unfinished_exit"
        ]
        and game_started
        and not game_over
    )


def leave_game_to_menu():
    global current_screen
    global current_popup

    global secret_number
    global attempts_left

    global game_over
    global win
    global game_started

    global message
    global tiles

    global current_bet
    global balance_before_bet
    global started_all_in

    global result_line_1
    global result_line_2

    global custom_bet_active
    global custom_bet_error

    current_screen = MENU
    current_popup = None

    secret_number = None
    attempts_left = None

    game_over = False
    win = False
    game_started = False

    message = "Выбери число"
    tiles = []

    current_bet = selected_bet

    balance_before_bet = 0
    started_all_in = False

    result_line_1 = ""
    result_line_2 = ""

    custom_bet_active = False
    custom_bet_error = ""

    save_progress()


def request_leave_game():
    global current_popup

    if should_confirm_unfinished_exit():
        current_popup = (
            POPUP_UNFINISHED_EXIT
        )
        return

    leave_game_to_menu()


def get_can_change_bet():
    return not game_started or game_over


def get_visible_bet():
    if game_started and not game_over:
        return current_bet

    return selected_bet


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
    panel_x, panel_y, panel_width, panel_height = (
        get_bet_panel_position()
    )

    input_width = 115
    input_height = 40

    apply_button_width = 55
    gap_between = 10

    total_width = (
        input_width
        + gap_between
        + apply_button_width
    )

    input_x = (
        panel_x
        + (
            panel_width
            - total_width
        ) // 2
    )

    input_y = panel_y + 332

    return pygame.Rect(
        input_x,
        input_y,
        input_width,
        input_height
    )


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

def get_all_in_bet_button():
    panel_x, panel_y, panel_width, panel_height = (
        get_bet_panel_position()
    )

    button_width = 220
    button_height = 42

    button_x = (
        panel_x
        + (
            panel_width
            - button_width
        ) // 2
    )

    button_y = panel_y + 455

    can_use_all_in = (
        get_can_change_bet()
        and score > 0
    )

    if (
        can_use_all_in
        and selected_bet == score
    ):
        button_color = ORANGE

    elif can_use_all_in:
        button_color = WHITE

    else:
        button_color = GRAY

    button = create_button(
        button_x,
        button_y,
        button_width,
        button_height,
        "Поставить всё",
        button_color
    )

    button["active"] = can_use_all_in

    return button


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
    """
    Рисует неблокирующее Toast-уведомление нового уровня.

    Если открыт другой Popup, таймер приостанавливается,
    чтобы уведомление стало видно после его закрытия.
    """

    global level_up_timer
    global level_up_alpha

    if level_up_timer <= 0:
        return

    # Popup достижений рисуется поверх игры.
    # Приостанавливаем Toast, чтобы он не исчез за затемнением.
    if current_popup is not None:
        return

    # ======================================================
    #                  ОБНОВЛЕНИЕ ТАЙМЕРА
    # ======================================================

    level_up_timer -= 1

    if (
        level_up_timer
        > LEVEL_UP_TOAST_FADE_DURATION
    ):
        level_up_alpha = 255

    else:
        level_up_alpha = int(
            255
            * level_up_timer
            / LEVEL_UP_TOAST_FADE_DURATION
        )

    # ======================================================
    #                  ГЕОМЕТРИЯ TOAST
    # ======================================================

    center_x = get_game_area_center_x()

    toast_x = (
        center_x
        - LEVEL_UP_TOAST_WIDTH // 2
    )

    toast_y = (
        GAME_HEADER_HEIGHT
        + LEVEL_UP_TOAST_TOP_MARGIN
    )

    toast_rect = pygame.Rect(
        toast_x,
        toast_y,
        LEVEL_UP_TOAST_WIDTH,
        LEVEL_UP_TOAST_HEIGHT
    )

    # Отдельная прозрачная поверхность позволяет
    # одновременно затухать фону, рамке и тексту.
    toast_surface = pygame.Surface(
        (
            LEVEL_UP_TOAST_WIDTH,
            LEVEL_UP_TOAST_HEIGHT
        ),
        pygame.SRCALPHA
    )

    pygame.draw.rect(
        toast_surface,
        (
            *LEVEL_UP_TOAST_BACKGROUND,
            level_up_alpha
        ),
        (
            0,
            0,
            LEVEL_UP_TOAST_WIDTH,
            LEVEL_UP_TOAST_HEIGHT
        ),
        border_radius=LEVEL_UP_TOAST_RADIUS
    )

    pygame.draw.rect(
        toast_surface,
        (
            *LEVEL_UP_TOAST_BORDER,
            level_up_alpha
        ),
        (
            0,
            0,
            LEVEL_UP_TOAST_WIDTH,
            LEVEL_UP_TOAST_HEIGHT
        ),
        3,
        border_radius=LEVEL_UP_TOAST_RADIUS
    )

    # ======================================================
    #                     ТЕКСТ TOAST
    # ======================================================

    lines = level_up_message.split(
        "\n"
    )

    title_text = (
        lines[0]
        if lines
        else "НОВЫЙ УРОВЕНЬ!"
    )

    level_text = (
        lines[1]
        if len(lines) > 1
        else ""
    )

    title_surface = font.render(
        title_text,
        True,
        LEVEL_UP_TOAST_BORDER
    )

    title_surface.set_alpha(
        level_up_alpha
    )

    title_rect = title_surface.get_rect(
        center=(
            LEVEL_UP_TOAST_WIDTH // 2,
            34
        )
    )

    toast_surface.blit(
        title_surface,
        title_rect
    )

    level_surface = small_font.render(
        level_text,
        True,
        DARK_GRAY
    )

    level_surface.set_alpha(
        level_up_alpha
    )

    level_rect = level_surface.get_rect(
        center=(
            LEVEL_UP_TOAST_WIDTH // 2,
            72
        )
    )

    toast_surface.blit(
        level_surface,
        level_rect
    )

    screen.blit(
        toast_surface,
        toast_rect
    )


def draw_custom_bet_input():
    panel_x, panel_y, panel_width, panel_height = get_bet_panel_position()

    label_y = panel_y + 298

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
    panel_x, panel_y, panel_width, panel_height = (
        get_bet_panel_position()
    )

    panel_rect = pygame.Rect(
        panel_x,
        panel_y,
        panel_width,
        panel_height
    )

    pygame.draw.rect(
        screen,
        LIGHT_GRAY,
        panel_rect,
        border_radius=14
    )

    # ======================================================
    #                  ЗАГОЛОВОК ПАНЕЛИ
    # ======================================================

    if get_can_change_bet():
        title = "Выбор ставки"
        title_color = BLACK

    else:
        title = "Ставка заблокирована"
        title_color = DARK_GRAY

    title_text = small_font.render(
        title,
        True,
        title_color
    )

    title_x = (
        panel_x
        + panel_width // 2
        - title_text.get_width() // 2
    )

    title_y = panel_y + 18

    screen.blit(
        title_text,
        (
            title_x,
            title_y
        )
    )

    # ======================================================
    #                ГОТОВЫЕ ВАРИАНТЫ СТАВКИ
    # ======================================================

    bet_buttons = get_bet_buttons()

    for button in bet_buttons:
        draw_button(
            button,
            small_font
        )

    # ======================================================
    #                     РАЗДЕЛИТЕЛЬ
    # ======================================================

    pygame.draw.line(
        screen,
        (190, 190, 190),
        (
            panel_x + 18,
            panel_y + 280
        ),
        (
            panel_x + panel_width - 18,
            panel_y + 280
        ),
        2
    )

    # ======================================================
    #                     СВОЯ СТАВКА
    # ======================================================

    draw_custom_bet_input()

    # ======================================================
    #                    ПОСТАВИТЬ ВСЁ
    # ======================================================

    all_in_button = get_all_in_bet_button()

    draw_button(
        all_in_button,
        small_font
    )


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


def get_settings_back_button():
    return create_button(
        30,
        32,
        150,
        55,
        "Назад",
        LIGHT_GRAY
    )


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


settings_control_rects = {}

settings_slider_rects = {}

# Ключ ползунка, который пользователь
# сейчас удерживает мышью.
active_settings_slider = None

# Исходное значение нужно, чтобы не записывать
# сохранение при клике без фактического изменения.
settings_slider_drag_start_value = None

SETTINGS_TOGGLE_PATHS = {
    "Включить звук": (
        "audio",
        "enabled",
    ),

    "Подтверждение выхода из партии": (
        "game",
        "confirm_unfinished_exit",
    ),

    "Подробный расчёт результата": (
        "interface",
        "show_result_details",
    ),

    "Уведомления о достижениях": (
        "interface",
        "show_achievement_popups",
    ),

    "Уведомления о новом уровне": (
        "interface",
        "show_level_up_notification",
    ),

    "Плавная прокрутка": (
        "interface",
        "smooth_scroll",
    ),

    "Developer Panel": (
        "developer",
        "enabled",
    ),
}

SETTINGS_OPTION_CONFIGS = {
    "Запуск игры": {
        "category": "game",
        "key": "start_difficulty",

        "options": (
            (
                "ask",
                "Спрашивать"
            ),
            (
                "easy",
                "Лёгкая"
            ),
            (
                "medium",
                "Средняя"
            ),
            (
                "hard",
                "Сложная"
            ),
        ),
    },

    "Режим окна": {
        "category": "interface",
        "key": "window_mode",

        "options": (
            (
                "windowed",
                "Оконный"
            ),
            (
                "fullscreen",
                "Полный экран"
            ),
        ),
    },
}


SETTINGS_SLIDER_PATHS = {
    "Общая громкость": (
        "audio",
        "master_volume",
    ),

    "Громкость эффектов": (
        "audio",
        "effects_volume",
    ),

    "Громкость музыки": (
        "audio",
        "music_volume",
    ),
}


SETTINGS_DATA_ACTIONS = {
    "Сбросить прогресс": {
        "action": "reset_progress",
        "button_text": "Сбросить",
        "button_color": YELLOW,
        "popup_title": "Сбросить прогресс?",
        "popup_lines": (
            "Будут удалены статистика, баланс, XP,",
            "уровень, достижения, титулы и рекорды.",
            "Настройки и имя пользователя сохранятся.",
        ),
        "confirm_text": "Сбросить",
        "confirm_color": YELLOW,
    },

    "Сбросить настройки": {
        "action": "reset_settings",
        "button_text": "Сбросить",
        "button_color": ORANGE,
        "popup_title": "Сбросить настройки?",
        "popup_lines": (
            "Будут восстановлены стандартные настройки,",
            "сброшены имя пользователя и Developer Panel.",
            "Игровой прогресс и достижения сохранятся.",
        ),
        "confirm_text": "Сбросить",
        "confirm_color": ORANGE,
    },

    "Удалить все данные": {
        "action": "reset_all",
        "button_text": "Удалить всё",
        "button_color": RED,
        "popup_title": "Удалить все данные?",
        "popup_lines": (
            "Будут безвозвратно удалены весь прогресс,",
            "достижения, настройки и данные профиля.",
            "Игра вернётся в состояние первого запуска.",
        ),
        "confirm_text": "Удалить всё",
        "confirm_color": RED,
    },
}


DIFFICULTY_SETTING_TO_NAME = {
    "easy": "Лёгкая",
    "medium": "Средняя",
    "hard": "Сложная",
}


def draw_settings_toggle(
    toggle_rect,
    value,
    enabled=True
):
    if not enabled:
        track_color = (
            185,
            185,
            185
        )

    elif value:
        track_color = GREEN

    else:
        track_color = GRAY

    pygame.draw.rect(
        screen,
        track_color,
        toggle_rect,
        border_radius=(
            SETTINGS_TOGGLE_HEIGHT // 2
        )
    )

    if value:
        knob_x = (
            toggle_rect.right
            - SETTINGS_TOGGLE_KNOB_SIZE
            - 3
        )

    else:
        knob_x = toggle_rect.x + 3

    knob_y = (
        toggle_rect.centery
        - SETTINGS_TOGGLE_KNOB_SIZE // 2
    )

    knob_rect = pygame.Rect(
        knob_x,
        knob_y,
        SETTINGS_TOGGLE_KNOB_SIZE,
        SETTINGS_TOGGLE_KNOB_SIZE
    )

    pygame.draw.ellipse(
        screen,
        WHITE,
        knob_rect
    )

    pygame.draw.ellipse(
        screen,
        (
            150,
            150,
            150
        ),
        knob_rect,
        1
    )

    if value:
        state_text = "Вкл"
    else:
        state_text = "Выкл"

    if enabled:
        state_color = DARK_GRAY
    else:
        state_color = GRAY

    state_surface = small_font.render(
        state_text,
        True,
        state_color
    )

    state_rect = state_surface.get_rect(
        right=(
            toggle_rect.x
            - SETTINGS_TOGGLE_TEXT_GAP
        ),
        centery=toggle_rect.centery
    )

    screen.blit(
        state_surface,
        state_rect
    )


def draw_settings_option_selector(
    row_x,
    row_y,
    row_width,
    setting_key,
    options,
    current_value
):
    """
    Рисует набор взаимоисключающих вариантов.

    Ширина каждой кнопки рассчитывается по её тексту,
    поэтому длинные подписи не выходят за границы.
    """

    # ======================================================
    #                    РАСЧЁТ ШИРИНЫ
    # ======================================================

    option_widths = []

    for option_value, option_label in options:
        text_width = small_font.size(
            option_label
        )[0]

        option_width = max(
            SETTINGS_OPTION_MIN_WIDTH,
            (
                text_width
                + SETTINGS_OPTION_PADDING_X * 2
            )
        )

        option_widths.append(
            option_width
        )

    total_width = (
        sum(option_widths)
        + (
            len(options) - 1
        )
        * SETTINGS_OPTION_GAP
    )

    # Вся группа прижимается к правому краю строки.
    start_x = (
        row_x
        + row_width
        - total_width
    )

    button_y = (
        row_y
        + (
            SETTINGS_ROW_HEIGHT
            - SETTINGS_OPTION_HEIGHT
        ) // 2
    )

    # ======================================================
    #                  ОТРИСОВКА ВАРИАНТОВ
    # ======================================================

    current_x = start_x

    for (
        option_value,
        option_label
    ), option_width in zip(
        options,
        option_widths
    ):
        # Активный вариант выделяется синим.
        if option_value == current_value:
            button_color = BLUE
        else:
            button_color = WHITE

        option_button = create_button(
            current_x,
            button_y,
            option_width,
            SETTINGS_OPTION_HEIGHT,
            option_label,
            button_color
        )

        draw_button(
            option_button,
            small_font
        )

        # Составной ключ отличает варианты
        # одного и того же параметра.
        control_id = (
            "option",
            setting_key,
            option_value
        )

        settings_control_rects[
            control_id
        ] = option_button["rect"]

        current_x += (
            option_width
            + SETTINGS_OPTION_GAP
        )


def draw_settings_slider(
    row_x,
    row_y,
    row_width,
    setting_key,
    current_value,
    enabled=True
):
    """
    Рисует ползунок настройки в диапазоне 0–100.

    При отключённом звуке Slider остаётся видимым,
    но становится неактивным.
    """

    # ======================================================
    #                    ГЕОМЕТРИЯ SLIDER
    # ======================================================

    track_right = (
        row_x
        + row_width
        - SETTINGS_SLIDER_PERCENT_WIDTH
        - SETTINGS_SLIDER_PERCENT_GAP
    )

    track_left = (
        track_right
        - SETTINGS_SLIDER_WIDTH
    )

    track_center_y = (
        row_y
        + SETTINGS_ROW_HEIGHT // 2
    )

    track_rect = pygame.Rect(
        track_left,
        (
            track_center_y
            - SETTINGS_SLIDER_TRACK_HEIGHT // 2
        ),
        SETTINGS_SLIDER_WIDTH,
        SETTINGS_SLIDER_TRACK_HEIGHT
    )

    # Значение дополнительно ограничивается перед отрисовкой,
    # даже несмотря на валидацию при загрузке.
    safe_value = max(
        MIN_VOLUME,
        min(
            current_value,
            MAX_VOLUME
        )
    )

    value_ratio = (
        (safe_value - MIN_VOLUME)
        / (MAX_VOLUME - MIN_VOLUME)
    )

    knob_center_x = (
        track_rect.left
        + round(
            track_rect.width * value_ratio
        )
    )

    # ======================================================
    #                  ВИЗУАЛЬНОЕ СОСТОЯНИЕ
    # ======================================================

    if enabled:
        track_color = SETTINGS_SLIDER_TRACK_COLOR
        fill_color = SETTINGS_SLIDER_FILL_COLOR
        knob_color = SETTINGS_SLIDER_KNOB_COLOR
        knob_border_color = (
            SETTINGS_SLIDER_KNOB_BORDER_COLOR
        )
        percent_color = DARK_GRAY

    else:
        track_color = (
            205,
            205,
            205
        )
        fill_color = (
            165,
            165,
            165
        )
        knob_color = (
            225,
            225,
            225
        )
        knob_border_color = (
            185,
            185,
            185
        )
        percent_color = GRAY

    # ======================================================
    #                     ШКАЛА SLIDER
    # ======================================================

    pygame.draw.rect(
        screen,
        track_color,
        track_rect,
        border_radius=(
            SETTINGS_SLIDER_TRACK_HEIGHT // 2
        )
    )

    fill_width = max(
        0,
        knob_center_x - track_rect.left
    )

    if fill_width > 0:
        fill_rect = pygame.Rect(
            track_rect.left,
            track_rect.top,
            fill_width,
            track_rect.height
        )

        pygame.draw.rect(
            screen,
            fill_color,
            fill_rect,
            border_radius=(
                SETTINGS_SLIDER_TRACK_HEIGHT // 2
            )
        )

    # ======================================================
    #                    БЕГУНОК SLIDER
    # ======================================================

    knob_rect = pygame.Rect(
        0,
        0,
        SETTINGS_SLIDER_KNOB_SIZE,
        SETTINGS_SLIDER_KNOB_SIZE
    )

    knob_rect.center = (
        knob_center_x,
        track_center_y
    )

    pygame.draw.ellipse(
        screen,
        knob_color,
        knob_rect
    )

    pygame.draw.ellipse(
        screen,
        knob_border_color,
        knob_rect,
        1
    )

    # ======================================================
    #                       ПРОЦЕНТ
    # ======================================================

    percent_surface = small_font.render(
        f"{safe_value}%",
        True,
        percent_color
    )

    percent_rect = percent_surface.get_rect(
        left=(
            track_right
            + SETTINGS_SLIDER_PERCENT_GAP
        ),
        centery=track_center_y
    )

    screen.blit(
        percent_surface,
        percent_rect
    )

    # Область клика выше самой тонкой шкалы,
    # чтобы по Slider было удобно попадать мышью.
    hit_rect = pygame.Rect(
        track_rect.left
        - SETTINGS_SLIDER_KNOB_SIZE // 2,
        row_y,
        track_rect.width
        + SETTINGS_SLIDER_KNOB_SIZE,
        SETTINGS_ROW_HEIGHT
    )

    settings_slider_rects[
        setting_key
    ] = {
        "track": track_rect,
        "hit": hit_rect,
        "enabled": enabled,
    }


def get_settings_sections():
    return (
        (
            "Игра",
            (
                "Запуск игры",
                "Подтверждение выхода из партии",
            )
        ),

        (
            "Интерфейс",
            (
                "Режим окна",
                "Подробный расчёт результата",
                "Уведомления о достижениях",
                "Уведомления о новом уровне",
                "Плавная прокрутка",
            )
        ),

        (
            "Звук",
            (
                "Включить звук",
                "Общая громкость",
                "Громкость эффектов",
                "Громкость музыки",
            )
        ),

        (
            "Данные",
            (
                "Сбросить прогресс",
                "Сбросить настройки",
                "Удалить все данные",
            )
        ),

        (
            "Для разработчика",
            (
                "Developer Panel",
            )
        ),
    )


def get_settings_section_height(
    items_count
):
    return (
        SETTINGS_SECTION_PADDING_TOP
        + SETTINGS_SECTION_TITLE_HEIGHT
        + items_count * SETTINGS_ROW_HEIGHT
        + SETTINGS_SECTION_PADDING_BOTTOM
    )


def draw_settings_section(
    x,
    y,
    width,
    title,
    items
):
    section_height = (
        get_settings_section_height(
            len(items)
        )
    )

    section_rect = pygame.Rect(
        x,
        y,
        width,
        section_height
    )

    pygame.draw.rect(
        screen,
        LIGHT_GRAY,
        section_rect,
        border_radius=SETTINGS_SECTION_RADIUS
    )

    title_surface = font.render(
        title,
        True,
        BLACK
    )

    screen.blit(
        title_surface,
        (
            x + SETTINGS_SECTION_PADDING_X,
            y + SETTINGS_SECTION_PADDING_TOP
        )
    )

    row_y = (
        y
        + SETTINGS_SECTION_PADDING_TOP
        + SETTINGS_SECTION_TITLE_HEIGHT
    )

    for index, item in enumerate(items):
        current_row_y = (
            row_y
            + index * SETTINGS_ROW_HEIGHT
        )

        if index > 0:
            pygame.draw.line(
                screen,
                (200, 200, 200),
                (
                    x + SETTINGS_SECTION_PADDING_X,
                    current_row_y
                ),
                (
                    x
                    + width
                    - SETTINGS_SECTION_PADDING_X,
                    current_row_y
                ),
                1
            )

        item_color = DARK_GRAY

        if (
            item in SETTINGS_SLIDER_PATHS
            and not settings[
                "audio"
            ][
                "enabled"
            ]
        ):
            item_color = GRAY

        item_surface = small_font.render(
            item,
            True,
            item_color
        )

        item_rect = item_surface.get_rect(
            left=(
                x
                + SETTINGS_SECTION_PADDING_X
            ),
            centery=(
                current_row_y
                + SETTINGS_ROW_HEIGHT // 2
            )
        )

        screen.blit(
            item_surface,
            item_rect
        )

        setting_path = (
            SETTINGS_TOGGLE_PATHS.get(
                item
            )
        )

        if setting_path is not None:
            category, key = setting_path

            toggle_rect = pygame.Rect(
                (
                        x
                        + width
                        - SETTINGS_SECTION_PADDING_X
                        - SETTINGS_TOGGLE_WIDTH
                ),
                (
                        current_row_y
                        + (
                                SETTINGS_ROW_HEIGHT
                                - SETTINGS_TOGGLE_HEIGHT
                        ) // 2
                ),
                SETTINGS_TOGGLE_WIDTH,
                SETTINGS_TOGGLE_HEIGHT
            )

            # Полный путь нужен, потому что в разных
            # категориях могут существовать одинаковые ключи.
            control_id = (
                "toggle",
                category,
                key
            )

            settings_control_rects[
                control_id
            ] = toggle_rect

            draw_settings_toggle(
                toggle_rect,
                settings[
                    category
                ][
                    key
                ]
            )

        option_config = (
            SETTINGS_OPTION_CONFIGS.get(
                item
            )
        )

        if option_config is not None:
            category = option_config[
                "category"
            ]

            key = option_config[
                "key"
            ]

            options = option_config[
                "options"
            ]

            row_control_x = (
                x
                + SETTINGS_SECTION_PADDING_X
            )

            row_control_width = (
                width
                - SETTINGS_SECTION_PADDING_X * 2
            )

            draw_settings_option_selector(
                row_control_x,
                current_row_y,
                row_control_width,
                key,
                options,
                settings[
                    category
                ][
                    key
                ]
            )

        slider_path = (
            SETTINGS_SLIDER_PATHS.get(
                item
            )
        )

        if slider_path is not None:
            category, key = slider_path

            row_control_x = (
                x
                + SETTINGS_SECTION_PADDING_X
            )

            row_control_width = (
                width
                - SETTINGS_SECTION_PADDING_X * 2
            )

            draw_settings_slider(
                row_control_x,
                current_row_y,
                row_control_width,
                key,
                settings[
                    category
                ][
                    key
                ],
                enabled=settings[
                    "audio"
                ][
                    "enabled"
                ]
            )

        data_action_config = (
            SETTINGS_DATA_ACTIONS.get(
                item
            )
        )

        if data_action_config is not None:
            action = data_action_config[
                "action"
            ]

            button_x = (
                x
                + width
                - SETTINGS_SECTION_PADDING_X
                - SETTINGS_DATA_BUTTON_WIDTH
            )

            button_y = (
                current_row_y
                + (
                    SETTINGS_ROW_HEIGHT
                    - SETTINGS_DATA_BUTTON_HEIGHT
                ) // 2
            )

            data_button = create_button(
                button_x,
                button_y,
                SETTINGS_DATA_BUTTON_WIDTH,
                SETTINGS_DATA_BUTTON_HEIGHT,
                data_action_config[
                    "button_text"
                ],
                data_action_config[
                    "button_color"
                ]
            )

            draw_button(
                data_button,
                small_font
            )

            control_id = (
                "data_action",
                action
            )

            settings_control_rects[
                control_id
            ] = data_button["rect"]

    return section_height


def draw_settings_screen():
    """
    Рисует экран настроек и заново рассчитывает
    области всех интерактивных элементов.
    """

    settings_control_rects.clear()
    settings_slider_rects.clear()

    screen.fill(WHITE)

    # ======================================================
    #                  ОБЛАСТЬ ПРОКРУТКИ
    # ======================================================

    settings_viewport = pygame.Rect(
        0,
        SETTINGS_HEADER_HEIGHT,
        WIDTH,
        HEIGHT - SETTINGS_HEADER_HEIGHT
    )

    settings_scroll["rect"] = pygame.Rect(
        WIDTH - 25,
        settings_viewport.top,
        8,
        settings_viewport.height
    )

    settings_scroll["active_rect"] = (
        settings_viewport.copy()
    )

    settings_scroll["bar_x"] = (
        WIDTH - 25
    )

    settings_scroll["bar_top"] = (
        settings_viewport.top + 25
    )

    settings_scroll["bar_bottom"] = 25

    clamp_scroll(
        settings_scroll
    )

    scroll_y = settings_scroll["offset"]

    screen.set_clip(
        settings_viewport
    )

    # ======================================================
    #                    ШИРИНА КОНТЕНТА
    # ======================================================

    content_width = min(
        SETTINGS_CONTENT_WIDTH,
        (
            WIDTH
            - SETTINGS_SIDE_PADDING * 2
        )
    )

    content_x = (
        WIDTH // 2
        - content_width // 2
    )

    content_y = (
        SETTINGS_HEADER_HEIGHT
        + SETTINGS_CONTENT_TOP_MARGIN
        - scroll_y
    )

    # ======================================================
    #                         СЕКЦИИ
    # ======================================================

    sections = get_settings_sections()

    for title, items in sections:
        section_height = draw_settings_section(
            content_x,
            content_y,
            content_width,
            title,
            items
        )

        content_y += (
            section_height
            + SETTINGS_SECTION_GAP
        )

    # Последний промежуток между секциями
    # не входит в настоящую высоту контента.
    content_y -= SETTINGS_SECTION_GAP

    settings_scroll["content_height"] = max(
        0,
        (
            content_y
            + scroll_y
            + SETTINGS_CONTENT_BOTTOM_MARGIN
            - SETTINGS_HEADER_HEIGHT
        )
    )

    clamp_scroll(
        settings_scroll
    )

    screen.set_clip(None)

    # ======================================================
    #                       SCROLLBAR
    # ======================================================

    draw_scrollbar(
        settings_scroll
    )

    # ======================================================
    #                         HEADER
    # ======================================================

    header_rect = pygame.Rect(
        0,
        0,
        WIDTH,
        SETTINGS_HEADER_HEIGHT
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
            SETTINGS_HEADER_HEIGHT - 1
        ),
        (
            WIDTH,
            SETTINGS_HEADER_HEIGHT - 1
        ),
        2
    )

    draw_center_text(
        "Настройки",
        title_font,
        BLACK,
        35
    )

    back_button = (
        get_settings_back_button()
    )

    draw_button(
        back_button,
        font
    )


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

    # ======================================================
    #                  ОБЛАСТЬ ПРОКРУТКИ
    # ======================================================

    profile_viewport = pygame.Rect(
        0,
        PROFILE_HEADER_HEIGHT,
        WIDTH,
        HEIGHT - PROFILE_HEADER_HEIGHT
    )

    profile_scroll["rect"] = pygame.Rect(
        WIDTH - 25,
        profile_viewport.top,
        8,
        profile_viewport.height
    )

    profile_scroll["active_rect"] = (
        profile_viewport.copy()
    )

    profile_scroll["bar_x"] = WIDTH - 25

    profile_scroll["bar_top"] = (
            profile_viewport.top + 25
    )

    profile_scroll["bar_bottom"] = 25

    clamp_scroll(profile_scroll)

    scroll_y = profile_scroll["offset"]

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

    profile_scroll["content_height"] = max(
        0,
        (
            y
            + scroll_y
            + 60
            - PROFILE_HEADER_HEIGHT
        )
    )

    clamp_scroll(profile_scroll)

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

    # ======================================================
    #                  ОБЛАСТЬ ПРОКРУТКИ
    # ======================================================

    content_viewport = pygame.Rect(
        0,
        HEADER_HEIGHT,
        WIDTH,
        HEIGHT - HEADER_HEIGHT
    )

    achievement_scroll["rect"] = pygame.Rect(
        WIDTH - 25,
        content_viewport.top,
        8,
        content_viewport.height
    )

    achievement_scroll["active_rect"] = (
        content_viewport.copy()
    )

    achievement_scroll["bar_x"] = (
        WIDTH - 25
    )

    achievement_scroll["bar_top"] = (
        content_viewport.top + 25
    )

    achievement_scroll["bar_bottom"] = 25

    clamp_scroll(
        achievement_scroll
    )

    # ======================================================
    #              АДАПТИВНАЯ ШИРИНА КОНТЕНТА
    # ======================================================

    category_container_x = SCREEN_SIDE_MARGIN

    category_container_width = max(
        0,
        WIDTH - SCREEN_SIDE_MARGIN * 2
    )

    grid_width = max(
        0,
        category_container_width
        - CATEGORY_CONTAINER_PADDING_LEFT
        - CATEGORY_CONTAINER_PADDING_RIGHT
    )

    card_width = max(
        1,
        (
                grid_width
                - CARD_COLUMN_SPACING * (CARD_COLUMNS - 1)
        ) // CARD_COLUMNS
    )

    card_x = (
            category_container_x
            + CATEGORY_CONTAINER_PADDING_LEFT
    )

    scroll_y = (
        achievement_scroll["offset"]
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
            category_container_x,
            category_content_y - CATEGORY_CONTAINER_PADDING_TOP,
            category_container_width,
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
                    card_width + CARD_COLUMN_SPACING
            ) * column

            draw_achievement_card(
                current_x,
                card_y,
                card_width,
                achievement
            )

            column += 1

            if column >= CARD_COLUMNS:
                column = 0

                card_y += CARD_HEIGHT + CARD_SPACING

        if column != 0:
            card_y += CARD_HEIGHT + CARD_SPACING

        card_y += CATEGORY_SPACING

    achievement_scroll["content_height"] = max(
        0,
        (
                card_y
                + scroll_y
                - HEADER_HEIGHT
        )
    )

    clamp_scroll(
        achievement_scroll
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

def draw_achievement_card(x, y, card_width, achievement):
    """
    Рисует адаптивную карточку достижения.

    Ширина карточки рассчитывается экраном достижений,
    а высота пока остаётся фиксированной.
    """

    # ---------- Container ----------

    card_rect = pygame.Rect(
        x,
        y,
        card_width,
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

    # ---------- Text Colors ----------

    title_color = BLACK
    description_color = DARK_GRAY

    if achievement.get("type") == "hidden":
        title_color = WHITE
        description_color = LIGHT_GRAY

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

    # ======================================================
    #              АДАПТИВНЫЙ ЗАГОЛОВОК
    # ======================================================

    title_x = card_rect.left + TITLE_X

    title_max_width = max(
        40,
        progress_rect.left - title_x - 15
    )

    title_text = achievement["title"]
    title_font = font

    # Сначала пробуем обычный шрифт заголовка.
    # Если места недостаточно, используем меньший.
    if title_font.size(title_text)[0] > title_max_width:
        title_font = small_font

    title_text = fit_text_with_ellipsis(
        title_text,
        title_font,
        title_max_width
    )

    title_surface = title_font.render(
        title_text,
        True,
        title_color
    )

    screen.blit(
        title_surface,
        (
            title_x,
            content_y + TITLE_Y
        )
    )

    # ---------- Description ----------

    description_max_width = max(
        40,
        card_width
        - DESCRIPTION_X
        - CARD_RARITY_WIDTH
        - 20
    )

    draw_wrapped_text_limited(
        achievement["description"],
        small_font,
        description_color,
        card_rect.left + DESCRIPTION_X,
        content_y + DESCRIPTION_Y,
        description_max_width,
        max_lines=3
    )

    # ---------- Progress Bar ----------

    bar_x = card_rect.left + PROGRESS_BAR_X
    bar_y = content_y + PROGRESS_BAR_Y

    bar_width = max(
        1,
        card_width
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


def get_unfinished_exit_popup_layout():
    popup_width = 600
    popup_height = 300

    popup_rect = pygame.Rect(
        WIDTH // 2 - popup_width // 2,
        HEIGHT // 2 - popup_height // 2,
        popup_width,
        popup_height
    )

    button_width = 180
    button_height = 52
    button_gap = 25

    buttons_width = (
        button_width * 2
        + button_gap
    )

    buttons_x = (
        popup_rect.centerx
        - buttons_width // 2
    )

    buttons_y = (
        popup_rect.bottom
        - 82
    )

    stay_button = create_button(
        buttons_x,
        buttons_y,
        button_width,
        button_height,
        "Остаться",
        LIGHT_GRAY
    )

    leave_button = create_button(
        (
            buttons_x
            + button_width
            + button_gap
        ),
        buttons_y,
        button_width,
        button_height,
        "Выйти",
        RED
    )

    return {
        "popup_rect": popup_rect,
        "stay_button": stay_button,
        "leave_button": leave_button,
    }


def draw_unfinished_exit_popup():
    layout = (
        get_unfinished_exit_popup_layout()
    )

    popup_rect = layout["popup_rect"]

    pygame.draw.rect(
        screen,
        WHITE,
        popup_rect,
        border_radius=20
    )

    pygame.draw.rect(
        screen,
        DARK_GRAY,
        popup_rect,
        2,
        border_radius=20
    )

    draw_center_text(
        "Выйти из партии?",
        title_font,
        BLACK,
        popup_rect.y + 42
    )

    draw_center_text(
        "Текущая незавершённая партия будет отменена.",
        small_font,
        DARK_GRAY,
        popup_rect.y + 115
    )

    draw_center_text(
        "Статистика, баланс и ставка не изменятся.",
        small_font,
        DARK_GRAY,
        popup_rect.y + 150
    )

    draw_button(
        layout["stay_button"],
        font
    )

    draw_button(
        layout["leave_button"],
        font
    )


def get_data_reset_popup_layout():
    """
    Рассчитывает геометрию Popup подтверждения
    управления данными.
    """

    popup_rect = pygame.Rect(
        0,
        0,
        DATA_RESET_POPUP_WIDTH,
        DATA_RESET_POPUP_HEIGHT
    )

    popup_rect.center = (
        WIDTH // 2,
        HEIGHT // 2
    )

    buttons_width = (
        DATA_RESET_POPUP_BUTTON_WIDTH * 2
        + DATA_RESET_POPUP_BUTTON_GAP
    )

    buttons_x = (
        popup_rect.centerx
        - buttons_width // 2
    )

    buttons_y = (
        popup_rect.bottom
        - DATA_RESET_POPUP_BUTTON_HEIGHT
        - 35
    )

    cancel_button = create_button(
        buttons_x,
        buttons_y,
        DATA_RESET_POPUP_BUTTON_WIDTH,
        DATA_RESET_POPUP_BUTTON_HEIGHT,
        "Отмена",
        LIGHT_GRAY
    )

    return {
        "popup_rect": popup_rect,
        "cancel_button": cancel_button,
        "confirm_button_x": (
            buttons_x
            + DATA_RESET_POPUP_BUTTON_WIDTH
            + DATA_RESET_POPUP_BUTTON_GAP
        ),
        "buttons_y": buttons_y,
    }


def draw_data_reset_popup():
    """
    Рисует подтверждение выбранного действия
    без выполнения самого сброса.
    """

    config = (
        get_pending_data_action_config()
    )

    if config is None:
        close_data_reset_popup()
        return

    layout = (
        get_data_reset_popup_layout()
    )

    popup_rect = layout[
        "popup_rect"
    ]

    pygame.draw.rect(
        screen,
        WHITE,
        popup_rect,
        border_radius=DATA_RESET_POPUP_RADIUS
    )

    pygame.draw.rect(
        screen,
        DARK_GRAY,
        popup_rect,
        2,
        border_radius=DATA_RESET_POPUP_RADIUS
    )

    # ======================================================
    #                     ТЕКСТ POPUP
    # ======================================================

    title_surface = title_font.render(
        config[
            "popup_title"
        ],
        True,
        BLACK
    )

    title_rect = title_surface.get_rect(
        centerx=popup_rect.centerx,
        top=popup_rect.top + 38
    )

    screen.blit(
        title_surface,
        title_rect
    )

    for index, line in enumerate(
        config[
            "popup_lines"
        ]
    ):
        line_surface = small_font.render(
            line,
            True,
            DARK_GRAY
        )

        line_rect = line_surface.get_rect(
            centerx=popup_rect.centerx,
            top=(
                popup_rect.top
                + 110
                + index * 34
            )
        )

        screen.blit(
            line_surface,
            line_rect
        )

    # ======================================================
    #                    КНОПКИ POPUP
    # ======================================================

    confirm_button = create_button(
        layout[
            "confirm_button_x"
        ],
        layout[
            "buttons_y"
        ],
        DATA_RESET_POPUP_BUTTON_WIDTH,
        DATA_RESET_POPUP_BUTTON_HEIGHT,
        config[
            "confirm_text"
        ],
        config[
            "confirm_color"
        ]
    )

    draw_button(
        layout[
            "cancel_button"
        ],
        small_font
    )

    draw_button(
        confirm_button,
        small_font
    )


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

    if current_popup == POPUP_UNFINISHED_EXIT:
        draw_unfinished_exit_popup()
        return

    if current_popup == POPUP_DATA_RESET:
        draw_data_reset_popup()
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


def handle_unfinished_exit_popup_click(
    mouse_pos
):
    global current_popup

    layout = (
        get_unfinished_exit_popup_layout()
    )

    if layout[
        "stay_button"
    ][
        "rect"
    ].collidepoint(
        mouse_pos
    ):
        current_popup = None
        return

    if layout[
        "leave_button"
    ][
        "rect"
    ].collidepoint(
        mouse_pos
    ):
        leave_game_to_menu()
        return


def handle_data_reset_popup_click(
    mouse_pos
):
    """
    Обрабатывает кнопки подтверждения управления данными.

    На этапе 20 подтверждение только закрывает Popup.
    Сами действия подключаются на этапах 21–23.
    """

    config = (
        get_pending_data_action_config()
    )

    if config is None:
        close_data_reset_popup()
        return

    layout = (
        get_data_reset_popup_layout()
    )

    confirm_button = create_button(
        layout[
            "confirm_button_x"
        ],
        layout[
            "buttons_y"
        ],
        DATA_RESET_POPUP_BUTTON_WIDTH,
        DATA_RESET_POPUP_BUTTON_HEIGHT,
        config[
            "confirm_text"
        ],
        config[
            "confirm_color"
        ]
    )

    if layout[
        "cancel_button"
    ][
        "rect"
    ].collidepoint(
        mouse_pos
    ):
        close_data_reset_popup()
        return

    if confirm_button[
        "rect"
    ].collidepoint(
        mouse_pos
    ):
        # Сохраняем действие локально, потому что некоторые
        # функции сброса сами изменяют current_popup.
        confirmed_action = (
            pending_data_action
        )

        # ==================================================
        #                   СБРОС ПРОГРЕССА
        # ==================================================

        if confirmed_action == "reset_progress":
            reset_progress()

        # ==================================================
        #                  СБРОС НАСТРОЕК
        # ==================================================

        elif confirmed_action == "reset_settings":
            reset_settings()

        # ==================================================
        #                    ПОЛНЫЙ СБРОС
        # ==================================================

        elif confirmed_action == "reset_all":
            reset_all_data()

        close_data_reset_popup()
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

    if current_popup == POPUP_UNFINISHED_EXIT:
        handle_unfinished_exit_popup_click(
            mouse_pos
        )
        return

    if current_popup == POPUP_DATA_RESET:
        handle_data_reset_popup_click(
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


def draw_game_header():
    header_rect = pygame.Rect(
        0,
        0,
        WIDTH,
        GAME_HEADER_HEIGHT
    )

    pygame.draw.rect(
        screen,
        WHITE,
        header_rect
    )

    # ======================================================
    #                    КНОПКА «МЕНЮ»
    # ======================================================

    back_to_menu_button = (
        get_back_to_menu_button()
    )

    draw_button(
        back_to_menu_button,
        font
    )

    # ======================================================
    #                    НАЗВАНИЕ ИГРЫ
    # ======================================================

    center_x = get_game_area_center_x()

    title_text = title_font.render(
        "Угадай число",
        True,
        BLACK
    )

    title_rect = title_text.get_rect(
        center=(
            center_x,
            GAME_HEADER_HEIGHT // 2
        )
    )

    screen.blit(
        title_text,
        title_rect
    )

    # ======================================================
    #                    ОБЩИЙ БАЛАНС
    # ======================================================

    panel_x, panel_y, panel_width, panel_height = (
        get_bet_panel_position()
    )

    balance_text = font.render(
        f"Баланс: {score}",
        True,
        BLACK
    )

    balance_rect = balance_text.get_rect(
        center=(
            panel_x + panel_width // 2,
            43
        )
    )

    screen.blit(
        balance_text,
        balance_rect
    )

    visible_bet = get_visible_bet()

    if visible_bet == 0:
        bet_text_value = "Без ставки"
    else:
        bet_text_value = str(visible_bet)

    current_bet_text = small_font.render(
        f"Текущая ставка: {bet_text_value}",
        True,
        DARK_GRAY
    )

    current_bet_rect = current_bet_text.get_rect(
        center=(
            panel_x + panel_width // 2,
            82
        )
    )

    screen.blit(
        current_bet_text,
        current_bet_rect
    )

    # ======================================================
    #                  НИЖНЯЯ ЛИНИЯ HEADER
    # ======================================================

    pygame.draw.line(
        screen,
        LIGHT_GRAY,
        (
            0,
            GAME_HEADER_HEIGHT - 1
        ),
        (
            WIDTH,
            GAME_HEADER_HEIGHT - 1
        ),
        2
    )


def draw_game():
    screen.fill(WHITE)

    # ======================================================
    #                    ОСНОВНОЙ КОНТЕНТ
    # ======================================================

    draw_bet_panel()

    center_x = get_game_area_center_x()

    info_text = small_font.render(
        (
            f"Сложность: {difficulty_name} | "
            f"Числа: {min_number}-{max_number}"
        ),
        True,
        DARK_GRAY
    )

    screen.blit(
        info_text,
        (
            center_x
            - info_text.get_width() // 2,
            150
        )
    )

    # ======================================================
    #                СООБЩЕНИЕ ИЛИ РЕЗУЛЬТАТ
    # ======================================================

    if game_over:
        if win:
            result_color = GREEN
        else:
            result_color = RED

        result_text_1 = font.render(
            result_line_1,
            True,
            result_color
        )

        screen.blit(
            result_text_1,
            (
                center_x
                - result_text_1.get_width() // 2,
                195
            )
        )

        result_text_2 = small_font.render(
            result_line_2,
            True,
            DARK_GRAY
        )

        screen.blit(
            result_text_2,
            (
                center_x
                - result_text_2.get_width() // 2,
                245
            )
        )

    else:
        message_text = font.render(
            message,
            True,
            BLACK
        )

        screen.blit(
            message_text,
            (
                center_x
                - message_text.get_width() // 2,
                195
            )
        )

        attempts_text = small_font.render(
            (
                f"Попытки: "
                f"{attempts_left}/{max_attempts}"
            ),
            True,
            DARK_GRAY
        )

        screen.blit(
            attempts_text,
            (
                center_x
                - attempts_text.get_width() // 2,
                250
            )
        )

    # ======================================================
    #                       ПЛИТКИ
    # ======================================================

    for tile in tiles:
        rect = tile["rect"]
        number = tile["number"]
        color = tile["color"]

        pygame.draw.rect(
            screen,
            color,
            rect,
            border_radius=12
        )

        number_text = small_font.render(
            str(number),
            True,
            BLACK
        )

        text_x = (
            rect.centerx
            - number_text.get_width() // 2
        )

        text_y = (
            rect.centery
            - number_text.get_height() // 2
        )

        screen.blit(
            number_text,
            (
                text_x,
                text_y
            )
        )

    # ======================================================
    #                  ЗАВЕРШЁННАЯ ПАРТИЯ
    # ======================================================

    if game_over:
        bottom_text = small_font.render(
            "Выбери ставку и нажми «Заново»",
            True,
            DARK_GRAY
        )

        screen.blit(
            bottom_text,
            (
                center_x
                - bottom_text.get_width() // 2,
                HEIGHT - 140
            )
        )

        restart_button = get_restart_button()

        draw_button(
            restart_button,
            small_font
        )

    # Header закрывает верхнюю границу игрового контента.
    draw_game_header()

    # Toast рисуется после Header и всегда остаётся видимым.
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


def start_game_from_settings():
    """
    Запускает игру согласно сохранённому режиму сложности.

    Режим ask сохраняет старое поведение с Popup,
    а конкретная сложность начинает игру сразу.
    """

    global current_popup

    start_difficulty = settings[
        "game"
    ][
        "start_difficulty"
    ]

    # ======================================================
    #                 ВСЕГДА СПРАШИВАТЬ
    # ======================================================

    if start_difficulty == "ask":
        current_popup = POPUP_DIFFICULTY
        return

    # ======================================================
    #                  ПРЯМОЙ ЗАПУСК
    # ======================================================

    difficulty_name_value = (
        DIFFICULTY_SETTING_TO_NAME[
            start_difficulty
        ]
    )

    set_difficulty(
        difficulty_name_value
    )


def handle_menu_click(mouse_pos):
    global current_popup, popup_title, popup_text, current_screen

    for button in get_menu_buttons():

        if button["rect"].collidepoint(mouse_pos):

            if button["text"] == "Играть":
                start_game_from_settings()
                return


            elif button["text"] == "Профиль":
                current_screen = PROFILE



            elif button["text"] == "Достижения":
                current_screen = ACHIEVEMENTS_SCREEN
                return


            elif button["text"] == "Настройки":
                current_screen = SETTINGS_SCREEN
                return

            elif button["text"] == "Developer-панель":
                open_developer_popup()
                return

            elif button["text"] == "Выход":
                pygame.quit()
                sys.exit()


def set_settings_slider_value(
    setting_key,
    mouse_x
):
    """
    Переводит координату мыши в значение Slider
    и сразу обновляет настройку громкости в памяти.
    """

    slider_layout = settings_slider_rects.get(
        setting_key
    )

    if slider_layout is None:
        return

    track_rect = slider_layout["track"]

    mouse_x = max(
        track_rect.left,
        min(
            mouse_x,
            track_rect.right
        )
    )

    value_ratio = (
        (mouse_x - track_rect.left)
        / track_rect.width
    )

    new_value = round(
        MIN_VOLUME
        + value_ratio
        * (MAX_VOLUME - MIN_VOLUME)
    )

    settings[
        "audio"
    ][
        setting_key
    ] = new_value


def begin_settings_slider_drag(
    mouse_pos
):
    """
    Начинает перетаскивание Slider, если нажатие
    произошло внутри его расширенной области.
    """

    global active_settings_slider
    global settings_slider_drag_start_value

    for item, setting_path in (
        SETTINGS_SLIDER_PATHS.items()
    ):
        category, key = setting_path

        slider_layout = settings_slider_rects.get(
            key
        )

        if (
                slider_layout is not None
                and slider_layout["enabled"]
                and slider_layout["hit"].collidepoint(
            mouse_pos
        )
        ):
            active_settings_slider = key

            settings_slider_drag_start_value = (
                settings[
                    category
                ][
                    key
                ]
            )

            # Нажатие на любое место шкалы
            # сразу переносит туда бегунок.
            set_settings_slider_value(
                key,
                mouse_pos[0]
            )

            return True

    return False


def update_settings_slider_drag(
    mouse_pos
):
    """
    Обновляет активный Slider во время
    движения мыши с зажатой кнопкой.
    """

    if active_settings_slider is None:
        return

    set_settings_slider_value(
        active_settings_slider,
        mouse_pos[0]
    )


def finish_settings_slider_drag():
    """
    Завершает перетаскивание и сохраняет новое
    значение один раз после отпускания мыши.
    """

    global active_settings_slider
    global settings_slider_drag_start_value

    if active_settings_slider is None:
        return

    current_value = settings[
        "audio"
    ][
        active_settings_slider
    ]

    if (
        current_value
        != settings_slider_drag_start_value
    ):
        save_progress()

    active_settings_slider = None
    settings_slider_drag_start_value = None


def open_data_reset_popup(
    action
):
    """
    Открывает подтверждение выбранного
    действия управления данными.
    """

    global current_popup
    global pending_data_action

    valid_actions = {
        config["action"]
        for config in SETTINGS_DATA_ACTIONS.values()
    }

    if action not in valid_actions:
        return

    pending_data_action = action
    current_popup = POPUP_DATA_RESET


def close_data_reset_popup():
    """
    Закрывает Popup управления данными
    и очищает выбранное действие.
    """

    global current_popup
    global pending_data_action

    current_popup = None
    pending_data_action = None


def get_pending_data_action_config():
    """
    Возвращает описание выбранного действия
    для отрисовки и обработки Popup.
    """

    for config in SETTINGS_DATA_ACTIONS.values():
        if config[
            "action"
        ] == pending_data_action:
            return config

    return None


def handle_settings_click(
    mouse_pos
):
    """
    Обрабатывает кнопку возврата и интерактивные элементы настроек.

    Клики по прокрученным за пределы видимой области
    элементам блокируются через settings_viewport.
    """

    global current_screen

    # ======================================================
    #                         НАЗАД
    # ======================================================

    back_button = (
        get_settings_back_button()
    )

    if back_button["rect"].collidepoint(
        mouse_pos
    ):
        current_screen = MENU
        return

    # ======================================================
    #                    ВИДИМАЯ ОБЛАСТЬ
    # ======================================================

    settings_viewport = pygame.Rect(
        0,
        SETTINGS_HEADER_HEIGHT,
        WIDTH,
        HEIGHT - SETTINGS_HEADER_HEIGHT
    )

    if not settings_viewport.collidepoint(
        mouse_pos
    ):
        return

    # ======================================================
    #                 УПРАВЛЕНИЕ ДАННЫМИ
    # ======================================================

    for config in SETTINGS_DATA_ACTIONS.values():
        action = config[
            "action"
        ]

        control_id = (
            "data_action",
            action
        )

        button_rect = (
            settings_control_rects.get(
                control_id
            )
        )

        if (
            button_rect is not None
            and button_rect.collidepoint(
                mouse_pos
            )
        ):
            open_data_reset_popup(
                action
            )
            return

    # ======================================================
    #                         SLIDER
    # ======================================================

    if begin_settings_slider_drag(
        mouse_pos
    ):
        return

    # ======================================================
    #                         TOGGLE
    # ======================================================

    for setting_path in (
            SETTINGS_TOGGLE_PATHS.values()
    ):
        category, key = setting_path

        control_id = (
            "toggle",
            category,
            key
        )

        toggle_rect = (
            settings_control_rects.get(
                control_id
            )
        )

        if (
            toggle_rect is not None
            and toggle_rect.collidepoint(
                mouse_pos
            )
        ):
            settings[
                category
            ][
                key
            ] = not settings[
                category
            ][
                key
            ]

            save_progress()
            return

    # ======================================================
    #                    OPTION SELECTOR
    # ======================================================

    for option_config in (
        SETTINGS_OPTION_CONFIGS.values()
    ):
        category = option_config[
            "category"
        ]

        key = option_config[
            "key"
        ]

        for option_value, option_label in (
            option_config["options"]
        ):
            control_id = (
                "option",
                key,
                option_value
            )

            option_rect = (
                settings_control_rects.get(
                    control_id
                )
            )

            if (
                    option_rect is not None
                    and option_rect.collidepoint(
                mouse_pos
            )
            ):
                current_value = settings[
                    category
                ][
                    key
                ]

                # Повторный клик по уже активному
                # варианту ничего не пересоздаёт.
                if option_value == current_value:
                    return

                # ==================================================
                #                  РЕЖИМ ОКНА
                # ==================================================

                if (
                        category == "interface"
                        and key == "window_mode"
                ):
                    apply_window_mode(
                        option_value
                    )
                    return

                # ==================================================
                #               ОСТАЛЬНЫЕ OPTION
                # ==================================================

                settings[
                    category
                ][
                    key
                ] = option_value

                save_progress()
                return


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


def get_result_details_text(
    result,
    player_won
):
    """
    Формирует вторую строку результата согласно настройкам.

    Подробный режим показывает составляющие расчёта,
    компактный — только полученный XP и текущий баланс.
    """

    show_details = settings[
        "interface"
    ][
        "show_result_details"
    ]

    # ======================================================
    #                  КОМПАКТНЫЙ РЕЖИМ
    # ======================================================

    if not show_details:
        return (
            f"XP: +{last_xp_gained} | "
            f"Баланс: {score}"
        )

    # ======================================================
    #                  ПОДРОБНЫЙ РЕЖИМ
    # ======================================================

    if player_won:
        return (
            f"База: "
            f"{result['base_points']} "
            f"× x"
            f"{result['streak_multiplier']:.1f} "
            f"= {result['earned_points']} | "
            f"Ставка: +{result['bet_bonus']}"
        )

    return (
        f"Штраф: "
        f"{result['base_penalty']} | "
        f"Ставка: "
        f"-{result['bet_penalty']} | "
        f"Число было {secret_number}"
    )


def handle_game_click(mouse_pos):
    global secret_number, attempts_left
    global game_over, win, message, tiles

    global current_screen
    global selected_bet, current_bet
    global game_started

    global custom_bet_active
    global custom_bet_error

    global result_line_1
    global result_line_2

    global balance_before_bet
    global started_all_in

    back_to_menu_button = (
        get_back_to_menu_button()
    )

    restart_button = (
        get_restart_button()
    )

    bet_buttons = get_bet_buttons()

    input_rect = (
        get_custom_bet_input_rect()
    )

    apply_button = (
        get_custom_bet_apply_button()
    )

    all_in_button = (
        get_all_in_bet_button()
    )

    if back_to_menu_button["rect"].collidepoint(
        mouse_pos
    ):
        custom_bet_active = False

        request_leave_game()
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
            if (
                    button["rect"].collidepoint(
                        mouse_pos
                    )
                    and button["active"]
            ):
                set_selected_bet(
                    button["bet"]
                )

                custom_bet_error = ""
                return

    if (
            all_in_button["rect"].collidepoint(
                mouse_pos
            )
            and all_in_button["active"]
    ):
        set_selected_bet(score)

        custom_bet_error = ""
        return

    if (
            game_over
            and restart_button["rect"].collidepoint(
        mouse_pos
    )
    ):
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

                result_line_1 = (
                    f"Победа! "
                    f"+{result['total']} очков"
                )

                result_line_2 = (
                    get_result_details_text(
                        result,
                        player_won=True
                    )
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

                result_line_1 = (
                    f"Поражение! "
                    f"-{result['total']} очков"
                )

                result_line_2 = (
                    get_result_details_text(
                        result,
                        player_won=False
                    )
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
    Обрабатывает глобальную команду открытия Developer Panel.

    Горячая клавиша работает только тогда, когда доступ
    к панели включён в сохранённых настройках.
    """

    if not settings[
        "developer"
    ][
        "enabled"
    ]:
        return

    if (
        command_pressed
        and event.scancode
        == MAC_SCANCODE_1
    ):
        if current_popup is None:
            open_developer_popup()


initialize_achievement_states()
load_progress()

# Режим окна применяется после загрузки настроек,
# но до создания ScrollArea и начала главного цикла.
apply_saved_window_mode()

# Кумулятивные условия из старого сохранения выдаются сразу после миграции.
# Уже завершённые достижения пропускаются, поэтому повторной награды XP нет.
check_achievements()

profile_scroll = create_scroll_area(
    WIDTH - 25,
    PROFILE_HEADER_HEIGHT,
    8,
    HEIGHT - PROFILE_HEADER_HEIGHT,
    1100
)

achievement_scroll = create_scroll_area(
    WIDTH - 25,
    HEADER_HEIGHT,
    8,
    HEIGHT - HEADER_HEIGHT,
    5000
)

settings_scroll = create_scroll_area(
    WIDTH - 25,
    SETTINGS_HEADER_HEIGHT,
    8,
    HEIGHT - SETTINGS_HEADER_HEIGHT,
    1500
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
            # В fullscreen размеры контролирует система.
            # Ручной Resize обрабатываем только в оконном режиме.
            if settings[
                "interface"
            ][
                "window_mode"
            ] == "windowed":
                WIDTH = max(
                    event.w,
                    MIN_WIDTH
                )

                HEIGHT = max(
                    event.h,
                    MIN_HEIGHT
                )

                screen = pygame.display.set_mode(
                    (
                        WIDTH,
                        HEIGHT
                    ),
                    pygame.RESIZABLE
                )

                settings[
                    "interface"
                ][
                    "windowed_width"
                ] = WIDTH

                settings[
                    "interface"
                ][
                    "windowed_height"
                ] = HEIGHT

                update_tile_positions()

                # Сохраняем через короткую задержку:
                # следующее Resize-событие просто обновит срок.
                window_resize_save_deadline = (
                        pygame.time.get_ticks()
                        + 300
                )

            else:
                WIDTH, HEIGHT = (
                    screen.get_size()
                )

                update_tile_positions()

        if event.type == pygame.MOUSEMOTION:
            if (
                active_settings_slider is not None
                and current_popup is None
                and current_screen == SETTINGS_SCREEN
            ):
                update_settings_slider_drag(
                    event.pos
                )

        if (
            event.type == pygame.MOUSEBUTTONUP
            and event.button == 1
            and active_settings_slider is not None
        ):
            finish_settings_slider_drag()

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

            elif current_screen == SETTINGS_SCREEN:
                handle_settings_click(
                    mouse_position
                )

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

                elif current_popup == POPUP_DATA_RESET:
                    close_data_reset_popup()

                else:
                    current_popup = None

                continue

            if (
                event.key == pygame.K_ESCAPE
                and current_popup is None
                and current_screen == SETTINGS_SCREEN
            ):
                current_screen = MENU
                continue

            if (
                event.key == pygame.K_ESCAPE
                and current_popup is None
                and current_screen == GAME
            ):
                request_leave_game()
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

            elif current_screen == SETTINGS_SCREEN:
                handle_scroll_event(
                    settings_scroll,
                    event
                )

    # ======================================================
    #              ОТЛОЖЕННОЕ СОХРАНЕНИЕ RESIZE
    # ======================================================

    if (
        window_resize_save_deadline
        is not None
        and pygame.time.get_ticks()
        >= window_resize_save_deadline
    ):
        save_progress()

        window_resize_save_deadline = None

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

        elif current_screen == SETTINGS_SCREEN:
            update_scroll(
                settings_scroll
            )

    if current_screen == MENU:
        draw_menu()

    elif current_screen == GAME:
        draw_game()

    elif current_screen == PROFILE:
        draw_profile()

    elif current_screen == ACHIEVEMENTS_SCREEN:
        draw_achievements_screen()

    elif current_screen == SETTINGS_SCREEN:
        draw_settings_screen()

    draw_popup()

    pygame.display.flip()

pygame.quit()
