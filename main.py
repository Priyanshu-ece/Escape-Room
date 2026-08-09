import pygame
import sys
import time
import os
import math
import random


# =========================================================
# INITIALIZATION
# =========================================================

pygame.init()

try:
    pygame.mixer.init()
    SOUND_ENABLED = True
except pygame.error:
    SOUND_ENABLED = False
    print("WARNING: Audio system could not be initialized.")


# =========================================================
# WINDOW
# =========================================================

WIDTH = 1200
HEIGHT = 700

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Escape Room: The Abandoned Lab")

clock = pygame.time.Clock()


# =========================================================
# COLORS
# =========================================================

BLACK = (0, 0, 0)
WHITE = (240, 240, 240)

DARK = (12, 15, 20)
GRAY = (100, 105, 110)
LIGHT_GRAY = (170, 175, 180)

BLUE = (50, 120, 255)
RED = (220, 60, 60)
GREEN = (50, 200, 100)
YELLOW = (255, 220, 70)
CYAN = (0, 220, 255)

DARK_GREEN = (10, 50, 25)


# =========================================================
# FONTS
# =========================================================

font = pygame.font.SysFont("consolas", 22)
small_font = pygame.font.SysFont("consolas", 17)
big_font = pygame.font.SysFont("consolas", 70, bold=True)


# =========================================================
# DEBUG MODE
# =========================================================

DEBUG_HITBOXES = False


# =========================================================
# SOUND SYSTEM
# =========================================================

def load_sound(filename, volume=0.5):

    if not SOUND_ENABLED:
        return None

    path = os.path.join("sounds", filename)

    try:

        sound = pygame.mixer.Sound(path)
        sound.set_volume(volume)

        return sound

    except (pygame.error, FileNotFoundError):

        print(f"WARNING: Could not load sound: {path}")

        return None


def play_sound(sound):

    if sound is not None:
        sound.play()


click_sound = load_sound("click.wav", 0.4)
pickup_sound = load_sound("pickup.wav", 0.6)
success_sound = load_sound("success.wav", 0.7)
error_sound = load_sound("error.wav", 0.6)
unlock_sound = load_sound("unlock.wav", 0.8)


def start_background_music():

    if not SOUND_ENABLED:
        return

    music_path = os.path.join(
        "sounds",
        "background.mp3"
    )

    try:

        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(0.25)
        pygame.mixer.music.play(-1)

    except (pygame.error, FileNotFoundError):

        print(
            f"WARNING: Background music not found: "
            f"{music_path}"
        )


# =========================================================
# LOAD LAB BACKGROUND
# =========================================================

try:

    lab_background = pygame.image.load(
        os.path.join(
            "assets",
            "lab_background.png"
        )
    ).convert()

    lab_background = pygame.transform.scale(
        lab_background,
        (WIDTH, HEIGHT)
    )

    print("Lab background loaded successfully.")

except (pygame.error, FileNotFoundError):

    lab_background = None

    print(
        "WARNING: Lab background image not found."
    )


# =========================================================
# GAME SETTINGS
# =========================================================

TIME_LIMIT = 600

CORRECT_POWER_SEQUENCE = [1, 2, 3, 4]
CORRECT_PASSWORD = "LAB"
CORRECT_DOOR_CODE = "2026"


# =========================================================
# GAME STATE
# =========================================================

game_started = False
game_start = None

game_won = False
game_over = False

inventory = []

message = (
    "SYSTEM: You are trapped inside an abandoned laboratory."
)

flashlight_taken = False
drawer_opened = False
power_on = False
computer_used = False

show_power_puzzle = False
power_sequence = []

show_computer_puzzle = False
password_input = ""

show_door_puzzle = False
door_code_input = ""


# =========================================================
# ANIMATION STATE
# =========================================================

drawer_open_progress = 0.0
drawer_animation_start = 0

door_open_progress = 0.0
door_animation_start = 0
door_animating = False

power_flash_start = 0

light_flicker_alpha = 0
next_flicker_time = 0

last_frame_time = pygame.time.get_ticks()


# =========================================================
# INTERACTIVE OBJECT POSITIONS
# =========================================================

# EXIT DOOR
door = pygame.Rect(
    762, 205,
    138, 301
)

# DRAWER
drawer = pygame.Rect(
    345, 353,
    109, 147
)

# FLASHLIGHT
flashlight = pygame.Rect(
    64, 90,
    248, 103
)

# COMPUTER
computer = pygame.Rect(
    485, 301,
    120, 100
)

# POWER BOX
power_box = pygame.Rect(
    920, 231,
    99, 140
)


# =========================================================
# START BUTTON
# =========================================================

start_button = pygame.Rect(
    450,
    450,
    300,
    70
)


# =========================================================
# POWER PUZZLE SWITCHES
# =========================================================

