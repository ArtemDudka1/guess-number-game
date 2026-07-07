import pygame
import random
import math
import json

pygame.init()

# Минимальный размер окна
MIN_WIDTH = 1250
MIN_HEIGHT = 900

# Текущий размер окна
WIDTH = 1250
HEIGHT = 900

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Угадай число")

# Цвета
WHITE = (245, 245, 245)
BLACK = (30, 30, 30)
BLUE = (100, 170, 255)
RED = (255, 100, 100)
GREEN = (100, 220, 130)
GRAY = (170, 170, 170)
LIGHT_GRAY = (225, 225, 225)
DARK_GRAY = (90, 90, 90)
YELLOW = (255, 215, 100)
ORANGE = (255, 180, 80)

# Шрифты
font = pygame.font.Font(None, 44)
big_font = pygame.font.Font(None, 68)
small_font = pygame.font.Font(None, 32)

# Состояния игры
MENU = "menu"
GAME = "game"

current_screen = MENU

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
games_played = 0
wins = 0
losses = 0
current_streak = 0
best_streak = 0

# Файл сохранения
SAVE_FILE = "save_data.json"

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

# Общие настройки плиток
TILE_SIZE = 70
TILE_GAP = 10
columns = 5

# Правая боковая панель
SIDEBAR_MARGIN = 30
PANEL_WIDTH = 260
PANEL_GAP = 25

STATS_PANEL_HEIGHT = 340
BET_PANEL_HEIGHT = 430


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

    pygame.draw.rect(screen, color, rect, border_radius=14)

    button_text = font_obj.render(text, True, BLACK)
    text_x = rect.centerx - button_text.get_width() // 2
    text_y = rect.centery - button_text.get_height() // 2

    screen.blit(button_text, (text_x, text_y))


def create_button(x, y, width, height, text, color):
    rect = pygame.Rect(x, y, width, height)

    return {
        "rect": rect,
        "text": text,
        "color": color
    }