switches = {

    1: pygame.Rect(400, 280, 100, 55),

    2: pygame.Rect(560, 280, 100, 55),

    3: pygame.Rect(400, 370, 100, 55),

    4: pygame.Rect(560, 370, 100, 55)
}


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def draw_text(
    text,
    x,
    y,
    color=WHITE,
    font_type=font
):

    rendered = font_type.render(
        text,
        True,
        color
    )

    screen.blit(
        rendered,
        (x, y)
    )


def draw_center_text(
    text,
    center_x,
    y,
    color=WHITE,
    font_type=font
):

    rendered = font_type.render(
        text,
        True,
        color
    )

    rect = rendered.get_rect(
        center=(center_x, y)
    )

    screen.blit(
        rendered,
        rect
    )


# =========================================================
# GLOW FUNCTION
# =========================================================

def draw_glow(
    rect,
    color,
    strength=100,
    expand=15
):

    glow_rect = pygame.Rect(
        rect.x - expand,
        rect.y - expand,
        rect.width + expand * 2,
        rect.height + expand * 2
    )

    glow = pygame.Surface(
        (glow_rect.width, glow_rect.height),
        pygame.SRCALPHA
    )

    glow.fill(
        (
            color[0],
            color[1],
            color[2],
            strength
        )
    )

    screen.blit(
        glow,
        (glow_rect.x, glow_rect.y)
    )


# =========================================================
# ANIMATED HOVER
# =========================================================

def draw_hover(rect, mouse, color=YELLOW):

    if rect.collidepoint(mouse):

        current_time = pygame.time.get_ticks()

        pulse = (
            math.sin(current_time / 150)
            + 1
        ) / 2

        thickness = int(
            2 + pulse * 3
        )

        expand = int(
            3 + pulse * 5
        )

        hover_rect = rect.inflate(
            expand,
            expand
        )

        pygame.draw.rect(
            screen,
            color,
            hover_rect,
            thickness,
            border_radius=5
        )


# =========================================================
# DEBUG HITBOXES
# =========================================================

def draw_hitboxes():

    objects = [

        ("DOOR", door, RED),

        ("DRAWER", drawer, BLUE),

        ("FLASHLIGHT", flashlight, YELLOW),

        ("COMPUTER", computer, GREEN),

        ("POWER BOX", power_box, CYAN)
    ]

    for name, rect, color in objects:

        overlay = pygame.Surface(
            (rect.width, rect.height),
            pygame.SRCALPHA
        )

        overlay.fill(
            (
                color[0],
                color[1],
                color[2],
                50
            )
        )

        screen.blit(
            overlay,
            (rect.x, rect.y)
        )

        pygame.draw.rect(
            screen,
            color,
            rect,
            3
        )

        label = small_font.render(
            name,
            True,
            color
        )

        label_rect = label.get_rect(
            topleft=(
                rect.x,
                max(0, rect.y - 24)
            )
        )

        pygame.draw.rect(
            screen,
            BLACK,
            label_rect.inflate(8, 4)
        )

        screen.blit(
            label,
            label_rect
        )


# =========================================================
# START MENU
# =========================================================

def draw_start_menu():

    screen.fill((8, 12, 18))

    current_time = pygame.time.get_ticks()

    # Animated background lines
    for x in range(-300, WIDTH + 300, 100):

        offset = int(
            math.sin(
                current_time / 1500
            ) * 30
        )

        pygame.draw.line(
            screen,
            (15, 25, 35),
            (x + offset, 0),
            (x + 300 + offset, HEIGHT),
            2
        )

    pygame.draw.rect(
        screen,
        (20, 30, 40),
        (150, 100, 900, 500)
    )

    pygame.draw.rect(
        screen,
        BLUE,
        (150, 100, 900, 500),
        3
    )

    draw_center_text(
        "ESCAPE ROOM",
        WIDTH // 2,
        205,
        YELLOW,
        big_font
    )

    draw_center_text(
        "THE ABANDONED LAB",
        WIDTH // 2,
        270,
        GREEN,
        font
    )

    draw_center_text(
        "You wake up inside a mysterious abandoned laboratory.",
        WIDTH // 2,
        340,
        WHITE,
        small_font
    )

    draw_center_text(
        "Restore power. Find the keycard. Escape.",
        WIDTH // 2,
        375,
        WHITE,
        small_font
    )

    mouse = pygame.mouse.get_pos()

    pulse = (
        math.sin(current_time / 250)
        + 1
    ) / 2

    if start_button.collidepoint(mouse):

        button_color = (
            30,
            int(130 + pulse * 60),
            70
        )

    else:

        button_color = (
            30,
            100,
            60
        )

    pygame.draw.rect(
        screen,
        button_color,
        start_button,
        border_radius=10
    )

    pygame.draw.rect(
        screen,
        WHITE,
        start_button,
        2,
        border_radius=10
    )

    draw_center_text(
        "START GAME",
        WIDTH // 2,
        485,
        WHITE,
        font
    )

    draw_center_text(
        "ESC to quit",
        WIDTH // 2,
        550,
        GRAY,
        small_font
    )


# =========================================================
# DRAW ROOM
# =========================================================

def draw_room():

    if lab_background is not None:

        screen.blit(
            lab_background,
            (0, 0)
        )

    else:

        screen.fill(DARK)

        draw_text(
            "LAB BACKGROUND NOT FOUND",
            400,
            300,
            RED,
            font
        )

    # Status indicator
    current_time = pygame.time.get_ticks()

    if power_on:

        pulse = (
            math.sin(current_time / 250)
            + 1
        ) / 2

        indicator_color = (
            30,
            int(150 + pulse * 80),
            80
        )

    else:

        blink = (
            math.sin(current_time / 300)
            + 1
        ) / 2

        indicator_color = (
            int(150 + blink * 70),
            40,
            40
        )

    pygame.draw.circle(
        screen,
        indicator_color,
        (30, 30),
        10
    )

    pygame.draw.circle(
        screen,
        WHITE,
        (30, 30),
        10,
        1
    )


# =========================================================
# LIGHT FLICKER
# =========================================================

def update_light_flicker():

    global light_flicker_alpha
    global next_flicker_time

    if not game_started:
        return

    if not flashlight_taken:
        return

    current_time = pygame.time.get_ticks()

    if current_time > next_flicker_time:

        chance = random.randint(1, 100)

        if chance < 4:

            light_flicker_alpha = random.randint(
                15,
                50
            )

            next_flicker_time = (
                current_time
                + random.randint(60, 180)
            )

        else:

            light_flicker_alpha = max(
                0,
                light_flicker_alpha - 2
            )

            next_flicker_time = (
                current_time
                + random.randint(80, 250)
            )


def draw_light_flicker():

    if light_flicker_alpha <= 0:
        return

    flicker = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )

    flicker.fill(
        (
            255,
            255,
            230,
            light_flicker_alpha
        )
    )

    screen.blit(
        flicker,
        (0, 0)
    )


# =========================================================
# POWER RESTORATION FLASH
# =========================================================

def draw_power_flash():

    if power_flash_start == 0:
        return

    current_time = pygame.time.get_ticks()

    elapsed = (
        current_time
        - power_flash_start
    )

    if elapsed > 900:
        return

    progress = elapsed / 900

    alpha = int(
        150 * (1 - progress)
    )

    flash = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )

    flash.fill(
        (
            180,
            255,
            200,
            alpha
        )
    )

    screen.blit(
        flash,
        (0, 0)
    )


# =========================================================
# FLASHLIGHT DARKNESS EFFECT
# =========================================================

def draw_darkness():

    if flashlight_taken:
        return

    mouse_x, mouse_y = pygame.mouse.get_pos()

    darkness = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )

    darkness.fill(
        (0, 0, 0, 225)
    )

    pygame.draw.circle(
        darkness,
        (0, 0, 0, 170),
        (mouse_x, mouse_y),
        230
    )

    pygame.draw.circle(
        darkness,
        (0, 0, 0, 110),
        (mouse_x, mouse_y),
        170
    )

    pygame.draw.circle(
        darkness,
        (0, 0, 0, 50),
        (mouse_x, mouse_y),
        110
    )

    pygame.draw.circle(
        darkness,
        (0, 0, 0, 0),
        (mouse_x, mouse_y),
        65
    )

    screen.blit(
        darkness,
        (0, 0)
    )


# =========================================================
# COMPUTER SCREEN GLOW
# =========================================================

def draw_computer_glow():

    if not power_on:
        return

    current_time = pygame.time.get_ticks()

    pulse = (
        math.sin(current_time / 220)
        + 1
    ) / 2

    glow_alpha = int(
        25 + pulse * 45
    )

    glow = pygame.Surface(
        (
            computer.width + 30,
            computer.height + 30
        ),
        pygame.SRCALPHA
    )

    glow.fill(
        (
            40,
            255,
            100,
            glow_alpha
        )
    )

    screen.blit(
        glow,
        (
            computer.x - 15,
            computer.y - 15
        )
    )

    # Animated screen overlay
    screen_rect = pygame.Rect(
        computer.x + 10,
        computer.y + 10,
        computer.width - 20,
        computer.height - 20
    )

    screen_overlay = pygame.Surface(
        (
            screen_rect.width,
            screen_rect.height
        ),
        pygame.SRCALPHA
    )

    screen_overlay.fill(
        (
            0,
            180,
            60,
            25
        )
    )

    screen.blit(
        screen_overlay,
        (
            screen_rect.x,
            screen_rect.y
        )
    )

    # Scanning line
    scan_y = (
        screen_rect.y
        + (
            current_time // 4
        ) % screen_rect.height
    )

    pygame.draw.line(
        screen,
        GREEN,
        (
            screen_rect.x,
            scan_y
        ),
        (
            screen_rect.right,
            scan_y
        ),
        1
    )

    # Small status light
    pygame.draw.circle(
        screen,
        GREEN,
        (
            computer.right - 10,
            computer.bottom - 10
        ),
        4
    )