def save_progress():
    data = {
        "score": score,
        "games_played": games_played,
        "wins": wins,
        "losses": losses,
        "current_streak": current_streak,
        "best_streak": best_streak,
        "selected_bet": selected_bet
    }

    with open(SAVE_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def load_progress():
    global score, games_played, wins, losses
    global current_streak, best_streak, selected_bet, current_bet

    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        score = data.get("score", 0)
        games_played = data.get("games_played", 0)
        wins = data.get("wins", 0)
        losses = data.get("losses", 0)
        current_streak = data.get("current_streak", 0)
        best_streak = data.get("best_streak", 0)
        selected_bet = data.get("selected_bet", 0)

        if selected_bet > score:
            selected_bet = 0

        current_bet = selected_bet

    except FileNotFoundError:
        pass
    except json.JSONDecodeError:
        pass


def reset_progress():
    global score, games_played, wins, losses
    global current_streak, best_streak
    global selected_bet, current_bet
    global custom_bet_text, custom_bet_error, custom_bet_active
    global reset_popup_open

    score = 0
    games_played = 0
    wins = 0
    losses = 0
    current_streak = 0
    best_streak = 0

    selected_bet = 0
    current_bet = 0

    custom_bet_text = ""
    custom_bet_error = ""
    custom_bet_active = False

    reset_popup_open = False

    save_progress()


def get_menu_buttons():
    button_width = 270
    button_height = 75
    button_gap = 25

    total_height = 3 * button_height + 2 * button_gap

    start_x = WIDTH // 2 - 250
    start_y = HEIGHT // 2 - total_height // 2 + 70

    return [
        create_button(start_x, start_y, button_width, button_height, "Лёгкая", BLUE),
        create_button(start_x, start_y + button_height + button_gap, button_width, button_height, "Средняя", YELLOW),
        create_button(start_x, start_y + 2 * (button_height + button_gap), button_width, button_height, "Сложная", RED)
    ]


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
    panel_x = WIDTH - PANEL_WIDTH - SIDEBAR_MARGIN

    total_sidebar_height = STATS_PANEL_HEIGHT + PANEL_GAP + BET_PANEL_HEIGHT
    panel_y = (HEIGHT - total_sidebar_height) // 2

    if panel_y < SIDEBAR_MARGIN:
        panel_y = SIDEBAR_MARGIN

    return panel_x, panel_y, PANEL_WIDTH, STATS_PANEL_HEIGHT


def get_bet_panel_position():
    stats_x, stats_y, stats_width, stats_height = get_stats_panel_position()

    panel_x = stats_x
    panel_y = stats_y + stats_height + PANEL_GAP

    return panel_x, panel_y, PANEL_WIDTH, BET_PANEL_HEIGHT


def get_reset_button():
    panel_x, panel_y, panel_width, panel_height = get_stats_panel_position()

    button_width = 180
    button_height = 36
    button_x = panel_x + (panel_width - button_width) // 2
    button_y = panel_y + panel_height - button_height - 15

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
    start_y = panel_y + 55

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
    input_y = panel_y + 300

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


def finish_game(player_won):
    global score, games_played, wins, losses
    global current_streak, best_streak

    games_played += 1

    if player_won:
        wins += 1
        current_streak += 1

        if current_streak > best_streak:
            best_streak = current_streak

        base_points = attempts_left * get_points_multiplier()
        streak_multiplier = get_streak_multiplier()
        earned_points = int(base_points * streak_multiplier)

        bet_bonus = current_bet * 2
        total_earned = earned_points + bet_bonus

        score += total_earned

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

    base_penalty = get_loss_penalty()
    bet_penalty = current_bet
    total_penalty = base_penalty + bet_penalty

    score -= total_penalty

    if score < 0:
        score = 0

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

    current_bet = selected_bet
    game_started = False

    result_line_1 = ""
    result_line_2 = ""

    new_secret_number = random.randint(min_number, max_number)
    new_attempts_left = max_attempts
    new_game_over = False
    new_win = False
    new_message = "Выбери число"

    new_tiles = create_tiles()

    return new_secret_number, new_attempts_left, new_game_over, new_win, new_message, new_tiles


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

    panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
    pygame.draw.rect(screen, LIGHT_GRAY, panel_rect, border_radius=14)

    draw_text("Статистика", small_font, BLACK, panel_x + 22, panel_y + 15)
    draw_text(f"Очки: {score}", small_font, DARK_GRAY, panel_x + 22, panel_y + 48)
    draw_text(f"Ставка: {selected_bet}", small_font, DARK_GRAY, panel_x + 22, panel_y + 76)
    draw_text(f"Множитель: x{get_streak_multiplier():.1f}", small_font, DARK_GRAY, panel_x + 22, panel_y + 104)
    draw_text(f"Игры: {games_played}", small_font, DARK_GRAY, panel_x + 22, panel_y + 132)
    draw_text(f"Победы: {wins}", small_font, DARK_GRAY, panel_x + 22, panel_y + 160)
    draw_text(f"Поражения: {losses}", small_font, DARK_GRAY, panel_x + 22, panel_y + 188)
    draw_text(f"Серия: {current_streak}", small_font, DARK_GRAY, panel_x + 22, panel_y + 216)
    draw_text(f"Лучшая серия: {best_streak}", small_font, DARK_GRAY, panel_x + 22, panel_y + 244)

    reset_button = get_reset_button()
    draw_button(reset_button, small_font)


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


def draw_custom_bet_input():
    panel_x, panel_y, panel_width, panel_height = get_bet_panel_position()

    label_y = panel_y + 270

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

    draw_center_text("Угадай число", big_font, BLACK, 125)

    difficulty_text = font.render("Выбери сложность", True, DARK_GRAY)
    difficulty_x = WIDTH // 2 - 250 + 135 - difficulty_text.get_width() // 2
    screen.blit(difficulty_text, (difficulty_x, 220))

    menu_buttons = get_menu_buttons()

    for button in menu_buttons:
        draw_button(button, font)

    draw_menu_stats_panel()

    if reset_popup_open:
        draw_reset_popup()


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
    global reset_popup_open

    if reset_popup_open:
        handle_reset_popup_click(mouse_pos)
        return

    menu_reset_button = get_menu_reset_button()

    if menu_reset_button["rect"].collidepoint(mouse_pos):
        reset_popup_open = True
        return

    menu_buttons = get_menu_buttons()

    for button in menu_buttons:
        if button["rect"].collidepoint(mouse_pos):
            set_difficulty(button["text"])


def handle_game_click(mouse_pos):
    global secret_number, attempts_left, game_over, win, message, tiles
    global current_screen, selected_bet, current_bet, game_started
    global custom_bet_active, custom_bet_error, reset_popup_open
    global result_line_1, result_line_2

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


load_progress()

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

            if current_screen == MENU:
                handle_menu_click(mouse_position)

            elif current_screen == GAME:
                handle_game_click(mouse_position)

        if event.type == pygame.KEYDOWN:
            if current_screen == GAME:
                handle_custom_bet_typing(event)

    if current_screen == MENU:
        draw_menu()

    elif current_screen == GAME:
        draw_game()

    pygame.display.flip()

pygame.quit()