# =========================================================
# DRAWER OPENING ANIMATION
# =========================================================

def update_drawer_animation():

    global drawer_open_progress

    if not drawer_opened:
        return

    if drawer_animation_start == 0:
        drawer_open_progress = 1.0
        return

    elapsed = (
        pygame.time.get_ticks()
        - drawer_animation_start
    )

    drawer_open_progress = min(
        1.0,
        elapsed / 700
    )


def draw_drawer_animation():

    if not drawer_opened:
        return

    progress = drawer_open_progress

    # Drawer appears to slide outward
    slide_distance = int(
        35 * progress
    )

    animated_rect = pygame.Rect(
        drawer.x,
        drawer.y + slide_distance,
        drawer.width,
        drawer.height
    )

    shadow_rect = animated_rect.move(
        8,
        10
    )

    pygame.draw.rect(
        screen,
        (5, 5, 8),
        shadow_rect,
        border_radius=4
    )

    pygame.draw.rect(
        screen,
        (45, 48, 52),
        animated_rect,
        border_radius=4
    )

    pygame.draw.rect(
        screen,
        LIGHT_GRAY,
        animated_rect,
        2,
        border_radius=4
    )

    # Handle
    handle = pygame.Rect(
        animated_rect.centerx - 25,
        animated_rect.y + 15,
        50,
        6
    )

    pygame.draw.rect(
        screen,
        GRAY,
        handle,
        border_radius=3
    )

    # Screwdriver hint during opening
    if progress < 1:

        alpha = int(
            255 * progress
        )

        item_surface = small_font.render(
            "SCREWDRIVER FOUND",
            True,
            YELLOW
        )

        item_surface.set_alpha(alpha)

        screen.blit(
            item_surface,
            (
                animated_rect.x - 20,
                animated_rect.bottom + 8
            )
        )


# =========================================================
# DOOR OPENING ANIMATION
# =========================================================

def update_door_animation():

    global door_open_progress
    global game_won

    if not door_animating:
        return

    elapsed = (
        pygame.time.get_ticks()
        - door_animation_start
    )

    door_open_progress = min(
        1.0,
        elapsed / 1800
    )

    if door_open_progress >= 1.0:

        game_won = True


def draw_door_animation():

    if not door_animating:
        return

    progress = door_open_progress

    # Brightness behind opening door
    opening_width = int(
        door.width * progress
    )

    if opening_width > 0:

        light_rect = pygame.Rect(
            door.x,
            door.y,
            opening_width,
            door.height
        )

        light = pygame.Surface(
            (
                max(1, light_rect.width),
                light_rect.height
            ),
            pygame.SRCALPHA
        )

        light.fill(
            (
                180,
                255,
                220,
                int(160 * progress)
            )
        )

        screen.blit(
            light,
            (
                light_rect.x,
                light_rect.y
            )
        )

    # Moving door panel
    remaining_width = int(
        door.width * (1 - progress)
    )

    if remaining_width > 2:

        door_panel = pygame.Rect(
            door.x + opening_width,
            door.y,
            remaining_width,
            door.height
        )

        overlay = pygame.Surface(
            (
                door_panel.width,
                door_panel.height
            ),
            pygame.SRCALPHA
        )

        overlay.fill(
            (
                20,
                10,
                10,
                100
            )
        )

        screen.blit(
            overlay,
            (
                door_panel.x,
                door_panel.y
            )
        )

        pygame.draw.rect(
            screen,
            (130, 160, 150),
            door_panel,
            2
        )

    # Exit light
    glow = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )

    glow.fill(
        (
            180,
            255,
            220,
            int(25 * progress)
        )
    )

    screen.blit(
        glow,
        (0, 0)
    )


# =========================================================
# INVENTORY
# =========================================================

def draw_inventory():

    pygame.draw.rect(
        screen,
        (10, 10, 15),
        (20, 610, 700, 75)
    )

    pygame.draw.rect(
        screen,
        GRAY,
        (20, 610, 700, 75),
        2
    )

    draw_text(
        "INVENTORY",
        35,
        630,
        YELLOW,
        small_font
    )

    x = 180

    for item in inventory:

        pygame.draw.rect(
            screen,
            (45, 50, 60),
            (x, 620, 120, 50),
            border_radius=5
        )

        pygame.draw.rect(
            screen,
            LIGHT_GRAY,
            (x, 620, 120, 50),
            1,
            border_radius=5
        )

        draw_text(
            item,
            x + 10,
            637,
            WHITE,
            small_font
        )

        x += 140


# =========================================================
# TIMER
# =========================================================

def draw_timer():

    if game_start is None:
        return 0

    elapsed = int(
        time.time()
        - game_start
    )

    remaining = max(
        0,
        TIME_LIMIT - elapsed
    )

    minutes = remaining // 60
    seconds = remaining % 60

    timer_text = (
        f"TIME: {minutes:02}:{seconds:02}"
    )

    if remaining < 60:

        pulse = (
            math.sin(
                pygame.time.get_ticks() / 150
            )
            + 1
        ) / 2

        color = (
            int(180 + pulse * 75),
            40,
            40
        )

    else:

        color = WHITE

    draw_text(
        timer_text,
        1000,
        25,
        color,
        font
    )

    return remaining


# =========================================================
# MESSAGE BOX
# =========================================================

def draw_message():

    pygame.draw.rect(
        screen,
        (5, 5, 8),
        (100, 70, 850, 55)
    )

    pygame.draw.rect(
        screen,
        GRAY,
        (100, 70, 850, 55),
        2
    )

    draw_text(
        message,
        120,
        87,
        WHITE,
        small_font
    )


# =========================================================
# POWER PUZZLE
# =========================================================

def draw_power_puzzle():

    overlay = pygame.Surface(
        (WIDTH, HEIGHT)
    )

    overlay.set_alpha(235)
    overlay.fill(BLACK)

    screen.blit(
        overlay,
        (0, 0)
    )

    pygame.draw.rect(
        screen,
        (45, 50, 60),
        (300, 150, 600, 380)
    )

    pygame.draw.rect(
        screen,
        YELLOW,
        (300, 150, 600, 380),
        4
    )

    draw_text(
        "POWER CONTROL SYSTEM",
        410,
        180,
        YELLOW,
        font
    )

    draw_text(
        "Activate switches in the correct order",
        360,
        220,
        WHITE,
        small_font
    )

    draw_text(
        "Sequence: " + str(power_sequence),
        420,
        465,
        GREEN,
        small_font
    )

    for number, rect in switches.items():

        active = number in power_sequence

        if active:
            color = GREEN
        else:
            color = RED

        pygame.draw.rect(
            screen,
            color,
            rect,
            border_radius=5
        )

        pygame.draw.rect(
            screen,
            WHITE,
            rect,
            3,
            border_radius=5
        )

        draw_text(
            str(number),
            rect.x + 42,
            rect.y + 14,
            BLACK,
            font
        )

    draw_text(
        "Press ESC to close",
        450,
        500,
        WHITE,
        small_font
    )


# =========================================================
# COMPUTER PUZZLE
# =========================================================

def draw_computer_puzzle():

    overlay = pygame.Surface(
        (WIDTH, HEIGHT)
    )

    overlay.set_alpha(240)
    overlay.fill(BLACK)

    screen.blit(
        overlay,
        (0, 0)
    )

    pygame.draw.rect(
        screen,
        DARK_GREEN,
        (250, 120, 700, 450)
    )

    pygame.draw.rect(
        screen,
        GREEN,
        (250, 120, 700, 450),
        3
    )

    draw_text(
        "LAB SECURITY TERMINAL",
        440,
        160,
        GREEN,
        font
    )

    draw_text(
        "> SYSTEM BOOTED",
        320,
        220,
        GREEN,
        small_font
    )

    draw_text(
        "> SECURITY ACCESS REQUIRED",
        320,
        255,
        GREEN,
        small_font
    )

    draw_text(
        "CLUE: The password is the name of",
        320,
        310,
        WHITE,
        small_font
    )

    draw_text(
        "the facility where you are trapped.",
        320,
        340,
        WHITE,
        small_font
    )

    draw_text(
        "PASSWORD:",
        320,
        400,
        YELLOW,
        font
    )

    pygame.draw.rect(
        screen,
        BLACK,
        (500, 385, 300, 50)
    )

    pygame.draw.rect(
        screen,
        GREEN,
        (500, 385, 300, 50),
        2
    )

    # Blinking cursor
    cursor = ""

    if (
        pygame.time.get_ticks() // 400
    ) % 2 == 0:

        cursor = "_"

    draw_text(
        password_input + cursor,
        515,
        398,
        GREEN,
        font
    )

    draw_text(
        "Press ENTER to submit",
        420,
        485,
        WHITE,
        small_font
    )

    draw_text(
        "ESC = Exit Terminal",
        430,
        520,
        WHITE,
        small_font
    )


# =========================================================
# DOOR PUZZLE
# =========================================================

def draw_door_puzzle():

    overlay = pygame.Surface(
        (WIDTH, HEIGHT)
    )

    overlay.set_alpha(235)
    overlay.fill(BLACK)

    screen.blit(
        overlay,
        (0, 0)
    )

    pygame.draw.rect(
        screen,
        (40, 40, 50),
        (380, 100, 440, 500)
    )

    pygame.draw.rect(
        screen,
        YELLOW,
        (380, 100, 440, 500),
        4
    )

    draw_text(
        "EXIT SECURITY SYSTEM",
        455,
        135,
        YELLOW,
        font
    )

    draw_text(
        "KEYCARD VERIFIED",
        505,
        180,
        GREEN,
        small_font
    )

    draw_text(
        "ENTER EMERGENCY CODE",
        475,
        220,
        WHITE,
        small_font
    )

    pygame.draw.rect(
        screen,
        BLACK,
        (470, 260, 260, 60)
    )

    pygame.draw.rect(
        screen,
        GREEN,
        (470, 260, 260, 60),
        2
    )

    hidden_code = (
        "*" * len(door_code_input)
    )

    cursor = ""

    if (
        pygame.time.get_ticks() // 400
    ) % 2 == 0:

        cursor = "_"

    draw_text(
        hidden_code + cursor,
        570,
        275,
        GREEN,
        font
    )

    draw_text(
        "CLUE: Emergency protocol created in 2026",
        420,
        350,
        WHITE,
        small_font
    )

    draw_text(
        "Press ENTER to unlock",
        500,
        450,
        GREEN,
        small_font
    )

    draw_text(
        "ESC = Cancel",
        530,
        500,
        WHITE,
        small_font
    )


# =========================================================
# DOOR OPENING SCREEN
# =========================================================

def draw_escape_sequence():

    draw_room()

    draw_computer_glow()

    draw_drawer_animation()

    draw_door_animation()

    draw_inventory()

    draw_timer()

    elapsed = (
        pygame.time.get_ticks()
        - door_animation_start
    )

    if elapsed < 500:

        draw_center_text(
            "ACCESS GRANTED",
            WIDTH // 2,
            100,
            GREEN,
            font
        )

    elif elapsed < 1300:

        draw_center_text(
            "EXIT DOOR UNLOCKED",
            WIDTH // 2,
            100,
            YELLOW,
            font
        )

    else:

        draw_center_text(
            "RUN.",
            WIDTH // 2,
            100,
            GREEN,
            big_font
        )


# =========================================================
# WIN SCREEN
# =========================================================

def draw_win_screen():

    screen.fill(
        (10, 50, 30)
    )

    draw_center_text(
        "YOU ESCAPED!",
        WIDTH // 2,
        220,
        GREEN,
        big_font
    )

    elapsed = int(
        time.time()
        - game_start
    )

    minutes = elapsed // 60
    seconds = elapsed % 60

    draw_center_text(
        f"ESCAPE TIME: {minutes:02}:{seconds:02}",
        WIDTH // 2,
        310,
        WHITE,
        font
    )

    draw_center_text(
        "The laboratory doors finally open...",
        WIDTH // 2,
        370,
        WHITE,
        font
    )

    draw_center_text(
        "Press R to restart | ESC to quit",
        WIDTH // 2,
        470,
        YELLOW,
        font
    )


# =========================================================
# GAME OVER SCREEN
# =========================================================

def draw_game_over():

    screen.fill(
        (60, 10, 10)
    )

    draw_center_text(
        "TIME'S UP",
        WIDTH // 2,
        250,
        RED,
        big_font
    )

    draw_center_text(
        "The laboratory security system locked permanently.",
        WIDTH // 2,
        340,
        WHITE,
        font
    )

    draw_center_text(
        "Press R to restart | ESC to quit",
        WIDTH // 2,
        450,
        YELLOW,
        font
    )


# =========================================================
# RESET GAME
# =========================================================

def reset_game():

    global game_started
    global game_start

    global game_won
    global game_over

    global inventory
    global message

    global flashlight_taken
    global drawer_opened
    global power_on
    global computer_used

    global show_power_puzzle
    global power_sequence

    global show_computer_puzzle
    global password_input

    global show_door_puzzle
    global door_code_input

    global drawer_open_progress
    global drawer_animation_start

    global door_open_progress
    global door_animation_start
    global door_animating

    global power_flash_start

    game_started = False
    game_start = None

    game_won = False
    game_over = False

    inventory = []

    message = (
        "SYSTEM: You are trapped inside an abandoned laboratory."
    )

    flashlight_taken = False
    drawer_opened = False
    power_on = False
    computer_used = False

    show_power_puzzle = False
    power_sequence = []

    show_computer_puzzle = False
    password_input = ""

    show_door_puzzle = False
    door_code_input = ""

    drawer_open_progress = 0.0
    drawer_animation_start = 0

    door_open_progress = 0.0
    door_animation_start = 0
    door_animating = False

    power_flash_start = 0

    if SOUND_ENABLED:
        pygame.mixer.music.stop()


# =========================================================
# MAIN GAME LOOP
# =========================================================

running = True

while running:

    mouse = pygame.mouse.get_pos()

    # =====================================================
    # UPDATE ANIMATIONS
    # =====================================================

    if game_started:

        update_light_flicker()

        update_drawer_animation()

        update_door_animation()


    # =====================================================
    # EVENTS
    # =====================================================

    for event in pygame.event.get():

        # -------------------------------------------------
        # QUIT
        # -------------------------------------------------

        if event.type == pygame.QUIT:

            running = False


        # -------------------------------------------------
        # KEYBOARD EVENTS
        # -------------------------------------------------

        if event.type == pygame.KEYDOWN:

            # Toggle debug hitboxes
            if event.key == pygame.K_h:

                DEBUG_HITBOXES = (
                    not DEBUG_HITBOXES
                )


            # WIN / GAME OVER
            if game_won or game_over:

                if event.key == pygame.K_ESCAPE:

                    running = False

                elif event.key == pygame.K_r:

                    reset_game()


            # Ignore keyboard during door animation
            elif door_animating:

                pass


            # COMPUTER PUZZLE
            elif show_computer_puzzle:

                if event.key == pygame.K_ESCAPE:

                    show_computer_puzzle = False
                    password_input = ""

                    message = (
                        "Terminal closed."
                    )

                    play_sound(click_sound)


                elif event.key == pygame.K_BACKSPACE:

                    password_input = (
                        password_input[:-1]
                    )

                    play_sound(click_sound)


                elif event.key == pygame.K_RETURN:

                    if (
                        password_input.upper()
                        == CORRECT_PASSWORD
                    ):

                        if "Keycard" not in inventory:

                            inventory.append(
                                "Keycard"
                            )

                        computer_used = True

                        show_computer_puzzle = False

                        password_input = ""

                        message = (
                            "ACCESS GRANTED! "
                            "SECURITY KEYCARD ACQUIRED."
                        )

                        play_sound(success_sound)


                    else:

                        password_input = ""

                        message = (
                            "ACCESS DENIED. "
                            "INCORRECT PASSWORD."
                        )

                        play_sound(error_sound)


                else:

                    if event.unicode.isalpha():

                        if len(password_input) < 12:

                            password_input += (
                                event.unicode.upper()
                            )

                            play_sound(click_sound)


            # DOOR PUZZLE
            elif show_door_puzzle:

                if event.key == pygame.K_ESCAPE:

                    show_door_puzzle = False

                    door_code_input = ""

                    message = (
                        "Exit keypad closed."
                    )

                    play_sound(click_sound)


                elif event.key == pygame.K_BACKSPACE:

                    door_code_input = (
                        door_code_input[:-1]
                    )

                    play_sound(click_sound)


                elif event.key == pygame.K_RETURN:

                    if (
                        door_code_input
                        == CORRECT_DOOR_CODE
                    ):

                        show_door_puzzle = False

                        door_animating = True

                        door_animation_start = (
                            pygame.time.get_ticks()
                        )

                        door_open_progress = 0.0

                        message = (
                            "ACCESS GRANTED. "
                            "EXIT DOOR UNLOCKED."
                        )

                        play_sound(unlock_sound)


                    else:

                        door_code_input = ""

                        message = (
                            "ACCESS DENIED. WRONG CODE."
                        )

                        play_sound(error_sound)


                else:

                    if event.unicode.isdigit():

                        if len(door_code_input) < 4:

                            door_code_input += (
                                event.unicode
                            )

                            play_sound(click_sound)


            # POWER PUZZLE
            elif show_power_puzzle:

                if event.key == pygame.K_ESCAPE:

                    show_power_puzzle = False

                    power_sequence = []

                    message = (
                        "Power panel closed."
                    )

                    play_sound(click_sound)


            # START MENU
            elif not game_started:

                if event.key == pygame.K_ESCAPE:

                    running = False


            # NORMAL GAME
            else:

                if event.key == pygame.K_ESCAPE:

                    running = False


        # -------------------------------------------------
        # MOUSE EVENTS
        # -------------------------------------------------

        if event.type == pygame.MOUSEBUTTONDOWN:

            # START GAME
            if not game_started:

                if start_button.collidepoint(mouse):

                    game_started = True

                    game_start = time.time()

                    message = (
                        "SYSTEM: Find a way to restore "
                        "power and escape."
                    )

                    play_sound(click_sound)

                    start_background_music()


            # POWER PUZZLE
            elif (
                show_power_puzzle
                and not game_won
                and not game_over
            ):

                for number, rect in switches.items():

                    if rect.collidepoint(mouse):

                        expected_index = len(
                            power_sequence
                        )

                        if (
                            expected_index
                            < len(
                                CORRECT_POWER_SEQUENCE
                            )
                        ):

                            if (
                                number
                                == CORRECT_POWER_SEQUENCE[
                                    expected_index
                                ]
                            ):

                                power_sequence.append(
                                    number
                                )

                                play_sound(
                                    click_sound
                                )

                                if (
                                    power_sequence
                                    == CORRECT_POWER_SEQUENCE
                                ):

                                    power_on = True

                                    show_power_puzzle = False

                                    power_sequence = []

                                    power_flash_start = (
                                        pygame.time.get_ticks()
                                    )

                                    message = (
                                        "POWER RESTORED! "
                                        "THE COMPUTER IS ONLINE."
                                    )

                                    play_sound(
                                        success_sound
                                    )


                            else:

                                power_sequence = []

                                message = (
                                    "ERROR: WRONG SEQUENCE. "
                                    "SYSTEM RESET."
                                )

                                play_sound(
                                    error_sound
                                )


            # NORMAL GAME
            elif (
                game_started
                and not game_won
                and not game_over
                and not door_animating
                and not show_power_puzzle
                and not show_computer_puzzle
                and not show_door_puzzle
            ):

                # FLASHLIGHT
                if flashlight.collidepoint(mouse):

                    if not flashlight_taken:

                        flashlight_taken = True

                        inventory.append(
                            "Flashlight"
                        )

                        message = (
                            "You found a flashlight. "
                            "The room is now visible."
                        )

                        play_sound(
                            pickup_sound
                        )


                # DRAWER
                elif drawer.collidepoint(mouse):

                    if not drawer_opened:

                        drawer_opened = True

                        drawer_animation_start = (
                            pygame.time.get_ticks()
                        )

                        inventory.append(
                            "Screwdriver"
                        )

                        message = (
                            "You found a screwdriver "
                            "inside the drawer!"
                        )

                        play_sound(
                            pickup_sound
                        )


                    else:

                        message = (
                            "The drawer is empty."
                        )

                        play_sound(
                            click_sound
                        )


                # POWER BOX
                elif power_box.collidepoint(mouse):

                    if (
                        "Screwdriver"
                        not in inventory
                    ):

                        message = (
                            "The power box is sealed. "
                            "Find a screwdriver."
                        )

                        play_sound(
                            error_sound
                        )


                    elif not power_on:

                        show_power_puzzle = True

                        power_sequence = []

                        message = (
                            "Solve the power sequence puzzle."
                        )

                        play_sound(
                            click_sound
                        )


                    else:

                        message = (
                            "Power is already restored."
                        )

                        play_sound(
                            click_sound
                        )


                # COMPUTER
                elif computer.collidepoint(mouse):

                    if not power_on:

                        message = (
                            "The computer has no power."
                        )

                        play_sound(
                            error_sound
                        )


                    elif computer_used:

                        message = (
                            "Terminal already accessed."
                        )

                        play_sound(
                            click_sound
                        )


                    else:

                        show_computer_puzzle = True

                        password_input = ""

                        message = (
                            "Security terminal opened."
                        )

                        play_sound(
                            click_sound
                        )


                # EXIT DOOR
                elif door.collidepoint(mouse):

                    if (
                        "Keycard"
                        not in inventory
                    ):

                        message = (
                            "The exit requires a "
                            "security keycard."
                        )

                        play_sound(
                            error_sound
                        )


                    else:

                        show_door_puzzle = True

                        door_code_input = ""

                        message = (
                            "Keycard accepted. "
                            "Enter emergency code."
                        )

                        play_sound(
                            click_sound
                        )


    # =====================================================
    # DRAW GAME
    # =====================================================

    if not game_started:

        draw_start_menu()


    elif game_won:

        draw_win_screen()


    elif game_over:

        draw_game_over()


    elif door_animating:

        draw_escape_sequence()


    else:

        remaining = (
            TIME_LIMIT
            - int(
                time.time()
                - game_start
            )
        )

        if remaining <= 0:

            game_over = True

            if SOUND_ENABLED:

                pygame.mixer.music.stop()


        else:

            # Background
            draw_room()

            # Drawer animation
            draw_drawer_animation()

            # Computer glow after power
            draw_computer_glow()

            # Darkness before flashlight
            draw_darkness()

            # Flickering lab light
            draw_light_flicker()

            # Power restoration flash
            draw_power_flash()

            # UI
            draw_inventory()

            draw_timer()

            draw_message()


            # Debug hitboxes
            if DEBUG_HITBOXES:

                draw_hitboxes()


            # Hover effects
            if (
                not show_power_puzzle
                and not show_computer_puzzle
                and not show_door_puzzle
            ):

                draw_hover(
                    drawer,
                    mouse,
                    BLUE
                )

                if not flashlight_taken:

                    draw_hover(
                        flashlight,
                        mouse,
                        YELLOW
                    )

                draw_hover(
                    computer,
                    mouse,
                    GREEN
                )

                draw_hover(
                    power_box,
                    mouse,
                    CYAN
                )

                draw_hover(
                    door,
                    mouse,
                    RED
                )


            # Puzzle screens
            if show_power_puzzle:

                draw_power_puzzle()


            if show_computer_puzzle:

                draw_computer_puzzle()


            if show_door_puzzle:

                draw_door_puzzle()


    pygame.display.flip()

    clock.tick(60)


pygame.quit()

sys.exit()