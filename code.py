import random
import time
import board
import busio
import displayio
import rtc
import digitalio
import array
import audiocore
import audiobusio
import gc
import json
import math
import os
import sdcardio
import storage
import fourwire
import adafruit_imageload
import adafruit_ds3231
import circuitpython_st7796s
import xpt2046_circuitpython
import neopixel
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import label
from adafruit_displayio_layout.layouts.page_layout import PageLayout
from xpt2046_circuitpython.exceptions import ReadFailedException
from adafruit_ili9341 import ILI9341
from xpt2046_circuitpython import XPT2046


bnp = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2)
bnp.fill((0, 0, 255))
np = neopixel.NeoPixel(board.D13, 3, brightness=0.2, pixel_order=neopixel.RGB)
np.fill((0, 255, 0))
STARTUP_PROGRESS_ON = (40, 30, 0)
STARTUP_PROGRESS_OFF = (0, 0, 0)
startup_progress_step = 0
NP_READY_BLUE = (0, 0, 40)
NP_CORRECT_GREEN = (0, 40, 0)
NP_INCORRECT_RED = (40, 0, 0)
NP_SKIP_YELLOW = (40, 30, 0)
NP_HINT_CYAN = (0, 30, 40)
NP_OFF = (0, 0, 0)


def tick_startup_progress_leds():
    global startup_progress_step

    try:
        for pixel_index in range(len(np)):
            if pixel_index == startup_progress_step:
                np[pixel_index] = STARTUP_PROGRESS_ON
            else:
                np[pixel_index] = STARTUP_PROGRESS_OFF
        startup_progress_step = (startup_progress_step + 1) % len(np)
    except Exception:
        pass


def set_gameplay_np_color(color):
    try:
        np.fill(color)
    except Exception:
        pass


def set_gameplay_wrong_attempt_leds(wrong_attempts):
    try:
        led_colors = [NP_READY_BLUE, NP_READY_BLUE, NP_READY_BLUE]
        for led_index in range(min(wrong_attempts, len(led_colors))):
            led_colors[led_index] = NP_INCORRECT_RED
        for led_index, led_color in enumerate(led_colors):
            np[led_index] = led_color
    except Exception:
        pass


def _gameplay_memory_text():
    try:
        return "mem_free={}".format(gc.mem_free())
    except Exception:
        return "mem_free=?"


def set_startup_progress_complete():
    try:
        np.fill((0, 40, 0))
    except Exception:
        pass


def set_startup_progress_idle():
    try:
        np.fill(NP_OFF)
    except Exception:
        pass

# Display SPI pins (updated for this hardware revision).
TFT_CS = board.D11
TFT_DC = board.D9
TFT_RST = board.D10
TFT_BACKLIGHT = board.D6

# Touch controller chip-select pin.
TOUCH_CS = board.D5

# SD card socket chip-select pin.
SD_CS = board.D12

# MAX98357A I2S amplifier pins.
AUDIO_BIT_CLOCK = board.A0
AUDIO_WORD_SELECT = board.A1
AUDIO_DATA = board.A3
AUDIO_ENABLE = board.A2
AUDIO_STARTUP_WAVS = (
    "/sd/wavs/_start_lpag.wav",
    "/sd/wavs/_start_hello1.wav",
    "/sd/wavs/_start_hello2.wav",
    "/sd/wavs/_start_hello3.wav",
    "/sd/wavs/_start_helloletsplay.wav",
    "/sd/wavs/_start_hisif.wav",
    "/sd/wavs/_start_hithere.wav",
    "/sd/wavs/_start_lets spell.wav",
    "/sd/wavs/_start_letshavefun.wav",
)
AUDIO_WORDS_DIR = "/sd/wavs"
AUDIOMODE_IMAGE_CANDIDATES = ("/sd/img/_audio.bmp", "/sd/imgs/_audio.bmp")
PICTUREMODE_IDLE_IMAGE_CANDIDATES = (
    "/sd/imgs/_spbee.bmp",
    "/sd/img/_spbee.bmp",
    "/sd/imgs/_sbee.bmp",
    "/sd/img/_sbee.bmp",
)
MODE_PICTURE = "picture"
MODE_SOUND = "sound"
MODE_AUDIO = MODE_SOUND
MUTE_TONES_IN_AUDIO_MODE = False
ENABLE_WAV_FORMAT_CHECK = False
WAV_TARGET_SAMPLE_RATES = (16000, 22050)

DISPLAY_WIDTH = 320
DISPLAY_HEIGHT = 480
DISPLAY_ROTATION = 90
DISPLAY_SPI_BAUDRATE = 12000000

# Touch orientation tuning.
TOUCH_SWAP_XY = False
TOUCH_INVERT_X = True
TOUCH_INVERT_Y = False

BG_COLOR = 0x101820
BUTTON_FILL_COLOR = 0x1F4E79
BUTTON_TEXT_COLOR = 0xFFFFFF
VOWEL_TEXT_COLOR = 0xFFD400
STATUS_TEXT_COLOR = 0xD0D7DE
TITLE_TEXT_COLOR = 0xFFFFFF
DARK_PANEL_COLOR = 0x2B2B2B
WRONG_ANSWER_COLOR = 0xFF6B6B
CORRECT_ANSWER_HINT_COLOR = 0x00C060
KEY_ROW_COLOR_DARK = 0x2E567E
KEY_ROW_COLOR_LIGHT = 0x3A6A99
MATH_GAME_BLUE = 0x26547C
MATH_GAME_ORANGE = 0xB85C00
MATH_GAME_GREEN = 0x1A6B3A
MATH_GAME_GOLD = 0xC9B000
MATH_GAME_RED = 0xA00000

FLOW_BUTTON_WIDTH = 64
FLOW_BUTTON_HEIGHT = 40
FLOW_BUTTON_MARGIN = 8

STATUS_LINE_Y = DISPLAY_HEIGHT - 12

START_ACTIONS_TOP_Y = 340
START_ACTION_BUTTON_WIDTH = 144
START_ACTION_BUTTON_HEIGHT = 42
START_ACTION_BUTTON_GAP_X = 12
START_ACTION_BUTTON_GAP_Y = 8
START_ACTION_LEFT_X = (DISPLAY_WIDTH - ((START_ACTION_BUTTON_WIDTH * 2) + START_ACTION_BUTTON_GAP_X)) // 2
START_ACTION_RIGHT_X = START_ACTION_LEFT_X + START_ACTION_BUTTON_WIDTH + START_ACTION_BUTTON_GAP_X
START_ACTION_BOTTOM_Y = START_ACTIONS_TOP_Y + START_ACTION_BUTTON_HEIGHT + START_ACTION_BUTTON_GAP_Y

KEYBOARD_COLS = 4
KEYBOARD_ROWS = 7
KEY_WIDTH = 74
KEY_HEIGHT = 35
KEY_GAP = 2
KEYBOARD_TOTAL_WIDTH = (KEYBOARD_COLS * KEY_WIDTH) + ((KEYBOARD_COLS - 1) * KEY_GAP)
KEYBOARD_TOTAL_HEIGHT = (KEYBOARD_ROWS * KEY_HEIGHT) + ((KEYBOARD_ROWS - 1) * KEY_GAP)
KEYBOARD_START_X = (DISPLAY_WIDTH - KEYBOARD_TOTAL_WIDTH) // 2
KEYBOARD_START_Y = 190

IMAGE_PANEL_SIZE = 120
IMAGE_PANEL_X = (DISPLAY_WIDTH - IMAGE_PANEL_SIZE) // 2
IMAGE_PANEL_Y = FLOW_BUTTON_MARGIN

FONT_PATHS = {
    #"button": "/fonts/ComicSansMS-19.pcf",
    "button": "/fonts/Calibri-21.pcf",
    "small_button": "/fonts/ComicSansMS-15.pcf",
    "title": "/fonts/EffectsEighty-32.pcf",
    "score": "/fonts/Calibri-21.pcf", #17
}
FONTS = {}
BUTTON_REGISTRY = []
STATUS_LINE_LABELS = []

pages = None
current_page_name = "main"
answer_display_label = None
answer_display_text = ""
sd_card = None
sd_vfs = None
keyboard_page_group = None
keyboard_image_index = 0
keyboard_image_tile = None
keyboard_image_bitmap = None
keyboard_image_file = None
keyboard_image_paths = []
keyboard_image_paths_by_length = {"3": [], "4": [], "5": [], "6+": []}
audio_mode_bitmap_cache = None
audio_mode_palette_cache = None
audio_mode_image_path_cache = None
audio_word_index = 0
audio_word_paths = []
audio_word_paths_by_length = {"3": [], "4": [], "5": [], "6+": []}
current_mode = MODE_PICTURE
keyboard_mode_label = None
keyboard_answer_button = None
TEST_FILE_PATH = "/sd/test.txt"
PLAYERS_FILE_PATH = "/sd/players.txt"
TPLAYERS_FILE_PATH = "/tplayers.txt"
SCORES_FILE_PATH = "/sd/scores.txt"
IMAGE_SELECTION_LOG_PATH = "/sd/image.txt"
AUDIO_SELECTION_LOG_PATH = "/sd/audio.txt"
ENABLE_SELECTION_DEBUG_LOG = False
SUMMARY_TOP_COUNT = 10
SUMMARY_PAGE_LPS_PICTURE = "summary_lps_picture"
SUMMARY_PAGE_LPS_SOUND = "summary_lps_sound"
SUMMARY_PAGE_FIRST_TRY = "summary_first_try"
SUMMARY_PAGE_GPW = "summary_gpw"
GPW_WORD_LENGTHS = ("3", "4", "5", "6", "6+")
SUMMARY_PAGE_ORDER = (
    "main",
    SUMMARY_PAGE_LPS_PICTURE,
    SUMMARY_PAGE_LPS_SOUND,
    SUMMARY_PAGE_FIRST_TRY,
    SUMMARY_PAGE_GPW,
)
SUMMARY_DYNAMIC_PAGES = (
    SUMMARY_PAGE_LPS_PICTURE,
    SUMMARY_PAGE_LPS_SOUND,
    SUMMARY_PAGE_FIRST_TRY,
    SUMMARY_PAGE_GPW,
)

STATS_FILE_PATH = "/sd/stats.json"
DEFAULT_STATS = {"total_games": 0, "total_correct": 0, "high_score": 0, "total_time": 0.0, "total_guesses": 0}

audio_out = None
audio_enable = None
audio_session_active = False
system_rtc = rtc.RTC()
external_rtc = None
last_status_second = None
sd_write_faulted = False

startup_title_label = None
startup_prompt_label = None
startup_summary_label = None
startup_error_label = None
startup_start_button = None
startup_option_buttons = []
startup_option_actions = [None, None, None, None]
startup_error_text = ""

STARTUP_STEP_READY = "ready"
STARTUP_STEP_PLAYER = "player"
STARTUP_STEP_NAME_ENTRY = "name_entry"
STARTUP_STEP_MODE = "mode"
STARTUP_STEP_WORD_LENGTH = "word_length"
STARTUP_STEP_WORD_COUNT = "word_count"

startup_step = STARTUP_STEP_READY
startup_player_names = []
startup_player_page = 0
startup_name_entry_page = 0
startup_new_player_text = ""
startup_selected_player = ""
startup_selected_mode = MODE_PICTURE
startup_selected_word_length = "3"
startup_selected_word_count = 10
MAX_PLAYER_NAME_LEN = 12
WORD_LENGTH_BUCKETS = ("3", "4", "5", "6+")

NAME_ENTRY_COLS = 4
NAME_ENTRY_ROWS = 4
NAME_ENTRY_KEY_WIDTH = 74
NAME_ENTRY_KEY_HEIGHT = 46
NAME_ENTRY_KEY_GAP = 2
NAME_ENTRY_TOTAL_WIDTH = (NAME_ENTRY_COLS * NAME_ENTRY_KEY_WIDTH) + ((NAME_ENTRY_COLS - 1) * NAME_ENTRY_KEY_GAP)
NAME_ENTRY_START_X = (DISPLAY_WIDTH - NAME_ENTRY_TOTAL_WIDTH) // 2
NAME_ENTRY_START_Y = 218

NAME_ENTRY_DYNAMIC_PAGES = (
    ("B", "C", "D", "F", "G", "H", "J", "K"),
    ("L", "M", "N", "P", "Q", "R", "S", "T"),
    ("V", "W", "X", "Y", "Z", "U", "_", ""),
)

name_entry_text_label = None
name_entry_page_label = None
name_entry_dynamic_buttons = []

game_word_list = []
game_word_index = 0
game_total = 0
game_correct = 0
game_correct_total = 0
game_skipped = 0
game_hints_used = 0
game_current_word_hint_used = False
game_hint_word_index = -1
game_current_word_wrong_attempts = 0
game_active = False
game_wrong_no_hint_words = []
game_skipped_words = []
game_round_start_time = None
game_round_elapsed_seconds = 0.0
game_total_guesses = 0
game_first_try_correct_count = 0

results_player_label = None
results_total_label = None
results_attempted_label = None
results_correct_no_hint_label = None
results_correct_with_hint_label = None
results_percent_no_hint_label = None
results_time_label = None
results_guesses_label = None
summary_lps_picture_labels = []
summary_lps_sound_labels = []
summary_first_try_labels = []
summary_gpw_player_label = None
summary_gpw_row_labels = []
summary_gpw_current_player_index = 0
summary_lps_picture_page_group = None
summary_lps_sound_page_group = None
summary_first_try_page_group = None
summary_gpw_page_group = None
summary_registered_buttons = []
summary_registered_status_labels = []
summary_pages_initialized = False


def _normalize_player_name(name_text):
    return name_text.strip()


def _exception_errno(exc):
    try:
        return exc.errno
    except Exception:
        return None


def _is_io_error(exc):
    return _exception_errno(exc) == 5


def _is_missing_file_error(exc):
    return _exception_errno(exc) == 2


def _read_text_with_retry(file_path, attempts=3):
    last_exc = None
    for attempt in range(attempts):
        try:
            with open(file_path, "r") as source_file:
                return source_file.read(), None
        except Exception as exc:
            last_exc = exc
            if _is_io_error(exc) and attempt + 1 < attempts:
                gc.collect()
                time.sleep(0.05)
                continue
            break
    return None, last_exc


def _write_text_with_retry(file_path, text_data, attempts=3):
    last_exc = None
    for attempt in range(attempts):
        try:
            with open(file_path, "w") as destination_file:
                destination_file.write(text_data)
            return True, None
        except Exception as exc:
            last_exc = exc
            if _is_io_error(exc) and attempt + 1 < attempts:
                gc.collect()
                time.sleep(0.05)
                continue
            break
    return False, last_exc


def _parse_player_names(text_data):
    names = []
    for line in text_data.splitlines():
        candidate = _normalize_player_name(line)
        if candidate:
            names.append(candidate)
    return names


def load_player_names(file_path=PLAYERS_FILE_PATH):
    global startup_player_names

    cached_names = []
    for existing_name in startup_player_names:
        normalized = _normalize_player_name(existing_name)
        if normalized:
            cached_names.append(normalized)

    players_text, players_read_exc = _read_text_with_retry(file_path)
    if players_text is not None:
        parsed_names = _parse_player_names(players_text)
        if parsed_names:
            startup_player_names = parsed_names
            return True
    elif players_read_exc is not None and not _is_missing_file_error(players_read_exc):
        print("Player list read failed for {}: {}".format(file_path, players_read_exc))
        if cached_names:
            startup_player_names = cached_names
            print("Using cached player list after read failure.")
        else:
            startup_player_names = ["PLAYER 1"]
        return False

    print("players.txt is missing or empty. Restoring from template...")
    template_content, template_read_exc = _read_text_with_retry(TPLAYERS_FILE_PATH)
    if template_content is None:
        if template_read_exc is not None:
            print("Failed to read template {}: {}".format(TPLAYERS_FILE_PATH, template_read_exc))
    else:
        restore_ok, restore_exc = _write_text_with_retry(file_path, template_content)
        if restore_ok:
            print("Successfully copied {} to {}".format(TPLAYERS_FILE_PATH, file_path))
        else:
            print("Failed to restore players.txt from {}: {}".format(TPLAYERS_FILE_PATH, restore_exc))

    players_text, players_read_exc = _read_text_with_retry(file_path)
    if players_text is not None:
        parsed_names = _parse_player_names(players_text)
        if parsed_names:
            startup_player_names = parsed_names
            return True

    if players_read_exc is not None:
        print("Player list read failed for {}: {}".format(file_path, players_read_exc))

    if cached_names:
        startup_player_names = cached_names
        print("Using cached player list after restore failure.")
    else:
        startup_player_names = ["PLAYER 1"]

    return False


def save_player_names(file_path=PLAYERS_FILE_PATH):
    try:
        with open(file_path, "w") as players_file:
            for name in startup_player_names:
                players_file.write(name + "\n")
        print("Player list saved to {}".format(file_path))
        return True
    except Exception as exc:
        print("Player list save failed for {}: {}".format(file_path, exc))
        return False


def create_new_player_name():
    existing = {}
    for name in startup_player_names:
        existing[name.upper()] = True

    for index in range(1, 200):
        candidate = "PLAYER {}".format(index)
        if candidate.upper() not in existing:
            return candidate

    return "PLAYER NEW"


def add_new_player(name_text=None):
    global startup_selected_player

    if name_text is None:
        new_name = create_new_player_name()
    else:
        new_name = _normalize_player_name(name_text)
        if not new_name:
            new_name = create_new_player_name()

    startup_player_names.append(new_name)
    save_player_names()
    startup_selected_player = new_name
    print("Added player '{}'".format(new_name))
    return new_name


def _normalized_player_name_from_entry():
    trimmed = _normalize_player_name(startup_new_player_text)
    if not trimmed:
        return ""

    return trimmed[:MAX_PLAYER_NAME_LEN]


def _has_player_name(candidate_name):
    candidate_upper = candidate_name.upper()
    for existing_name in startup_player_names:
        if existing_name.upper() == candidate_upper:
            return True
    return False


def _set_name_entry_page(page_index):
    global startup_name_entry_page

    page_count = len(NAME_ENTRY_DYNAMIC_PAGES)
    if page_count <= 0:
        startup_name_entry_page = 0
        return

    startup_name_entry_page = page_index % page_count


def _append_to_new_player_name(char_text):
    global startup_new_player_text

    if len(startup_new_player_text) >= MAX_PLAYER_NAME_LEN:
        return

    startup_new_player_text += char_text


def _backspace_new_player_name():
    global startup_new_player_text
    startup_new_player_text = startup_new_player_text[:-1]


def _name_entry_display_text():
    if startup_new_player_text:
        return startup_new_player_text
    return "_"


def update_name_entry_keyboard_ui():
    if name_entry_text_label is None or name_entry_page_label is None:
        return

    name_entry_text_label.text = _name_entry_display_text()
    name_entry_page_label.text = "Page {}/{}".format(startup_name_entry_page + 1, len(NAME_ENTRY_DYNAMIC_PAGES))

    active_chars = NAME_ENTRY_DYNAMIC_PAGES[startup_name_entry_page]
    for idx in range(8):
        key_text = active_chars[idx]
        key_button = name_entry_dynamic_buttons[idx]
        if key_text:
            _set_button_visual(key_button, key_text, MATH_GAME_BLUE)
        else:
            _set_button_visual(key_button, "", 0x2F3A44)


def _save_new_player_from_entry():
    global startup_selected_player

    candidate_name = _normalized_player_name_from_entry()
    if not candidate_name:
        print("Name entry ignored: empty value")
        return False

    if _has_player_name(candidate_name):
        startup_selected_player = candidate_name
        print("Name entry matched existing player '{}'".format(candidate_name))
        return True

    startup_selected_player = add_new_player(candidate_name)
    return True


def _handle_name_entry_action(action_text):
    global startup_step, startup_new_player_text

    if not action_text:
        return

    if action_text == "BKSP":
        _backspace_new_player_name()
        update_name_entry_keyboard_ui()
        return

    if action_text == "DONE":
        if _save_new_player_from_entry():
            startup_new_player_text = ""
            startup_step = STARTUP_STEP_MODE
            show_page("main")
            update_startup_ui()
        else:
            update_name_entry_keyboard_ui()
        return

    if len(action_text) == 1:
        _append_to_new_player_name(action_text)
        update_name_entry_keyboard_ui()


def _set_button_visual(button_info, text, fill_color, text_color=BUTTON_TEXT_COLOR):
    button_info["text"] = text
    button_info["label"].text = text
    button_info["label"].color = text_color
    button_info["tile"].pixel_shader[0] = fill_color


def _set_page_flow_back_button_text(page_name, text, fill_color=BUTTON_FILL_COLOR):
    for button in BUTTON_REGISTRY:
        if button["page"] == page_name and button["role"] == "flow_back":
            _set_button_visual(button, text, fill_color)
            return True
    return False


def _set_start_option(slot_index, text, action_data, fill_color):
    startup_option_actions[slot_index] = action_data
    _set_button_visual(startup_option_buttons[slot_index], text, fill_color)


def _clear_start_option(slot_index):
    startup_option_actions[slot_index] = None
    _set_button_visual(startup_option_buttons[slot_index], "", 0x2F3A44)


def _startup_summary_text():
    player_text = startup_selected_player if startup_selected_player else "-"
    mode_text = "PIC" if startup_selected_mode == MODE_PICTURE else "AUD"
    return "{} | {} | LEN {} | {}".format(player_text, mode_text, startup_selected_word_length, startup_selected_word_count)


def update_startup_ui():
    if startup_prompt_label is None or startup_summary_label is None or startup_start_button is None:
        return

    startup_summary_label.text = _startup_summary_text()
    if startup_error_label is not None:
        startup_error_label.text = startup_error_text

    if startup_step == STARTUP_STEP_READY:
        startup_prompt_label.text = "Press START"
        _set_button_visual(startup_start_button, "START", MATH_GAME_GREEN)
        for idx in range(4):
            _clear_start_option(idx)
        return

    _set_button_visual(startup_start_button, "", 0x2F3A44)

    if startup_step == STARTUP_STEP_PLAYER:
        startup_prompt_label.text = "Select Player"

        first_index = startup_player_page * 3
        for idx in range(3):
            name_index = first_index + idx
            if name_index < len(startup_player_names):
                player_name = startup_player_names[name_index]
                _set_start_option(idx, player_name, {"kind": "player", "value": player_name}, MATH_GAME_BLUE)
            else:
                _clear_start_option(idx)

        next_index = first_index + 3
        if next_index < len(startup_player_names):
            _set_start_option(3, "MORE", {"kind": "more_players", "value": startup_player_page + 1}, MATH_GAME_GOLD)
        else:
            _set_start_option(3, "NEW", {"kind": "new_player", "value": "NEW"}, MATH_GAME_ORANGE)
        return

    if startup_step == STARTUP_STEP_MODE:
        startup_prompt_label.text = "Select Game Mode"
        _set_start_option(0, "Picture", {"kind": "mode", "value": MODE_PICTURE}, MATH_GAME_BLUE)
        _set_start_option(1, "Sound", {"kind": "mode", "value": MODE_AUDIO}, MATH_GAME_ORANGE)
        _clear_start_option(2)
        _clear_start_option(3)
        return

    if startup_step == STARTUP_STEP_WORD_LENGTH:
        startup_prompt_label.text = "Select Word Length"
        _set_start_option(0, "3", {"kind": "word_length", "value": "3"}, MATH_GAME_BLUE)
        _set_start_option(1, "4", {"kind": "word_length", "value": "4"}, MATH_GAME_ORANGE)
        _set_start_option(2, "5", {"kind": "word_length", "value": "5"}, MATH_GAME_GREEN)
        _set_start_option(3, "6+", {"kind": "word_length", "value": "6+"}, MATH_GAME_GOLD)
        return

    if startup_step == STARTUP_STEP_WORD_COUNT:
        startup_prompt_label.text = "How Many Words?"
        _set_start_option(0, "10", {"kind": "word_count", "value": 10}, MATH_GAME_ORANGE)
        _set_start_option(1, "20", {"kind": "word_count", "value": 20}, MATH_GAME_BLUE)
        _set_start_option(2, "35", {"kind": "word_count", "value": 35}, MATH_GAME_GOLD)
        _set_start_option(3, "50", {"kind": "word_count", "value": 50}, MATH_GAME_GREEN)
        return


def begin_startup_flow():
    global startup_step, startup_player_page, startup_name_entry_page, startup_new_player_text

    _unload_summary_pages()
    startup_step = STARTUP_STEP_PLAYER
    startup_player_page = 0
    startup_name_entry_page = 0
    startup_new_player_text = ""
    load_player_names()
    update_startup_ui()


def _goto_next_startup_step():
    global startup_step

    if startup_step == STARTUP_STEP_PLAYER:
        startup_step = STARTUP_STEP_MODE
    elif startup_step == STARTUP_STEP_MODE:
        startup_step = STARTUP_STEP_WORD_LENGTH
    elif startup_step == STARTUP_STEP_WORD_LENGTH:
        startup_step = STARTUP_STEP_WORD_COUNT

    update_startup_ui()


def _goto_previous_startup_step():
    global startup_step

    if startup_step == STARTUP_STEP_WORD_COUNT:
        startup_step = STARTUP_STEP_WORD_LENGTH
    elif startup_step == STARTUP_STEP_WORD_LENGTH:
        startup_step = STARTUP_STEP_MODE
    elif startup_step == STARTUP_STEP_MODE:
        startup_step = STARTUP_STEP_PLAYER
    elif startup_step == STARTUP_STEP_NAME_ENTRY:
        startup_step = STARTUP_STEP_PLAYER
    elif startup_step == STARTUP_STEP_PLAYER:
        startup_step = STARTUP_STEP_READY

    update_startup_ui()


def _select_random_unique_items(items, count):
    """Select random unique items from a list (CircuitPython compatible)."""
    if count >= len(items):
        return items[:]
    
    selected = []
    available = items[:]
    for _ in range(count):
        index = random.randint(0, len(available) - 1)
        selected.append(available[index])
        available.pop(index)
    return selected


def reset_game_session_state(clear_word_list=False):
    global game_word_list, game_word_index, game_total, game_correct, game_correct_total
    global game_skipped, game_hints_used, game_current_word_hint_used, game_hint_word_index, game_current_word_wrong_attempts, game_active
    global game_wrong_no_hint_words, game_skipped_words
    global game_round_start_time, game_round_elapsed_seconds, game_total_guesses, game_first_try_correct_count

    if clear_word_list:
        game_word_list = []
    game_word_index = 0
    game_total = 0
    game_correct = 0
    game_correct_total = 0
    game_skipped = 0
    game_hints_used = 0
    game_current_word_hint_used = False
    game_hint_word_index = -1
    game_current_word_wrong_attempts = 0
    game_active = False
    game_wrong_no_hint_words = []
    game_skipped_words = []
    game_round_start_time = None
    game_round_elapsed_seconds = 0.0
    game_total_guesses = 0
    game_first_try_correct_count = 0
    _set_keyboard_answer_button_visible(False)


def set_startup_error_message(message_text=""):
    global startup_error_text
    startup_error_text = message_text
    if startup_error_label is not None:
        startup_error_label.text = startup_error_text


def abort_game_due_to_asset_failure(asset_path, exc, failure_kind):
    global game_active, startup_step, startup_player_page, startup_new_player_text

    print("{} for {}: {}".format(failure_kind, asset_path, exc))
    game_active = False
    stop_audio_session()
    set_gameplay_np_color(NP_OFF)
    clear_answer_text()
    refresh_answer_display()
    _set_keyboard_answer_button_visible(False)
    startup_step = STARTUP_STEP_READY
    startup_player_page = 0
    startup_new_player_text = ""
    set_startup_error_message("ASSET READ FAILED\nRESTART DEVICE")
    _set_page_flow_back_button_text("keyboard", "BACK", BUTTON_FILL_COLOR)
    show_page("main")
    update_startup_ui()
    update_status_line(force=True)


def finalize_startup_flow():
    print("[DEBUG] Entered finalize_startup_flow")  # Confirm function entry
    global game_word_list, game_word_index, game_total, game_correct, game_correct_total, game_skipped, game_active
    global game_hints_used, game_current_word_hint_used, game_hint_word_index
    global game_wrong_no_hint_words, game_skipped_words
    global game_round_start_time, game_round_elapsed_seconds, game_total_guesses, game_first_try_correct_count
    global startup_step
    set_game_mode(startup_selected_mode)
    # Select the correct asset list
    if startup_selected_mode == MODE_PICTURE:
        length_map = keyboard_image_paths_by_length
        asset_list = keyboard_image_paths[:]
    else:
        length_map = audio_word_paths_by_length
        asset_list = audio_word_paths[:]

    selected_bucket = length_map.get(startup_selected_word_length, [])
    asset_list = selected_bucket[:]

    print("[DEBUG] Asset list prepared, selecting words...")  # Confirm asset list setup
    # Randomly select X unique words
    word_count = min(startup_selected_word_count, len(asset_list))
    if word_count <= 0:
        print("No words available for selected length '{}' in mode '{}'".format(startup_selected_word_length, startup_selected_mode))
        startup_step = STARTUP_STEP_WORD_LENGTH
        update_startup_ui()
        return

    game_word_list = _select_random_unique_items(asset_list, word_count)
    append_selected_words_debug_log(startup_selected_mode, game_word_list)
    print("[DEBUG] Selected word list:")
    for i, w in enumerate(game_word_list):
        print("  {}: {}".format(i+1, w))
    game_word_index = 0
    game_total = word_count
    game_correct = 0
    game_correct_total = 0
    game_skipped = 0
    game_hints_used = 0
    game_current_word_hint_used = False
    game_hint_word_index = -1
    game_active = True
    game_wrong_no_hint_words = []
    game_skipped_words = []
    game_round_start_time = time.monotonic()
    game_round_elapsed_seconds = 0.0
    game_total_guesses = 0
    game_first_try_correct_count = 0
    print(
        "Start game: player='{}' mode='{}' length='{}' words={}".format(
            startup_selected_player,
            startup_selected_mode,
            startup_selected_word_length,
            startup_selected_word_count,
        )
    )
    print("[DEBUG] finalize_startup_flow completed ({})".format(_gameplay_memory_text()))  # Confirm function exit
    if startup_selected_mode == MODE_AUDIO:
        start_audio_session()
    else:
        stop_audio_session()
    set_startup_error_message("")
    _set_page_flow_back_button_text("keyboard", "QUIT", MATH_GAME_ORANGE)
    show_page("keyboard")
    show_current_game_word()


def show_current_game_word():
    """Update the UI to show the current word/image/audio."""
    global game_word_list, game_word_index, game_active, keyboard_image_bitmap, keyboard_image_tile
    global game_current_word_hint_used, game_hint_word_index, game_current_word_wrong_attempts
    print("[DEBUG] Showing current word. Index: {}, Active: {} ({})".format(game_word_index, game_active, _gameplay_memory_text()))
    if not game_active or game_word_index >= len(game_word_list):
        print("[DEBUG] No active game or index out of range. ({})".format(_gameplay_memory_text()))
        return

    if game_word_index != game_hint_word_index:
        game_current_word_hint_used = False
        game_hint_word_index = game_word_index
    game_current_word_wrong_attempts = 0

    clear_last_answer_label()
    _set_keyboard_answer_button_visible(False)
    set_gameplay_wrong_attempt_leds(0)

    # Set the current asset index for answer checking and display
    if current_mode == MODE_PICTURE:
        # Load and display the image directly from the randomized list
        image_path = game_word_list[game_word_index]
        print("[DEBUG] Displaying image: {} ({})".format(image_path, _gameplay_memory_text()))
        # Clear old image first
        clear_keyboard_panel_image()
        try:
            with open(image_path, "rb") as f:
                keyboard_image_bitmap, keyboard_image_palette = adafruit_imageload.load(f)
            keyboard_image_tile = displayio.TileGrid(
                keyboard_image_bitmap,
                pixel_shader=keyboard_image_palette,
                x=IMAGE_PANEL_X,
                y=IMAGE_PANEL_Y,
            )
            keyboard_page_group.append(keyboard_image_tile)
            print("[DEBUG] Image loaded and displayed successfully ({})".format(_gameplay_memory_text()))
        except Exception as exc:
            abort_game_due_to_asset_failure(image_path, exc, "Failed to load image")
            return
    else:
        # Play audio directly from the randomized list
        audio_path = game_word_list[game_word_index]
        print("[DEBUG] Playing audio: {} ({})".format(audio_path, _gameplay_memory_text()))
        try:
            global audio_word_index
            audio_word_index = audio_word_paths.index(audio_path)
            update_keyboard_panel_image()
            if not play_word_audio_for_current_image():
                raise RuntimeError("audio playback failed")
        except Exception as exc:
            abort_game_due_to_asset_failure(audio_path, exc, "Failed to play audio")
            return
    clear_answer_text()
    refresh_answer_display()
    update_status_line(force=True)
    set_gameplay_np_color(NP_READY_BLUE)


def handle_skip_word():
    global game_skipped, game_word_index, game_active
    if game_active:
        _track_skipped_word(current_prompt_answer())
        set_gameplay_np_color(NP_SKIP_YELLOW)
        game_skipped += 1
        advance_to_next_word()
        update_status_line(force=True)


def advance_to_next_word():
    global game_word_index, game_active, game_total
    print("[DEBUG] Advancing to next word. Current index: {}, Total: {} ({})".format(game_word_index, game_total, _gameplay_memory_text()))
    game_word_index += 1
    if game_word_index >= game_total:
        print("[DEBUG] Word limit reached. Ending game. ({})".format(_gameplay_memory_text()))
        game_active = False
        stop_audio_session()
        update_status_line(force=True)
        show_results_page()
    else:
        show_current_game_word()


def handle_startup_option(slot_index):
    global startup_selected_player, startup_selected_mode, startup_selected_word_length
    global startup_selected_word_count, startup_player_page
    global startup_step, startup_name_entry_page, startup_new_player_text

    if slot_index < 0 or slot_index >= len(startup_option_actions):
        return

    action_data = startup_option_actions[slot_index]
    if action_data is None:
        return

    action_kind = action_data.get("kind")
    action_value = action_data.get("value")

    if action_kind == "player":
        startup_selected_player = action_value
        _goto_next_startup_step()
        return

    if action_kind == "new_player":
        startup_new_player_text = ""
        startup_step = STARTUP_STEP_NAME_ENTRY
        _set_name_entry_page(0)
        update_name_entry_keyboard_ui()
        show_page("name_entry")
        return

    if action_kind == "more_players":
        startup_player_page = action_value
        update_startup_ui()
        return

    if action_kind == "mode":
        startup_selected_mode = action_value
        _goto_next_startup_step()
        return

    if action_kind == "word_length":
        startup_selected_word_length = action_value
        _goto_next_startup_step()
        return

    if action_kind == "word_count":
        startup_selected_word_count = action_value
        finalize_startup_flow()
        return


def build_status_line_text():
    try:
        now = system_rtc.datetime
        hour_24 = now.tm_hour
        hour_12 = hour_24 % 12
        if hour_12 == 0:
            hour_12 = 12
        am_pm = "am" if hour_24 < 12 else "pm"
        clock_text = "{:02d}:{:02d} {}".format(hour_12, now.tm_min, am_pm)
    except Exception:
        clock_text = "--:-- --"

    remaining_questions = 0
    if game_active:
        remaining_questions = game_total - game_word_index
        if remaining_questions < 0:
            remaining_questions = 0

    return "{} | R {} | C {} | H {} | S {}".format(
        clock_text,
        remaining_questions,
        game_correct,
        game_hints_used,
        game_skipped,
    )


def update_status_line(force=False):
    global last_status_second

    try:
        now = system_rtc.datetime
        current_second = now.tm_sec
    except Exception:
        current_second = None

    if not force and current_second == last_status_second:
        return

    last_status_second = current_second
    status_text = build_status_line_text()
    for status_label in STATUS_LINE_LABELS:
        status_label.text = status_text


def _set_cs_high(pin):
    cs = digitalio.DigitalInOut(pin)
    cs.direction = digitalio.Direction.OUTPUT
    cs.value = True
    cs.deinit()


def prepare_spi_chip_selects():
    # Keep non-target SPI devices deselected during startup.
    _set_cs_high(TFT_CS)
    _set_cs_high(TOUCH_CS)
    _set_cs_high(SD_CS)


def init_real_time_clock():
    global external_rtc

    try:
        i2c = board.STEMMA_I2C() if hasattr(board, "STEMMA_I2C") else board.I2C()
        external_rtc = adafruit_ds3231.DS3231(i2c)
        print("DS3231 initialized")
    except Exception as exc:
        external_rtc = None
        print("DS3231 init failed: {}".format(exc))
        fallback_time = time.struct_time((2026, 1, 1, 13, 0, 0, 3, 1, -1))
        system_rtc.datetime = fallback_time
        print("System RTC set to fallback time: 2026-01-01 13:00:00")
        return False

    # Sync the CircuitPython system clock from the external RTC.
    try:
        rtc_time = external_rtc.datetime
        system_rtc.datetime = rtc_time
        print(
            "System RTC synced: {:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                rtc_time.tm_year,
                rtc_time.tm_mon,
                rtc_time.tm_mday,
                rtc_time.tm_hour,
                rtc_time.tm_min,
                rtc_time.tm_sec,
            )
        )
    except Exception as exc:
        print("RTC sync failed: {}".format(exc))

    if False:  # change to True if you want to set the time!
        #                     year, mon, date, hour, min, sec, wday, yday, isdst
        t = time.struct_time((2026, 5, 18, 11, 51, 0, 1, -1, -1))
        # you must set year, mon, date, hour, min, sec and weekday
        # yearday is not supported, isdst can be set but we don't do anything with it at this time
        print("Setting time to:", t)
        system_rtc.datetime = t
        if external_rtc is not None:
            external_rtc.datetime = t

    return True


def load_fonts():
    for font_key in FONT_PATHS:
        FONTS[font_key] = bitmap_font.load_font(FONT_PATHS[font_key])


def init_audio_output():
    global audio_out, audio_enable

    try:
        audio_enable = digitalio.DigitalInOut(AUDIO_ENABLE)
        audio_enable.direction = digitalio.Direction.OUTPUT
        audio_enable.value = True

        audio_out = audiobusio.I2SOut(
            bit_clock=AUDIO_BIT_CLOCK,
            word_select=AUDIO_WORD_SELECT,
            data=AUDIO_DATA,
        )
        # print("I2S audio initialized")
        return True
    except Exception as exc:
        print("I2S audio init failed: {}".format(exc))
        shutdown_audio_output()
        return False


def ensure_audio_output():
    if audio_out is None:
        return init_audio_output()

    if audio_enable is not None:
        try:
            audio_enable.value = True
        except Exception:
            pass
    return True


def start_audio_session():
    global audio_session_active
    audio_session_active = True
    return ensure_audio_output()


def stop_audio_session():
    global audio_session_active
    audio_session_active = False
    shutdown_audio_output()


def play_startup_wav(file_path=None):
    if audio_out is None:
        return False

    if file_path is None:
        file_path = random.choice(AUDIO_STARTUP_WAVS)

    wave_file = None
    try:
        wave_file = open(file_path, "rb")
        wave = audiocore.WaveFile(wave_file)
        audio_out.play(wave)
        while audio_out.playing:
            time.sleep(0.01)
        print("Startup WAV played: {}".format(file_path))
        return True
    except Exception as exc:
        print("Startup WAV playback failed for {}: {}".format(file_path, exc))
        return False
    finally:
        if wave_file is not None:
            try:
                wave_file.close()
            except Exception:
                pass


def play_wav_file_isolated(file_path):
    """Play a WAV with minimal runtime activity to reduce audio artifacts."""
    if audio_out is None:
        return False

    wave_file = None
    gc_was_enabled = False
    try:
        # Clear pending allocations first, then avoid GC pauses during stream playback.
        gc.collect()
        try:
            gc_was_enabled = gc.isenabled()
        except Exception:
            gc_was_enabled = False
        if gc_was_enabled:
            gc.disable()

        wave_file = open(file_path, "rb")
        wave = audiocore.WaveFile(wave_file)
        audio_out.play(wave)
        while audio_out.playing:
            # Keep loop lightweight while the DMA stream runs.
            time.sleep(0.001)
        print("Isolated WAV played: {}".format(file_path))
        return True
    except Exception as exc:
        print("Isolated WAV playback failed for {}: {}".format(file_path, exc))
        return False
    finally:
        if wave_file is not None:
            try:
                wave_file.close()
            except Exception:
                pass
        if gc_was_enabled:
            try:
                gc.enable()
            except Exception:
                pass


def create_tone_sample(frequency=440, sample_rate=8000, tone_volume=0.1):
    period_length = sample_rate // frequency

    if period_length <= 0:
        return None

    sine_wave = array.array("H", [0] * period_length)
    for index in range(period_length):
        sine_wave[index] = int(
            (math.sin((math.pi * 2 * frequency * index) / sample_rate) * tone_volume + 1)
            * ((2 ** 15) - 1)
        )

    return audiocore.RawSample(sine_wave, sample_rate=sample_rate)


def play_beep_sequence(sequence):
    if audio_out is None:
        return False

    for frequency, on_time, off_time in sequence:
        beep_sample = create_tone_sample(frequency=frequency)
        if beep_sample is None:
            continue
        audio_out.play(beep_sample, loop=True)
        time.sleep(on_time)
        audio_out.stop()
        time.sleep(off_time)

    return True


def play_startup_beep_sequence():
    if not play_beep_sequence(((440, 0.25, 0.25), (440, 0.25, 0.25), (440, 0.25, 0.25))):
        return False

    print("Startup beep sequence complete")
    return True


def current_word_wav_path():
    if current_mode == MODE_AUDIO:
        if not audio_word_paths:
            return None
        return audio_word_paths[audio_word_index]

    word = current_image_answer()
    if not word:
        return None
    return "{}/{}.wav".format(AUDIO_WORDS_DIR, word)


def play_word_audio_for_current_image():
    wav_path = current_word_wav_path()
    if not wav_path:
        print("No prompt audio available for mode '{}'".format(current_mode))
        return False

    if not ensure_audio_output():
        return False

    played_ok = play_wav_file_isolated(wav_path)
    if not audio_session_active:
        shutdown_audio_output()
    return played_ok


def play_result_feedback(is_correct):
    if MUTE_TONES_IN_AUDIO_MODE and current_mode == MODE_AUDIO:
        return True

    if not ensure_audio_output():
        return False

    if is_correct:
        sequence = ((660, 0.12, 0.05), (880, 0.18, 0.05))
    else:
        sequence = ((220, 0.16, 0.05), (180, 0.22, 0.05))
    result = play_beep_sequence(sequence)
    if not audio_session_active:
        shutdown_audio_output()
    return result


def play_button_feedback():
    """Play a very short click tone for any button press."""
    if MUTE_TONES_IN_AUDIO_MODE and current_mode == MODE_AUDIO:
        return True

    if not ensure_audio_output():
        return False

    result = play_beep_sequence(((960, 0.025, 0.0),))
    if not audio_session_active:
        shutdown_audio_output()
    return result


def shutdown_audio_output():
    global audio_out, audio_enable

    if audio_out is not None:
        try:
            audio_out.stop()
        except Exception:
            pass
        try:
            audio_out.deinit()
        except Exception:
            pass
        audio_out = None

    if audio_enable is not None:
        try:
            audio_enable.value = False
        except Exception:
            pass
        try:
            audio_enable.deinit()
        except Exception:
            pass
        audio_enable = None


def refresh_answer_display():
    if answer_display_label is not None:
        answer_display_label.text = answer_display_text if answer_display_text else "_"


def clear_answer_text():
    global answer_display_text
    answer_display_text = ""
    refresh_answer_display()


def clear_last_answer_label():
    """Blank the last-wrong-answer label (call when a new image loads)."""
    if keyboard_mode_label is not None:
        keyboard_mode_label.color = WRONG_ANSWER_COLOR
        keyboard_mode_label.text = ""


def _set_keyboard_answer_button_visible(visible):
    global keyboard_answer_button

    if keyboard_answer_button is None:
        return

    keyboard_answer_button["visible"] = visible
    keyboard_answer_button["active"] = visible
    try:
        keyboard_answer_button["tile"].hidden = not visible
    except Exception:
        pass
    try:
        keyboard_answer_button["label"].hidden = not visible
    except Exception:
        pass


def reveal_answer_for_current_word():
    _set_keyboard_answer_button_visible(True)
    clear_answer_text()
    mark_hint_for_current_word()
    show_correct_answer_hint()


def show_wrong_answer_label(typed_text):
    """Show the player's incorrect spelling in light red."""
    if keyboard_mode_label is not None:
        keyboard_mode_label.color = WRONG_ANSWER_COLOR
        keyboard_mode_label.text = typed_text


def show_correct_answer_hint():
    """Show the correct spelling in green so the player can type it in."""
    answer = current_prompt_answer()
    if keyboard_mode_label is not None and answer:
        keyboard_mode_label.color = CORRECT_ANSWER_HINT_COLOR
        keyboard_mode_label.text = answer.upper()


def mark_hint_for_current_word():
    global game_hints_used, game_current_word_hint_used

    if not game_active:
        return

    if game_current_word_hint_used:
        return

    game_current_word_hint_used = True
    game_hints_used += 1
    update_status_line(force=True)


def update_keyboard_mode_label():
    """Called on mode change — clear the last-answer label for the new mode."""
    clear_last_answer_label()


def _answer_from_asset_path(asset_path):
    file_name = asset_path.split("/")[-1]
    dot_index = file_name.rfind(".")
    if dot_index > 0:
        return file_name[:dot_index].lower()
    return file_name.lower()


def _length_bucket_for_answer(answer_text):
    answer_length = len(answer_text)
    if answer_length <= 3:
        return "3"
    if answer_length == 4:
        return "4"
    if answer_length == 5:
        return "5"
    return "6+"


def _empty_length_buckets():
    return {"3": [], "4": [], "5": [], "6+": []}


def _normalized_bucket_key(bucket_key):
    key_text = str(bucket_key).strip()
    if key_text in ("6", "6+"):
        return "6+"
    if key_text in ("3", "4", "5"):
        return key_text
    return None


def _normalize_manifest_paths(manifest_map, required_suffix):
    normalized = _empty_length_buckets()
    if not isinstance(manifest_map, dict):
        return None

    suffix_text = required_suffix.lower()
    for key_text in manifest_map:
        bucket_key = _normalized_bucket_key(key_text)
        if bucket_key is None:
            continue

        bucket_items = manifest_map.get(key_text)
        if not isinstance(bucket_items, (list, tuple)):
            continue

        for candidate in bucket_items:
            if not isinstance(candidate, str):
                continue
            path_text = candidate.strip()
            if not path_text:
                continue
            if not path_text.lower().endswith(suffix_text):
                continue

            file_name = path_text.split("/")[-1]
            if file_name.startswith("_"):
                continue

            normalized[bucket_key].append(path_text)

    total_count = 0
    for bucket in normalized:
        total_count += len(normalized[bucket])
    if total_count <= 0:
        return None

    for bucket in normalized:
        normalized[bucket].sort()
    return normalized


def _flatten_bucket_map(bucket_map):
    return bucket_map["3"] + bucket_map["4"] + bucket_map["5"] + bucket_map["6+"]


def _load_manifest_bucket_map(module_name, attr_name, required_suffix):
    try:
        module_obj = __import__(module_name)
    except Exception:
        return None

    try:
        raw_map = getattr(module_obj, attr_name)
    except Exception:
        return None

    return _normalize_manifest_paths(raw_map, required_suffix)


def load_keyboard_image_paths(folder_path="/img"):
    global keyboard_image_paths, keyboard_image_index, keyboard_image_paths_by_length

    manifest_buckets = _load_manifest_bucket_map("pictures", "PICTURES_BY_LENGTH", ".bmp")
    if manifest_buckets is not None:
        keyboard_image_paths_by_length = manifest_buckets
        keyboard_image_paths = _flatten_bucket_map(manifest_buckets)
        keyboard_image_index = 0

        if not keyboard_image_paths:
            print("Picture manifest loaded but empty")
            return False

        print("Loaded {} keyboard images from pictures.py manifest".format(len(keyboard_image_paths)))
        print(
            "Image length buckets 3:{} 4:{} 5:{} 6+:{}".format(
                len(keyboard_image_paths_by_length["3"]),
                len(keyboard_image_paths_by_length["4"]),
                len(keyboard_image_paths_by_length["5"]),
                len(keyboard_image_paths_by_length["6+"]),
            )
        )
        return True

    try:
        names = os.listdir(folder_path)
    except Exception as exc:
        keyboard_image_paths = []
        keyboard_image_index = 0
        print("Image folder read failed for {}: {}".format(folder_path, exc))
        return False

    bmp_names = []
    for name in names:
        lower_name = name.lower()
        if lower_name.endswith(".bmp") and not name.startswith("_"):
            bmp_names.append(name)

    bmp_names.sort()
    keyboard_image_paths = ["{}/{}".format(folder_path, name) for name in bmp_names]
    keyboard_image_paths_by_length = _empty_length_buckets()
    for image_path in keyboard_image_paths:
        answer_text = _answer_from_asset_path(image_path)
        length_bucket = _length_bucket_for_answer(answer_text)
        keyboard_image_paths_by_length[length_bucket].append(image_path)
    keyboard_image_index = 0

    if not keyboard_image_paths:
        print("No BMP images found in {}".format(folder_path))
        return False

    print("Loaded {} keyboard images from {}".format(len(keyboard_image_paths), folder_path))
    for index, image_path in enumerate(keyboard_image_paths):
        print("  {}".format(image_path))
        if ((index + 1) % 25) == 0:
            tick_startup_progress_leds()
    print(
        "Image length buckets 3:{} 4:{} 5:{} 6+:{}".format(
            len(keyboard_image_paths_by_length["3"]),
            len(keyboard_image_paths_by_length["4"]),
            len(keyboard_image_paths_by_length["5"]),
            len(keyboard_image_paths_by_length["6+"]),
        )
    )
    return True


def load_audio_word_paths(folder_path=AUDIO_WORDS_DIR):
    global audio_word_paths, audio_word_index, audio_word_paths_by_length

    manifest_buckets = _load_manifest_bucket_map("sounds", "SOUNDS_BY_LENGTH", ".wav")
    if manifest_buckets is not None:
        audio_word_paths_by_length = manifest_buckets
        audio_word_paths = _flatten_bucket_map(manifest_buckets)
        audio_word_index = 0

        if not audio_word_paths:
            print("Sound manifest loaded but empty")
            return False

        print("Loaded {} audio prompts from sounds.py manifest".format(len(audio_word_paths)))
        print(
            "Audio length buckets 3:{} 4:{} 5:{} 6+:{}".format(
                len(audio_word_paths_by_length["3"]),
                len(audio_word_paths_by_length["4"]),
                len(audio_word_paths_by_length["5"]),
                len(audio_word_paths_by_length["6+"]),
            )
        )
        return True

    try:
        names = os.listdir(folder_path)
    except Exception as exc:
        audio_word_paths = []
        audio_word_index = 0
        print("Audio folder read failed for {}: {}".format(folder_path, exc))
        return False

    wav_names = []
    for name in names:
        if name.lower().endswith(".wav") and not name.startswith("_"):
            wav_names.append(name)

    wav_names.sort()
    audio_word_paths = ["{}/{}".format(folder_path, name) for name in wav_names]
    audio_word_paths_by_length = _empty_length_buckets()
    for wav_path in audio_word_paths:
        answer_text = _answer_from_asset_path(wav_path)
        length_bucket = _length_bucket_for_answer(answer_text)
        audio_word_paths_by_length[length_bucket].append(wav_path)
    audio_word_index = 0

    if not audio_word_paths:
        print("No WAV files found in {}".format(folder_path))
        return False

    print("Loaded {} audio prompts from {}".format(len(audio_word_paths), folder_path))
    for index, wav_path in enumerate(audio_word_paths):
        print("  {}".format(wav_path))
        if ((index + 1) % 25) == 0:
            tick_startup_progress_leds()
    print(
        "Audio length buckets 3:{} 4:{} 5:{} 6+:{}".format(
            len(audio_word_paths_by_length["3"]),
            len(audio_word_paths_by_length["4"]),
            len(audio_word_paths_by_length["5"]),
            len(audio_word_paths_by_length["6+"]),
        )
    )
    return True


def _le_u16(data, offset):
    return data[offset] | (data[offset + 1] << 8)


def _le_u32(data, offset):
    return (
        data[offset]
        | (data[offset + 1] << 8)
        | (data[offset + 2] << 16)
        | (data[offset + 3] << 24)
    )


def inspect_wav_header(file_path):
    """Return parsed WAV header details or None when header cannot be parsed."""
    try:
        with open(file_path, "rb") as wav_file:
            header = wav_file.read(512)
    except Exception as exc:
        print("WAV inspect read failed for {}: {}".format(file_path, exc))
        return None

    if len(header) < 12:
        return None
    if header[0:4] != b"RIFF" or header[8:12] != b"WAVE":
        return None

    index = 12
    fmt_info = None
    data_chunk_found = False

    while index + 8 <= len(header):
        chunk_id = header[index : index + 4]
        chunk_size = _le_u32(header, index + 4)
        chunk_data_start = index + 8
        chunk_data_end = chunk_data_start + chunk_size

        if chunk_id == b"fmt ":
            if chunk_data_start + 16 > len(header):
                return None
            audio_format = _le_u16(header, chunk_data_start)
            channel_count = _le_u16(header, chunk_data_start + 2)
            sample_rate = _le_u32(header, chunk_data_start + 4)
            bits_per_sample = _le_u16(header, chunk_data_start + 14)
            fmt_info = {
                "audio_format": audio_format,
                "channels": channel_count,
                "sample_rate": sample_rate,
                "bits_per_sample": bits_per_sample,
            }
        elif chunk_id == b"data":
            data_chunk_found = True

        step = 8 + chunk_size
        if step % 2 == 1:
            step += 1
        index += step

    if fmt_info is None:
        return None

    fmt_info["has_data_chunk"] = data_chunk_found
    return fmt_info


def validate_audio_prompt_formats():
    """Print warnings for WAV files that are outside preferred playback format."""
    if not audio_word_paths:
        print("WAV format check skipped: no audio prompts loaded")
        return

    warning_count = 0
    for wav_path in audio_word_paths:
        details = inspect_wav_header(wav_path)
        if details is None:
            warning_count += 1
            print("WAV format warning: {} (unreadable or non-standard header)".format(wav_path))
            continue

        is_pcm = details["audio_format"] == 1
        is_mono = details["channels"] == 1
        is_16_bit = details["bits_per_sample"] == 16
        is_target_rate = details["sample_rate"] in WAV_TARGET_SAMPLE_RATES
        has_data = details.get("has_data_chunk", False)

        if not (is_pcm and is_mono and is_16_bit and is_target_rate and has_data):
            warning_count += 1
            print(
                "WAV format warning: {} fmt={} ch={} rate={} bits={} data_chunk={}".format(
                    wav_path,
                    details["audio_format"],
                    details["channels"],
                    details["sample_rate"],
                    details["bits_per_sample"],
                    has_data,
                )
            )

    if warning_count == 0:
        print("WAV format check passed for {} files".format(len(audio_word_paths)))
    else:
        print("WAV format check: {} warning(s) across {} files".format(warning_count, len(audio_word_paths)))


def current_image_answer():
    # During gameplay, use the randomized game_word_list
    if game_active and game_word_list and game_word_index < len(game_word_list):
        image_path = game_word_list[game_word_index]
    elif not keyboard_image_paths:
        return ""
    else:
        image_path = keyboard_image_paths[keyboard_image_index]
    
    image_name = image_path.split("/")[-1]
    dot_index = image_name.rfind(".")
    if dot_index > 0:
        return image_name[:dot_index].lower()
    return image_name.lower()


def current_audio_answer():
    # During gameplay, use the randomized game_word_list
    if game_active and game_word_list and game_word_index < len(game_word_list):
        wav_path = game_word_list[game_word_index]
    elif not audio_word_paths:
        return ""
    else:
        wav_path = audio_word_paths[audio_word_index]
    
    wav_name = wav_path.split("/")[-1]
    dot_index = wav_name.rfind(".")
    if dot_index > 0:
        return wav_name[:dot_index].lower()
    return wav_name.lower()


def current_prompt_answer():
    if current_mode == MODE_AUDIO:
        return current_audio_answer()
    return current_image_answer()


def _append_unique_word(word_list, word_text):
    if not word_text:
        return
    if word_text in word_list:
        return
    word_list.append(word_text)


def _track_wrong_no_hint_word(word_text):
    _append_unique_word(game_wrong_no_hint_words, word_text)


def _track_skipped_word(word_text):
    _append_unique_word(game_skipped_words, word_text)


def _combined_missed_words():
    combined = []
    for word_text in game_wrong_no_hint_words:
        _append_unique_word(combined, word_text)
    for word_text in game_skipped_words:
        _append_unique_word(combined, word_text)
    return combined


def _current_timestamp_tag():
    try:
        now = system_rtc.datetime
    except Exception:
        now = time.localtime()
    return "{:04d}{:02d}{:02d}_{:02d}{:02d}".format(
        now.tm_year,
        now.tm_mon,
        now.tm_mday,
        now.tm_hour,
        now.tm_min,
    )


def _safe_player_file_token(name_text):
    if not name_text:
        return "PLAYER"

    def _is_ascii_alnum(ch):
        code = ord(ch)
        return (48 <= code <= 57) or (65 <= code <= 90) or (97 <= code <= 122)

    cleaned_chars = []
    for ch in name_text:
        if _is_ascii_alnum(ch):
            cleaned_chars.append(ch)
        elif ch in (" ", "-", "_"):
            cleaned_chars.append("_")

    cleaned = "".join(cleaned_chars).strip("_")
    if not cleaned:
        cleaned = "PLAYER"
    return cleaned.upper()


def append_selected_words_debug_log(mode_name, selected_assets):
    global sd_write_faulted

    if not ENABLE_SELECTION_DEBUG_LOG:
        return

    if sd_write_faulted:
        print("Selection log skipped: SD write faulted")
        return

    if mode_name == MODE_AUDIO:
        log_path = AUDIO_SELECTION_LOG_PATH
    else:
        log_path = IMAGE_SELECTION_LOG_PATH

    selected_words = []
    for asset_path in selected_assets:
        selected_words.append(_answer_from_asset_path(asset_path))

    line_text = ",".join(selected_words)

    try:
        with open(log_path, "a") as log_file:
            log_file.write(line_text + "\n")
        print("Selection log appended: {} -> {}".format(log_path, line_text))
    except Exception as exc:
        sd_write_faulted = True
        print("Selection log append failed for {}: {}".format(log_path, exc))


def append_game_score_records():
    global sd_write_faulted

    if sd_write_faulted:
        print("Score writes skipped: SD write faulted")
        return

    timestamp_text = _current_timestamp_tag()
    mode_text = "sound" if startup_selected_mode == MODE_AUDIO else "picture"
    selected_count = startup_selected_word_count

    attempted = game_total - game_skipped
    if attempted < 0:
        attempted = 0

    correct_no_hint = game_correct
    correct_with_hint = game_correct_total - game_correct
    if correct_with_hint < 0:
        correct_with_hint = 0
    total_correct = game_correct_total
    wrong_guess_count = game_total_guesses - total_correct
    if wrong_guess_count < 0:
        wrong_guess_count = 0
    if game_total > 0:
        completion_rate = (total_correct * 100) / game_total
    else:
        completion_rate = 0.0

    round_elapsed_seconds = _finalize_round_elapsed_seconds()
    if attempted > 0:
        seconds_per_word = round_elapsed_seconds / attempted
        guesses_per_word = game_total_guesses / attempted
    else:
        seconds_per_word = 0.0
        guesses_per_word = 0.0

    total_letters = _attempted_total_letters(attempted)
    if total_letters > 0:
        seconds_per_letter = round_elapsed_seconds / total_letters
    else:
        seconds_per_letter = 0.0

    player_text = startup_selected_player if startup_selected_player else "PLAYER"
    shared_line = "{},{},{},{},{},{},{},{:.2f},{},{:.2f},{:.2f},{:.2f},{},{},{},{},{},{:.2f}".format(
        player_text,
        timestamp_text,
        mode_text,
        selected_count,
        attempted,
        correct_no_hint,
        correct_with_hint,
        round_elapsed_seconds,
        game_total_guesses,
        seconds_per_word,
        seconds_per_letter,
        guesses_per_word,
        startup_selected_word_length,
        game_hints_used,
        game_first_try_correct_count,
        total_correct,
        wrong_guess_count,
        completion_rate,
    )

    try:
        with open(SCORES_FILE_PATH, "a") as scores_file:
            scores_file.write(shared_line + "\n")
        print("Score appended: {}".format(shared_line))
    except Exception as exc:
        sd_write_faulted = True
        print("Score append failed for {}: {}".format(SCORES_FILE_PATH, exc))
        return

    missed_words = _combined_missed_words()
    if missed_words:
        missed_text = "|".join(missed_words)
    else:
        missed_text = "-"

    player_file_path = "/sd/{}_scores.txt".format(_safe_player_file_token(player_text))
    player_line = "{},{},{},{},{},{},{:.2f},{},{:.2f},{:.2f},{:.2f},{},{},{},{},{},{:.2f},{},{}".format(
        timestamp_text,
        mode_text,
        selected_count,
        attempted,
        correct_no_hint,
        correct_with_hint,
        round_elapsed_seconds,
        game_total_guesses,
        seconds_per_word,
        seconds_per_letter,
        guesses_per_word,
        startup_selected_word_length,
        game_hints_used,
        game_first_try_correct_count,
        total_correct,
        wrong_guess_count,
        completion_rate,
        len(missed_words),
        missed_text,
    )

    try:
        with open(player_file_path, "a") as player_scores_file:
            player_scores_file.write(player_line + "\n")
        print("Player score appended: {} -> {}".format(player_file_path, player_line))
    except Exception as exc:
        sd_write_faulted = True
        print("Player score append failed for {}: {}".format(player_file_path, exc))


def _round_total_letters():
    total_letters = 0

    for asset_path in game_word_list[:game_total]:
        answer = _answer_from_asset_path(asset_path)
        if answer:
            total_letters += len(answer)

    if total_letters > 0:
        return total_letters

    fallback_length = 0
    try:
        fallback_length = int(startup_selected_word_length)
    except Exception:
        if startup_selected_word_length == "6+":
            fallback_length = 6

    if fallback_length > 0 and game_total > 0:
        return fallback_length * game_total

    return 0


def _attempted_total_letters(attempted_count):
    if attempted_count <= 0:
        return 0

    total_letters = 0
    max_index = min(attempted_count, len(game_word_list))
    for asset_path in game_word_list[:max_index]:
        answer = _answer_from_asset_path(asset_path)
        if answer:
            total_letters += len(answer)

    if total_letters > 0:
        return total_letters

    fallback_length = 0
    try:
        fallback_length = int(startup_selected_word_length)
    except Exception:
        if startup_selected_word_length == "6+":
            fallback_length = 6

    if fallback_length > 0:
        return fallback_length * attempted_count

    return 0


def _safe_float(value_text, default_value=0.0):
    try:
        return float(value_text)
    except Exception:
        return default_value


def _safe_int(value_text, default_value=0):
    try:
        return int(value_text)
    except Exception:
        return default_value


def _compact_score_timestamp(timestamp_text):
    if len(timestamp_text) >= 13 and timestamp_text[8] == "_":
        return "{}-{} {}:{}".format(
            timestamp_text[4:6],
            timestamp_text[6:8],
            timestamp_text[9:11],
            timestamp_text[11:13],
        )
    return timestamp_text


def _load_score_records():
    records = []
    text_data, read_exc = _read_text_with_retry(SCORES_FILE_PATH)
    if read_exc is not None or text_data is None:
        return records

    for line_text in text_data.splitlines():
        row_text = line_text.strip()
        if not row_text:
            continue
        fields = row_text.split(",")
        if len(fields) < 18:
            continue

        player_name = fields[0].strip() if fields[0].strip() else "-"
        timestamp_text = fields[1].strip()
        mode_text = fields[2].strip().lower()
        attempted = _safe_int(fields[4], 0)
        game_total_guesses_rec = _safe_int(fields[8], 0)
        seconds_per_letter = _safe_float(fields[10], 0.0)
        word_length = fields[12].strip()
        first_try_correct = _safe_int(fields[14], 0)

        records.append(
            {
                "player": player_name,
                "timestamp": timestamp_text,
                "mode": mode_text,
                "attempted": attempted,
                "game_total_guesses": game_total_guesses_rec,
                "seconds_per_letter": seconds_per_letter,
                "word_length": word_length,
                "first_try_correct": first_try_correct,
            }
        )

    return records


def _set_summary_rows(label_list, row_texts):
    limit = min(SUMMARY_TOP_COUNT, len(label_list))
    for index in range(limit):
        if index < len(row_texts):
            label_list[index].text = "{:2d}. {}".format(index + 1, row_texts[index])
        else:
            label_list[index].text = "{:2d}. -".format(index + 1)


def refresh_best_seconds_per_letter(mode_text, label_list):
    records = _load_score_records()
    ranked = []

    for record in records:
        if record["mode"] != mode_text:
            continue
        seconds_per_letter = record["seconds_per_letter"]
        if seconds_per_letter <= 0:
            continue
        ranked.append(
            (
                seconds_per_letter,
                "{} {} - {:.2f}s".format(
                    record["player"][:10],
                    _compact_score_timestamp(record["timestamp"]),
                    seconds_per_letter,
                ),
            )
        )

    ranked.sort(key=lambda item: item[0])  # ascending: lower sec/letter = better
    _set_summary_rows(label_list, [item[1] for item in ranked[:SUMMARY_TOP_COUNT]])


def refresh_first_try_summary(label_list):
    records = _load_score_records()
    ranked = []

    for record in records:
        attempted = record["attempted"]
        if attempted <= 0:
            continue
        first_try_pct = (record["first_try_correct"] * 100.0) / attempted
        mode_short = "PIC" if record["mode"] == "picture" else "SND"
        is_sound = record["mode"] == "sound"
        ranked.append(
            (
                first_try_pct,
                "{} {} - {} {:.1f}%".format(
                    record["player"][:8],
                    _compact_score_timestamp(record["timestamp"]),
                    mode_short,
                    first_try_pct,
                ),
                is_sound,
            )
        )

    ranked.sort(key=lambda item: item[0], reverse=True)
    top = ranked[:SUMMARY_TOP_COUNT]
    limit = min(SUMMARY_TOP_COUNT, len(label_list))
    for index in range(limit):
        if index < len(top):
            _, row_text, is_sound = top[index]
            label_list[index].text = "{:2d}. {}".format(index + 1, row_text)
            label_list[index].color = VOWEL_TEXT_COLOR if is_sound else TITLE_TEXT_COLOR
        else:
            label_list[index].text = "{:2d}. -".format(index + 1)
            label_list[index].color = STATUS_TEXT_COLOR


def _fmt_gpw_value(value):
    if value is None:
        return " ---"
    return "{:4.2f}".format(value)


def _fmt_word_count(value):
    return "{:4d}".format(max(0, int(value)))


def _gpw_calc(record_list):
    total_guesses = 0
    total_attempted = 0
    for r in record_list:
        total_guesses += r["game_total_guesses"]
        total_attempted += r["attempted"]
    if total_attempted > 0:
        return total_guesses / total_attempted
    return None


def _attempted_word_count(record_list):
    total_attempted = 0
    for r in record_list:
        total_attempted += r["attempted"]
    return total_attempted


def _today_day_number():
    try:
        now = time.localtime()
        t = time.mktime((now.tm_year, now.tm_mon, now.tm_mday, 0, 0, 0, 0, 0, -1))
        return t // 86400
    except Exception:
        return -1


def _record_day_number(timestamp_text):
    try:
        year = int(timestamp_text[0:4])
        month = int(timestamp_text[4:6])
        day = int(timestamp_text[6:8])
        t = time.mktime((year, month, day, 0, 0, 0, 0, 0, -1))
        return t // 86400
    except Exception:
        return -1


def refresh_gpw_page(player_index):
    global summary_gpw_current_player_index

    if not startup_player_names:
        return

    player_index = max(0, min(player_index, len(startup_player_names) - 1))
    summary_gpw_current_player_index = player_index
    player_name = startup_player_names[player_index]

    if summary_gpw_player_label is not None:
        summary_gpw_player_label.text = "{} ({}/{})".format(
            player_name[:14], player_index + 1, len(startup_player_names)
        )

    if not summary_gpw_row_labels:
        return

    records = _load_score_records()
    player_records = [r for r in records if r["player"] == player_name]

    today_day = _today_day_number()
    if today_day >= 0:
        recent_records = [
            r for r in player_records
            if (today_day - _record_day_number(r["timestamp"])) <= 2
        ]
    else:
        recent_records = []

    summary_gpw_row_labels[0].text = "{:<10} {:>4}  {:>4}".format("", "All", "3Day")
    summary_gpw_row_labels[1].text = "{:<10} {}  {}".format(
        "Overall",
        _fmt_gpw_value(_gpw_calc(player_records)),
        _fmt_gpw_value(_gpw_calc(recent_records)),
    )
    summary_gpw_row_labels[2].text = "{:<10} {}  {}".format(
        "Words",
        _fmt_word_count(_attempted_word_count(player_records)),
        _fmt_word_count(_attempted_word_count(recent_records)),
    )
    for idx, wlen in enumerate(GPW_WORD_LENGTHS):
        all_wl = [r for r in player_records if r["word_length"] == wlen]
        rec_wl = [r for r in recent_records if r["word_length"] == wlen]
        summary_gpw_row_labels[3 + idx].text = "{:<10} {}  {}".format(
            "Len " + wlen,
            _fmt_gpw_value(_gpw_calc(all_wl)),
            _fmt_gpw_value(_gpw_calc(rec_wl)),
        )


def refresh_start_summary_page(page_name):
    _add_summary_pages_if_needed()

    if page_name == SUMMARY_PAGE_LPS_PICTURE:
        refresh_best_seconds_per_letter("picture", summary_lps_picture_labels)
        return
    if page_name == SUMMARY_PAGE_LPS_SOUND:
        refresh_best_seconds_per_letter("sound", summary_lps_sound_labels)
        return
    if page_name == SUMMARY_PAGE_FIRST_TRY:
        refresh_first_try_summary(summary_first_try_labels)
        return
    if page_name == SUMMARY_PAGE_GPW:
        refresh_gpw_page(0)


def _summary_page_next(current_name):
    try:
        current_index = SUMMARY_PAGE_ORDER.index(current_name)
    except Exception:
        return "main"
    return SUMMARY_PAGE_ORDER[(current_index + 1) % len(SUMMARY_PAGE_ORDER)]


def _summary_page_prev(current_name):
    try:
        current_index = SUMMARY_PAGE_ORDER.index(current_name)
    except Exception:
        return "main"
    return SUMMARY_PAGE_ORDER[(current_index - 1) % len(SUMMARY_PAGE_ORDER)]


def _finalize_round_elapsed_seconds():
    global game_round_elapsed_seconds

    if game_round_elapsed_seconds > 0:
        return game_round_elapsed_seconds

    if game_round_start_time is None:
        game_round_elapsed_seconds = 0.0
        return game_round_elapsed_seconds

    elapsed = time.monotonic() - game_round_start_time
    if elapsed < 0:
        elapsed = 0.0
    game_round_elapsed_seconds = elapsed
    return game_round_elapsed_seconds


def update_cumulative_game_stats(round_elapsed_seconds, round_total_guesses):
    if sd_write_faulted:
        print("Cumulative stats update skipped: SD write faulted")
        return

    stats = read_game_stats()

    total_time = 0.0
    try:
        total_time = float(stats.get("total_time", 0.0))
    except Exception:
        total_time = 0.0

    total_guesses = 0
    try:
        total_guesses = int(stats.get("total_guesses", 0))
    except Exception:
        total_guesses = 0

    stats["total_time"] = round(total_time + round_elapsed_seconds, 2)
    stats["total_guesses"] = total_guesses + round_total_guesses

    save_game_stats(stats)


def clear_keyboard_panel_image():
    global keyboard_image_tile, keyboard_image_bitmap, keyboard_image_file

    if keyboard_image_tile is not None and keyboard_page_group is not None:
        try:
            keyboard_page_group.remove(keyboard_image_tile)
        except Exception:
            pass
        keyboard_image_tile = None

    # keyboard_image_file not used anymore (images loaded to memory)
    keyboard_image_file = None
    keyboard_image_bitmap = None


def resolve_audio_mode_image_path():
    for candidate_path in AUDIOMODE_IMAGE_CANDIDATES:
        file_handle = None
        try:
            file_handle = open(candidate_path, "rb")
            return candidate_path
        except Exception:
            pass
        finally:
            if file_handle is not None:
                try:
                    file_handle.close()
                except Exception:
                    pass
    return None


def resolve_picture_mode_idle_image_path():
    for candidate_path in PICTUREMODE_IDLE_IMAGE_CANDIDATES:
        file_handle = None
        try:
            file_handle = open(candidate_path, "rb")
            return candidate_path
        except Exception:
            pass
        finally:
            if file_handle is not None:
                try:
                    file_handle.close()
                except Exception:
                    pass
    return None


def update_keyboard_panel_image():
    global keyboard_image_tile, keyboard_image_bitmap, keyboard_image_file
    global audio_mode_bitmap_cache, audio_mode_palette_cache, audio_mode_image_path_cache

    if keyboard_page_group is None:
        return False

    if current_mode == MODE_AUDIO:
        clear_keyboard_panel_image()
        if audio_mode_bitmap_cache is None or audio_mode_palette_cache is None:
            audio_mode_image_path = resolve_audio_mode_image_path()
            if audio_mode_image_path is None:
                print("Audio mode image not found (tried: {})".format(AUDIOMODE_IMAGE_CANDIDATES))
                return False

            try:
                with open(audio_mode_image_path, "rb") as f:
                    audio_mode_bitmap_cache, audio_mode_palette_cache = adafruit_imageload.load(f)
                audio_mode_image_path_cache = audio_mode_image_path
                print("Audio mode image cached: {}".format(audio_mode_image_path))
            except Exception as exc:
                print("Audio mode image load failed for {}: {}".format(audio_mode_image_path, exc))
                audio_mode_bitmap_cache = None
                audio_mode_palette_cache = None
                audio_mode_image_path_cache = None
                clear_keyboard_panel_image()
                return False

        keyboard_image_bitmap = audio_mode_bitmap_cache
        keyboard_image_tile = displayio.TileGrid(
            audio_mode_bitmap_cache,
            pixel_shader=audio_mode_palette_cache,
            x=IMAGE_PANEL_X,
            y=IMAGE_PANEL_Y,
        )
        keyboard_page_group.append(keyboard_image_tile)
        return True

    if game_active:
        if not game_word_list or game_word_index >= len(game_word_list):
            clear_keyboard_panel_image()
            return False
        clear_keyboard_panel_image()
        image_path = game_word_list[game_word_index]
    else:
        clear_keyboard_panel_image()
        image_path = resolve_picture_mode_idle_image_path()
        if image_path is None:
            if not keyboard_image_paths:
                return False
            image_path = keyboard_image_paths[keyboard_image_index]
    try:
        with open(image_path, "rb") as f:
            keyboard_image_bitmap, keyboard_image_palette = adafruit_imageload.load(f)
        keyboard_image_tile = displayio.TileGrid(
            keyboard_image_bitmap,
            pixel_shader=keyboard_image_palette,
            x=IMAGE_PANEL_X,
            y=IMAGE_PANEL_Y,
        )
        keyboard_page_group.append(keyboard_image_tile)
        print("Keyboard panel image loaded: {}".format(image_path))
        return True
    except Exception as exc:
        print("Keyboard panel image load failed for {}: {}".format(image_path, exc))
        return False


def cycle_keyboard_panel_image():
    global keyboard_image_index

    if current_mode == MODE_AUDIO:
        return cycle_audio_prompt()

    # During gameplay, advance to next word instead of cycling through all images
    if game_active:
        advance_to_next_word()
        return True

    if not keyboard_image_paths:
        return False

    keyboard_image_index = (keyboard_image_index + 1) % len(keyboard_image_paths)
    clear_answer_text()
    clear_last_answer_label()
    return update_keyboard_panel_image()


def cycle_audio_prompt():
    global audio_word_index

    # During gameplay, advance to next word instead of cycling through all audio
    if game_active:
        advance_to_next_word()
        return True

    if not audio_word_paths:
        return False

    audio_word_index = (audio_word_index + 1) % len(audio_word_paths)
    clear_answer_text()
    clear_last_answer_label()
    return update_keyboard_panel_image()


def set_game_mode(mode_name):
    global current_mode

    current_mode = mode_name
    clear_answer_text()
    update_keyboard_mode_label()
    update_keyboard_panel_image()
    update_status_line(force=True)
    print("Game mode set to {}".format(mode_name))
    return True


def add_background(group):
    background_bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 1)
    background_palette = displayio.Palette(1)
    background_palette[0] = BG_COLOR
    group.append(displayio.TileGrid(background_bitmap, pixel_shader=background_palette, x=0, y=0))


def add_button(
    group,
    page_name,
    x,
    y,
    w,
    h,
    text,
    name,
    role,
    font_key="small_button",
    fill_color=BUTTON_FILL_COLOR,
    text_color=BUTTON_TEXT_COLOR,
):
    button_bitmap = displayio.Bitmap(w, h, 1)
    button_palette = displayio.Palette(1)
    button_palette[0] = fill_color
    button_tile = displayio.TileGrid(button_bitmap, pixel_shader=button_palette, x=x, y=y)
    group.append(button_tile)

    button_label = label.Label(FONTS[font_key], text=text, color=text_color)
    button_label.anchor_point = (0.5, 0.5)
    button_label.anchored_position = (x + (w // 2), y + (h // 2) + 1)
    group.append(button_label)

    button_info = {
        "page": page_name,
        "name": name,
        "role": role,
        "text": text,
        "visible": True,
        "active": True,
        "tile": button_tile,
        "label": button_label,
        "x0": x,
        "x1": x + w,
        "y0": y,
        "y1": y + h,
    }
    BUTTON_REGISTRY.append(button_info)
    if page_name in SUMMARY_DYNAMIC_PAGES:
        summary_registered_buttons.append(button_info)
    return button_info


def add_shared_page_chrome(page_group, page_name):
    add_button(
        page_group,
        page_name,
        FLOW_BUTTON_MARGIN,
        FLOW_BUTTON_MARGIN,
        FLOW_BUTTON_WIDTH,
        FLOW_BUTTON_HEIGHT,
        "BACK",
        "{}_back".format(page_name),
        "flow_back",
    )
    add_button(
        page_group,
        page_name,
        DISPLAY_WIDTH - FLOW_BUTTON_MARGIN - FLOW_BUTTON_WIDTH,
        FLOW_BUTTON_MARGIN,
        FLOW_BUTTON_WIDTH,
        FLOW_BUTTON_HEIGHT,
        "NEXT",
        "{}_next".format(page_name),
        "flow_next",
    )

    status_line = label.Label(
        FONTS["score"],
        text=build_status_line_text(),
        color=STATUS_TEXT_COLOR,
    )
    status_line.anchor_point = (0.5, 1.0)
    status_line.anchored_position = (DISPLAY_WIDTH // 2, STATUS_LINE_Y)
    page_group.append(status_line)
    STATUS_LINE_LABELS.append(status_line)
    if page_name in SUMMARY_DYNAMIC_PAGES:
        summary_registered_status_labels.append(status_line)


def build_main_page():
    global startup_title_label, startup_prompt_label, startup_summary_label, startup_error_label
    global startup_start_button, startup_option_buttons

    page = displayio.Group()
    add_background(page)
    add_shared_page_chrome(page, "main")

    # Add dark background panel for the image placeholder (same as on the keyboard page)
    panel_bitmap = displayio.Bitmap(IMAGE_PANEL_SIZE, IMAGE_PANEL_SIZE, 1)
    panel_palette = displayio.Palette(1)
    panel_palette[0] = DARK_PANEL_COLOR
    page.append(displayio.TileGrid(panel_bitmap, pixel_shader=panel_palette, x=IMAGE_PANEL_X, y=IMAGE_PANEL_Y))

    startup_image_path = resolve_picture_mode_idle_image_path()
    if startup_image_path is not None:
        try:
            with open(startup_image_path, "rb") as f:
                startup_bitmap, startup_palette = adafruit_imageload.load(f)
            startup_tile = displayio.TileGrid(
                startup_bitmap,
                pixel_shader=startup_palette,
                x=IMAGE_PANEL_X,
                y=IMAGE_PANEL_Y,
            )
            page.append(startup_tile)
        except Exception as exc:
            print("Failed to load startup image {}: {}".format(startup_image_path, exc))

    startup_title_label = label.Label(FONTS["title"], text="Spell Game", color=TITLE_TEXT_COLOR)
    startup_title_label.anchor_point = (0.5, 0.5)
    startup_title_label.anchored_position = (DISPLAY_WIDTH // 2, 300)
    page.append(startup_title_label)

    startup_prompt_label = label.Label(FONTS["button"], text="Press START", color=TITLE_TEXT_COLOR)
    startup_prompt_label.anchor_point = (0.5, 0.5)
    startup_prompt_label.anchored_position = (DISPLAY_WIDTH // 2, 148)
    page.append(startup_prompt_label)

    startup_summary_label = label.Label(FONTS["score"], text="- | PIC | RAND | 10", color=STATUS_TEXT_COLOR)
    startup_summary_label.anchor_point = (0.5, 0.5)
    startup_summary_label.anchored_position = (DISPLAY_WIDTH // 2, 182)
    page.append(startup_summary_label)

    startup_error_label = label.Label(FONTS["small_button"], text="", color=WRONG_ANSWER_COLOR)
    startup_error_label.anchor_point = (0.5, 0.5)
    startup_error_label.anchored_position = (DISPLAY_WIDTH // 2, 118)
    page.append(startup_error_label)

    startup_start_button = add_button(
        page,
        "main",
        (DISPLAY_WIDTH - 132) // 2,
        222,
        132,
        48,
        "START",
        "main_start",
        "startup_begin",
        font_key="button",
        fill_color=MATH_GAME_GREEN,
    )

    startup_option_buttons = []
    startup_option_buttons.append(
        add_button(
            page,
            "main",
            START_ACTION_LEFT_X,
            START_ACTIONS_TOP_Y,
            START_ACTION_BUTTON_WIDTH,
            START_ACTION_BUTTON_HEIGHT,
            "",
            "main_start_opt_0",
            "startup_opt_0",
            font_key="small_button",
            fill_color=0x2F3A44,
        )
    )
    startup_option_buttons.append(
        add_button(
            page,
            "main",
            START_ACTION_RIGHT_X,
            START_ACTIONS_TOP_Y,
            START_ACTION_BUTTON_WIDTH,
            START_ACTION_BUTTON_HEIGHT,
            "",
            "main_start_opt_1",
            "startup_opt_1",
            font_key="small_button",
            fill_color=0x2F3A44,
        )
    )
    startup_option_buttons.append(
        add_button(
            page,
            "main",
            START_ACTION_LEFT_X,
            START_ACTION_BOTTOM_Y,
            START_ACTION_BUTTON_WIDTH,
            START_ACTION_BUTTON_HEIGHT,
            "",
            "main_start_opt_2",
            "startup_opt_2",
            font_key="small_button",
            fill_color=0x2F3A44,
        )
    )
    startup_option_buttons.append(
        add_button(
            page,
            "main",
            START_ACTION_RIGHT_X,
            START_ACTION_BOTTOM_Y,
            START_ACTION_BUTTON_WIDTH,
            START_ACTION_BUTTON_HEIGHT,
            "",
            "main_start_opt_3",
            "startup_opt_3",
            font_key="small_button",
            fill_color=0x2F3A44,
        )
    )

    update_startup_ui()
    return page


def build_keyboard_page():
    global answer_display_label, keyboard_page_group, keyboard_mode_label, keyboard_answer_button

    page = displayio.Group()
    keyboard_page_group = page
    add_background(page)
    add_shared_page_chrome(page, "keyboard")

    keyboard_mode_label = label.Label(FONTS["score"], text="", color=WRONG_ANSWER_COLOR)
    keyboard_mode_label.anchor_point = (0.5, 0.5)
    keyboard_mode_label.anchored_position = (DISPLAY_WIDTH // 2, 162)
    page.append(keyboard_mode_label)

    add_button(
        page,
        "keyboard",
        FLOW_BUTTON_MARGIN,
        58,
        88,
        34,
        "REPLAY",
        "keyboard_replay",
        "audio_replay",
        font_key="small_button",
    )

    keyboard_answer_button = add_button(
        page,
        "keyboard",
        DISPLAY_WIDTH - FLOW_BUTTON_MARGIN - 88,
        58,
        88,
        34,
        "ANSWER",
        "keyboard_answer",
        "show_answer",
        font_key="small_button",
        fill_color=0x1A6B3A,
    )
    _set_keyboard_answer_button_visible(False)

    answer_display_label = label.Label(FONTS["button"], text="_", color=TITLE_TEXT_COLOR)
    answer_display_label.anchor_point = (0.5, 0.5)
    answer_display_label.anchored_position = (DISPLAY_WIDTH // 2, 142)
    page.append(answer_display_label)

    panel_bitmap = displayio.Bitmap(IMAGE_PANEL_SIZE, IMAGE_PANEL_SIZE, 1)
    panel_palette = displayio.Palette(1)
    panel_palette[0] = DARK_PANEL_COLOR
    page.append(displayio.TileGrid(panel_bitmap, pixel_shader=panel_palette, x=IMAGE_PANEL_X, y=IMAGE_PANEL_Y))
    update_keyboard_panel_image()

    keyboard_rows = (
        ("BkSp", "A", "B", "C"),
        ("D", "E", "F", "G"),
        ("H", "I", "J", "K"),
        ("L", "M", "N", "O"),
        ("P", "Q", "R", "S"),
        ("T", "U", "V", "W"),
        ("X", "Y", "Z", "ENTER"),
    )

    for row in range(KEYBOARD_ROWS):
        for col in range(KEYBOARD_COLS):
            key_text = keyboard_rows[row][col]
            key_color = KEY_ROW_COLOR_DARK if (row % 2 == 0) else KEY_ROW_COLOR_LIGHT
            key_text_color = BUTTON_TEXT_COLOR
            if key_text in ("A", "E", "I", "O", "U"):
                key_text_color = VOWEL_TEXT_COLOR
            if key_text == "BkSp":
                key_color = 0xC9B000
            elif key_text == "ENTER":
                key_color = 0x00A84F
            key_x = KEYBOARD_START_X + (col * (KEY_WIDTH + KEY_GAP))
            key_y = KEYBOARD_START_Y + (row * (KEY_HEIGHT + KEY_GAP))
            add_button(
                page,
                "keyboard",
                key_x,
                key_y,
                KEY_WIDTH,
                KEY_HEIGHT,
                key_text,
                "key_{}_{}".format(row, col),
                "kb_key",
                font_key="small_button",
                fill_color=key_color,
                text_color=key_text_color,
            )

    return page


def build_name_entry_page():
    global name_entry_text_label, name_entry_page_label, name_entry_dynamic_buttons

    page = displayio.Group()
    add_background(page)
    add_shared_page_chrome(page, "name_entry")

    header = label.Label(FONTS["button"], text="New Player Name", color=TITLE_TEXT_COLOR)
    header.anchor_point = (0.5, 0.5)
    header.anchored_position = (DISPLAY_WIDTH // 2, 98)
    page.append(header)

    name_entry_text_label = label.Label(FONTS["button"], text="_", color=VOWEL_TEXT_COLOR)
    name_entry_text_label.anchor_point = (0.5, 0.5)
    name_entry_text_label.anchored_position = (DISPLAY_WIDTH // 2, 132)
    page.append(name_entry_text_label)

    name_entry_page_label = label.Label(FONTS["score"], text="Page 1/3", color=STATUS_TEXT_COLOR)
    name_entry_page_label.anchor_point = (0.5, 0.5)
    name_entry_page_label.anchored_position = (DISPLAY_WIDTH // 2, 162)
    page.append(name_entry_page_label)

    fixed_rows = (
        ("PREV", "name_entry_prev", "ne_prev", MATH_GAME_ORANGE),
        ("NEXT", "name_entry_next", "ne_next", MATH_GAME_ORANGE),
        ("BKSP", "name_entry_bksp", "ne_bksp", MATH_GAME_RED),
        ("DONE", "name_entry_done", "ne_done", MATH_GAME_GREEN),
        ("A", "name_entry_a", "ne_char", MATH_GAME_GOLD),
        ("E", "name_entry_e", "ne_char", MATH_GAME_GOLD),
        ("I", "name_entry_i", "ne_char", MATH_GAME_GOLD),
        ("O", "name_entry_o", "ne_char", MATH_GAME_GOLD),
    )

    for idx, fixed_def in enumerate(fixed_rows):
        key_text, key_name, key_role, key_color = fixed_def
        row = idx // NAME_ENTRY_COLS
        col = idx % NAME_ENTRY_COLS
        key_x = NAME_ENTRY_START_X + (col * (NAME_ENTRY_KEY_WIDTH + NAME_ENTRY_KEY_GAP))
        key_y = NAME_ENTRY_START_Y + (row * (NAME_ENTRY_KEY_HEIGHT + NAME_ENTRY_KEY_GAP))
        add_button(
            page,
            "name_entry",
            key_x,
            key_y,
            NAME_ENTRY_KEY_WIDTH,
            NAME_ENTRY_KEY_HEIGHT,
            key_text,
            key_name,
            key_role,
            font_key="small_button",
            fill_color=key_color,
            text_color=BUTTON_TEXT_COLOR,
        )

    name_entry_dynamic_buttons = []
    for idx in range(8):
        row = 2 + (idx // NAME_ENTRY_COLS)
        col = idx % NAME_ENTRY_COLS
        key_x = NAME_ENTRY_START_X + (col * (NAME_ENTRY_KEY_WIDTH + NAME_ENTRY_KEY_GAP))
        key_y = NAME_ENTRY_START_Y + (row * (NAME_ENTRY_KEY_HEIGHT + NAME_ENTRY_KEY_GAP))
        button_info = add_button(
            page,
            "name_entry",
            key_x,
            key_y,
            NAME_ENTRY_KEY_WIDTH,
            NAME_ENTRY_KEY_HEIGHT,
            "",
            "name_entry_dyn_{}".format(idx),
            "ne_dynamic",
            font_key="small_button",
            fill_color=0x2F3A44,
            text_color=BUTTON_TEXT_COLOR,
        )
        name_entry_dynamic_buttons.append(button_info)

    update_name_entry_keyboard_ui()
    return page


def build_scores_page():
    global results_player_label, results_total_label, results_attempted_label
    global results_correct_no_hint_label, results_correct_with_hint_label, results_percent_no_hint_label
    global results_time_label, results_guesses_label

    page = displayio.Group()
    add_background(page)
    add_shared_page_chrome(page, "scores")

    header = label.Label(FONTS["button"], text="Scores", color=TITLE_TEXT_COLOR)
    header.anchor_point = (0.5, 0.5)
    header.anchored_position = (DISPLAY_WIDTH // 2, 95)
    page.append(header)

    results_player_label = label.Label(FONTS["score"], text="Player: -", color=STATUS_TEXT_COLOR)
    results_player_label.anchor_point = (0.0, 0.5)
    results_player_label.anchored_position = (24, 132)
    page.append(results_player_label)

    results_total_label = label.Label(FONTS["score"], text="Total Problems: 0", color=STATUS_TEXT_COLOR)
    results_total_label.anchor_point = (0.0, 0.5)
    results_total_label.anchored_position = (24, 160)
    page.append(results_total_label)

    results_attempted_label = label.Label(FONTS["score"], text="Attempted: 0", color=STATUS_TEXT_COLOR)
    results_attempted_label.anchor_point = (0.0, 0.5)
    results_attempted_label.anchored_position = (24, 188)
    page.append(results_attempted_label)

    results_correct_no_hint_label = label.Label(FONTS["score"], text="Correct (No Hint): 0", color=STATUS_TEXT_COLOR)
    results_correct_no_hint_label.anchor_point = (0.0, 0.5)
    results_correct_no_hint_label.anchored_position = (24, 216)
    page.append(results_correct_no_hint_label)

    results_correct_with_hint_label = label.Label(FONTS["score"], text="Correct (With Hint): 0", color=STATUS_TEXT_COLOR)
    results_correct_with_hint_label.anchor_point = (0.0, 0.5)
    results_correct_with_hint_label.anchored_position = (24, 244)
    page.append(results_correct_with_hint_label)

    results_percent_no_hint_label = label.Label(FONTS["score"], text="% No Hint: 0%", color=VOWEL_TEXT_COLOR)
    results_percent_no_hint_label.anchor_point = (0.0, 0.5)
    results_percent_no_hint_label.anchored_position = (24, 272)
    page.append(results_percent_no_hint_label)

    results_time_label = label.Label(FONTS["score"], text="Time (W/L): 0.00 / 0.00", color=STATUS_TEXT_COLOR)
    results_time_label.anchor_point = (0.0, 0.5)
    results_time_label.anchored_position = (24, 300)
    page.append(results_time_label)

    results_guesses_label = label.Label(FONTS["score"], text="Guesses/Word: 0.00", color=STATUS_TEXT_COLOR)
    results_guesses_label.anchor_point = (0.0, 0.5)
    results_guesses_label.anchored_position = (24, 328)
    page.append(results_guesses_label)

    return page


def _build_summary_page_rows(page, page_name):
    rows = []
    for row_index in range(SUMMARY_TOP_COUNT):
        row_label = label.Label(FONTS["small_button"], text="{:2d}. -".format(row_index + 1), color=STATUS_TEXT_COLOR)
        row_label.anchor_point = (0.0, 0.5)
        row_label.anchored_position = (12, 124 + (row_index * 30))
        page.append(row_label)
        rows.append(row_label)
    return rows


def _add_summary_pages_if_needed():
    global summary_pages_initialized

    if not summary_pages_initialized:
        summary_pages_initialized = all(page_group is not None for page_group in _summary_groups())

    if not summary_pages_initialized:
        return

    if not _summary_pages_have_content():
        _rebuild_summary_pages_in_place()


def _summary_groups():
    return (
        summary_lps_picture_page_group,
        summary_lps_sound_page_group,
        summary_first_try_page_group,
        summary_gpw_page_group,
    )


def _summary_pages_have_content():
    for page_group in _summary_groups():
        if page_group is not None and len(page_group) > 0:
            return True
    return False


def _clear_group_children(page_group):
    if page_group is None:
        return
    while len(page_group) > 0:
        page_group.pop()


def _rebuild_summary_pages_in_place():
    _clear_group_children(summary_lps_picture_page_group)
    _clear_group_children(summary_lps_sound_page_group)
    _clear_group_children(summary_first_try_page_group)
    _clear_group_children(summary_gpw_page_group)

    _populate_summary_lps_picture_page(summary_lps_picture_page_group)
    _populate_summary_lps_sound_page(summary_lps_sound_page_group)
    _populate_summary_first_try_page(summary_first_try_page_group)
    _populate_summary_gpw_page(summary_gpw_page_group)
    gc.collect()
    print("Summary pages rebuilt in place ({})".format(_gameplay_memory_text()))


def _unload_summary_pages():
    global summary_lps_picture_labels, summary_lps_sound_labels, summary_first_try_labels
    global summary_gpw_player_label, summary_gpw_row_labels
    global summary_registered_buttons, summary_registered_status_labels, summary_pages_initialized

    if not summary_pages_initialized:
        summary_pages_initialized = all(page_group is not None for page_group in _summary_groups())

    if not summary_pages_initialized:
        return
    if not _summary_pages_have_content():
        return

    _clear_group_children(summary_lps_picture_page_group)
    _clear_group_children(summary_lps_sound_page_group)
    _clear_group_children(summary_first_try_page_group)
    _clear_group_children(summary_gpw_page_group)

    if summary_registered_buttons:
        for button_info in summary_registered_buttons:
            if button_info in BUTTON_REGISTRY:
                BUTTON_REGISTRY.remove(button_info)
    if summary_registered_status_labels:
        for status_label in summary_registered_status_labels:
            if status_label in STATUS_LINE_LABELS:
                STATUS_LINE_LABELS.remove(status_label)
    summary_registered_buttons = []
    summary_registered_status_labels = []

    summary_lps_picture_labels = []
    summary_lps_sound_labels = []
    summary_first_try_labels = []
    summary_gpw_player_label = None
    summary_gpw_row_labels = []
    gc.collect()
    print("Summary pages unloaded")


def _populate_summary_lps_picture_page(page_group):
    global summary_lps_picture_labels

    add_background(page_group)
    add_shared_page_chrome(page_group, SUMMARY_PAGE_LPS_PICTURE)

    header = label.Label(FONTS["button"], text="Best Sec/Ltr - Pic", color=TITLE_TEXT_COLOR)
    header.anchor_point = (0.5, 0.5)
    header.anchored_position = (DISPLAY_WIDTH // 2, 95)
    page_group.append(header)

    summary_lps_picture_labels = _build_summary_page_rows(page_group, SUMMARY_PAGE_LPS_PICTURE)


def _populate_summary_lps_sound_page(page_group):
    global summary_lps_sound_labels

    add_background(page_group)
    add_shared_page_chrome(page_group, SUMMARY_PAGE_LPS_SOUND)

    header = label.Label(FONTS["button"], text="Best Sec/Ltr - Snd", color=TITLE_TEXT_COLOR)
    header.anchor_point = (0.5, 0.5)
    header.anchored_position = (DISPLAY_WIDTH // 2, 95)
    page_group.append(header)

    summary_lps_sound_labels = _build_summary_page_rows(page_group, SUMMARY_PAGE_LPS_SOUND)


def _populate_summary_first_try_page(page_group):
    global summary_first_try_labels

    add_background(page_group)
    add_shared_page_chrome(page_group, SUMMARY_PAGE_FIRST_TRY)

    header = label.Label(FONTS["button"], text="Top First Try %", color=TITLE_TEXT_COLOR)
    header.anchor_point = (0.5, 0.5)
    header.anchored_position = (DISPLAY_WIDTH // 2, 95)
    page_group.append(header)

    summary_first_try_labels = _build_summary_page_rows(page_group, SUMMARY_PAGE_FIRST_TRY)


def _populate_summary_gpw_page(page_group):
    global summary_gpw_player_label, summary_gpw_row_labels

    add_background(page_group)
    add_shared_page_chrome(page_group, SUMMARY_PAGE_GPW)

    title_lbl = label.Label(FONTS["button"], text="Guesses Per Word", color=TITLE_TEXT_COLOR)
    title_lbl.anchor_point = (0.5, 0.5)
    title_lbl.anchored_position = (DISPLAY_WIDTH // 2, 55)
    page_group.append(title_lbl)

    summary_gpw_player_label = label.Label(FONTS["score"], text="---", color=STATUS_TEXT_COLOR)
    summary_gpw_player_label.anchor_point = (0.5, 0.5)
    summary_gpw_player_label.anchored_position = (DISPLAY_WIDTH // 2, 82)
    page_group.append(summary_gpw_player_label)

    row_y_positions = (104, 128, 152, 176, 200, 224, 248, 272)
    summary_gpw_row_labels = []
    for row_y in row_y_positions:
        row_lbl = label.Label(FONTS["small_button"], text="-", color=STATUS_TEXT_COLOR)
        row_lbl.anchor_point = (0.0, 0.5)
        row_lbl.anchored_position = (12, row_y)
        page_group.append(row_lbl)
        summary_gpw_row_labels.append(row_lbl)


def build_summary_lps_picture_page():
    global summary_lps_picture_page_group

    page = displayio.Group()
    summary_lps_picture_page_group = page
    _populate_summary_lps_picture_page(page)
    return page


def build_summary_lps_sound_page():
    global summary_lps_sound_page_group

    page = displayio.Group()
    summary_lps_sound_page_group = page
    _populate_summary_lps_sound_page(page)
    return page


def build_summary_first_try_page():
    global summary_first_try_page_group

    page = displayio.Group()
    summary_first_try_page_group = page
    _populate_summary_first_try_page(page)
    return page


def build_summary_gpw_page():
    global summary_gpw_page_group

    page = displayio.Group()
    summary_gpw_page_group = page
    _populate_summary_gpw_page(page)
    return page


def show_results_page():
    append_game_score_records()

    round_elapsed_seconds = _finalize_round_elapsed_seconds()
    update_cumulative_game_stats(round_elapsed_seconds, game_total_guesses)

    attempted = game_total - game_skipped
    if attempted < 0:
        attempted = 0

    correct_no_hint = game_correct
    correct_with_hint = game_correct_total - game_correct
    if correct_with_hint < 0:
        correct_with_hint = 0

    if attempted > 0:
        # Requested formula: (attempted - hints) / attempted
        raw_percent_no_hint = ((attempted - game_hints_used) * 100) / attempted
        if raw_percent_no_hint < 0:
            raw_percent_no_hint = 0
    else:
        raw_percent_no_hint = 0

    if attempted > 0:
        seconds_per_word = round_elapsed_seconds / attempted
        guesses_per_word = game_total_guesses / attempted
    else:
        seconds_per_word = 0.0
        guesses_per_word = 0.0

    total_letters = _attempted_total_letters(attempted)
    if total_letters > 0:
        seconds_per_letter = round_elapsed_seconds / total_letters
    else:
        seconds_per_letter = 0.0

    if results_player_label is not None:
        results_player_label.text = "Player: {}".format(startup_selected_player if startup_selected_player else "-")
    if results_total_label is not None:
        results_total_label.text = "Total Problems: {}".format(game_total)
    if results_attempted_label is not None:
        results_attempted_label.text = "Attempted: {}".format(attempted)
    if results_correct_no_hint_label is not None:
        results_correct_no_hint_label.text = "Correct (No Hint): {}".format(correct_no_hint)
    if results_correct_with_hint_label is not None:
        results_correct_with_hint_label.text = "Correct (With Hint): {}".format(correct_with_hint)
    if results_percent_no_hint_label is not None:
        results_percent_no_hint_label.text = "% No Hint: {:.1f}%".format(raw_percent_no_hint)
    if results_time_label is not None:
        results_time_label.text = "Time (W/L): {:.2f} / {:.2f}".format(seconds_per_word, seconds_per_letter)
    if results_guesses_label is not None:
        results_guesses_label.text = "Guesses/Word: {:.2f}".format(guesses_per_word)

    _set_page_flow_back_button_text("scores", "HOME", MATH_GAME_ORANGE)
    _set_page_flow_back_button_text("keyboard", "BACK", BUTTON_FILL_COLOR)
    show_page("scores")


def init_display(spi):
    return circuitpython_st7796s.ST7796S(
        fourwire.FourWire(
            spi,
            command=TFT_DC,
            chip_select=TFT_CS,
            reset=TFT_RST,
            baudrate=DISPLAY_SPI_BAUDRATE,
        ),
        width=DISPLAY_WIDTH,
        height=DISPLAY_HEIGHT,
        rotation=DISPLAY_ROTATION,
    )

def init_touch(spi):
    touch_width = DISPLAY_HEIGHT if TOUCH_SWAP_XY else DISPLAY_WIDTH
    touch_height = DISPLAY_WIDTH if TOUCH_SWAP_XY else DISPLAY_HEIGHT
    touch_cs = digitalio.DigitalInOut(TOUCH_CS)
    return xpt2046_circuitpython.Touch(
        spi,
        cs=touch_cs,
        width=touch_width,
        height=touch_height,
        x_min=166,
        x_max=1960,
        y_min=162,
        y_max=1974,
        force_baudrate=100000,
    )


def init_sd_card(spi, mount_point="/sd"):
    global sd_card, sd_vfs

    def _release_sd_card_resources():
        global sd_card, sd_vfs

        try:
            if sd_vfs is not None:
                storage.umount(mount_point)
        except Exception:
            pass

        try:
            if sd_card is not None and hasattr(sd_card, "deinit"):
                sd_card.deinit()
        except Exception:
            pass

        sd_card = None
        sd_vfs = None
        gc.collect()

    for attempt in range(1, 4):
        _release_sd_card_resources()
        try:
            sd_card = sdcardio.SDCard(spi, SD_CS)
            sd_vfs = storage.VfsFat(sd_card)
            storage.mount(sd_vfs, mount_point)
            print("SD card mounted at {}".format(mount_point))
            return True
        except Exception as exc:
            _release_sd_card_resources()
            print("SD init attempt {} failed: {}".format(attempt, exc))
            time.sleep(0.15)

    print("SD card init failed after retries.")
    return False


def read_game_stats():
    if sd_write_faulted:
        return dict(DEFAULT_STATS)

    try:
        with open(STATS_FILE_PATH, "r") as stats_file:
            return json.loads(stats_file.read())
    except Exception:
        return dict(DEFAULT_STATS)


def save_game_stats(stats):
    global sd_write_faulted

    if sd_write_faulted:
        print("Stats save skipped: SD write faulted")
        return False

    try:
        with open(STATS_FILE_PATH, "w") as stats_file:
            stats_file.write(json.dumps(stats))
        print("Stats saved: {}".format(stats))
        return True
    except Exception as exc:
        sd_write_faulted = True
        print("Stats save failed: {}".format(exc))
        return False


def append_line_to_test_file(line_text):
    print("Attempting to append to {}: {}".format(TEST_FILE_PATH, line_text))
    if not line_text:
        return False

    try:
        with open(TEST_FILE_PATH, "a") as test_file:
            test_file.write(line_text + "\n")
        print("Appended to {}: {}".format(TEST_FILE_PATH, line_text))
        return True
    except Exception as exc:
        print("Write to {} failed: {}".format(TEST_FILE_PATH, exc))
        return False


def map_touch_to_screen(point):
    x, y = point
    if TOUCH_SWAP_XY:
        x, y = y, x

    if TOUCH_INVERT_X:
        x = (DISPLAY_WIDTH - 1) - x
    if TOUCH_INVERT_Y:
        y = (DISPLAY_HEIGHT - 1) - y

    if x < 0:
        x = 0
    elif x >= DISPLAY_WIDTH:
        x = DISPLAY_WIDTH - 1

    if y < 0:
        y = 0
    elif y >= DISPLAY_HEIGHT:
        y = DISPLAY_HEIGHT - 1

    return x, y


def button_from_touch(x, y):
    for button in BUTTON_REGISTRY:
        if button["page"] != current_page_name:
            continue
        if not button.get("active", True):
            continue
        if not button.get("visible", True):
            continue
        if button["x0"] <= x < button["x1"] and button["y0"] <= y < button["y1"]:
            return button
    return None


def show_page(page_name):
    global current_page_name

    if page_name in SUMMARY_PAGE_ORDER and page_name != "main":
        _add_summary_pages_if_needed()

    pages.show_page(page_name)
    current_page_name = page_name


def handle_button_press(button):
    global answer_display_text, startup_player_page, startup_step, startup_new_player_text
    global game_active, game_word_index, game_total, game_correct, game_correct_total, game_current_word_wrong_attempts
    global game_total_guesses, game_first_try_correct_count

    play_button_feedback()

    if button["role"] == "startup_begin" and current_page_name == "main":
        begin_startup_flow()
        return

    if button["role"].startswith("startup_opt_") and current_page_name == "main":
        slot_text = button["role"].split("_")[-1]
        try:
            slot_index = int(slot_text)
        except Exception:
            slot_index = -1
        handle_startup_option(slot_index)
        return

    if button["role"] == "flow_next" and current_page_name == "main":
        if startup_step == STARTUP_STEP_READY:
            next_page = _summary_page_next("main")
            refresh_start_summary_page(next_page)
            show_page(next_page)
            update_status_line(force=True)
            return
        if startup_step == STARTUP_STEP_PLAYER:
            max_page = (len(startup_player_names) - 1) // 3
            if startup_player_page < max_page:
                startup_player_page += 1
                update_startup_ui()
        return

    if button["role"] == "flow_back" and current_page_name == "main":
        if startup_step == STARTUP_STEP_PLAYER:
            if startup_player_page > 0:
                startup_player_page -= 1
                update_startup_ui()
            else:
                _goto_previous_startup_step()
        elif startup_step != STARTUP_STEP_READY:
            _goto_previous_startup_step()
        return

    if button["role"] == "flow_next" and current_page_name == SUMMARY_PAGE_GPW:
        next_player = summary_gpw_current_player_index + 1
        if next_player < len(startup_player_names):
            refresh_gpw_page(next_player)
        else:
            next_page = _summary_page_next(SUMMARY_PAGE_GPW)
            if next_page != "main":
                refresh_start_summary_page(next_page)
            show_page(next_page)
            if next_page == "main":
                update_startup_ui()
        update_status_line(force=True)
        return

    if button["role"] == "flow_back" and current_page_name == SUMMARY_PAGE_GPW:
        prev_player = summary_gpw_current_player_index - 1
        if prev_player >= 0:
            refresh_gpw_page(prev_player)
        else:
            prev_page = _summary_page_prev(SUMMARY_PAGE_GPW)
            if prev_page != "main":
                refresh_start_summary_page(prev_page)
            show_page(prev_page)
            if prev_page == "main":
                update_startup_ui()
        update_status_line(force=True)
        return

    if button["role"] == "flow_next" and current_page_name in (SUMMARY_PAGE_LPS_PICTURE, SUMMARY_PAGE_LPS_SOUND, SUMMARY_PAGE_FIRST_TRY):
        next_page = _summary_page_next(current_page_name)
        if next_page != "main":
            refresh_start_summary_page(next_page)
        show_page(next_page)
        update_status_line(force=True)
        return

    if button["role"] == "flow_back" and current_page_name in (SUMMARY_PAGE_LPS_PICTURE, SUMMARY_PAGE_LPS_SOUND, SUMMARY_PAGE_FIRST_TRY):
        prev_page = _summary_page_prev(current_page_name)
        if prev_page != "main":
            refresh_start_summary_page(prev_page)
        show_page(prev_page)
        if prev_page == "main":
            update_startup_ui()
        update_status_line(force=True)
        return

    if button["role"] == "flow_back" and current_page_name == "name_entry":
        startup_new_player_text = ""
        startup_step = STARTUP_STEP_PLAYER
        show_page("main")
        update_startup_ui()
        return

    if button["role"] == "flow_next" and current_page_name == "name_entry":
        _set_name_entry_page(startup_name_entry_page + 1)
        update_name_entry_keyboard_ui()
        return

    if current_page_name == "name_entry":
        if button["role"] == "ne_prev":
            _set_name_entry_page(startup_name_entry_page - 1)
            update_name_entry_keyboard_ui()
            return

        if button["role"] == "ne_next":
            _set_name_entry_page(startup_name_entry_page + 1)
            update_name_entry_keyboard_ui()
            return

        if button["role"] == "ne_bksp":
            _handle_name_entry_action("BKSP")
            return

        if button["role"] == "ne_done":
            _handle_name_entry_action("DONE")
            return

        if button["role"] == "ne_char":
            _handle_name_entry_action(button.get("text", ""))
            return

        if button["role"] == "ne_dynamic":
            _handle_name_entry_action(button.get("text", ""))
            return

    if button["role"] == "flow_back" and current_page_name == "keyboard":
        reset_game_session_state()
        stop_audio_session()
        set_gameplay_np_color(NP_OFF)
        startup_step = STARTUP_STEP_READY
        startup_player_page = 0
        startup_new_player_text = ""
        _set_page_flow_back_button_text("keyboard", "BACK", BUTTON_FILL_COLOR)
        show_page("main")
        update_startup_ui()
        update_status_line(force=True)
        return

    if button["role"] == "flow_back" and current_page_name == "scores":
        reset_game_session_state(clear_word_list=True)
        set_gameplay_np_color(NP_OFF)
        startup_step = STARTUP_STEP_READY
        startup_player_page = 0
        startup_new_player_text = ""
        _set_page_flow_back_button_text("scores", "BACK", BUTTON_FILL_COLOR)
        show_page("main")
        update_startup_ui()
        update_status_line(force=True)
        return

    if button["role"] == "flow_next" and current_page_name == "scores":
        reset_game_session_state(clear_word_list=True)
        set_gameplay_np_color(NP_OFF)
        startup_step = STARTUP_STEP_READY
        startup_player_page = 0
        startup_new_player_text = ""
        _set_page_flow_back_button_text("scores", "BACK", BUTTON_FILL_COLOR)
        show_page("main")
        update_startup_ui()
        update_status_line(force=True)
        return

    if button["role"] == "flow_next" and current_page_name == "keyboard":
        if game_active:
            handle_skip_word()
        else:
            cycle_keyboard_panel_image()
        if current_page_name == "keyboard" and current_mode == MODE_AUDIO and not game_active:
            play_word_audio_for_current_image()
        return

    if button["role"] == "audio_replay" and current_page_name == "keyboard":
        if current_mode == MODE_AUDIO:
            play_word_audio_for_current_image()
        return

    if button["role"] == "show_answer" and current_page_name == "keyboard":
        if game_active:
            reveal_answer_for_current_word()
        return

    if current_page_name != "keyboard":
        return

    key_text = button.get("text", "")
    if not key_text:
        return

    if key_text == "BkSp":
        answer_display_text = answer_display_text[:-1]
    elif key_text == "ENTER":
        expected_answer = current_prompt_answer()
        typed_answer = answer_display_text.lower()
        if game_active and expected_answer and typed_answer:
            game_total_guesses += 1
        if expected_answer and typed_answer == expected_answer:
            print("Correct: {} ({})".format(typed_answer, _gameplay_memory_text()))
            if game_active:
                game_correct_total += 1
                if game_current_word_wrong_attempts == 0 and not game_current_word_hint_used:
                    game_first_try_correct_count += 1
                if not game_current_word_hint_used:
                    game_correct += 1
                set_gameplay_np_color(NP_CORRECT_GREEN)
            play_result_feedback(True)
            clear_last_answer_label()
            _set_keyboard_answer_button_visible(False)
            cycle_keyboard_panel_image()
            if current_page_name == "keyboard" and current_mode == MODE_AUDIO and not game_active:
                play_word_audio_for_current_image()
        else:
            print("Incorrect: '{}' expected '{}' ({})".format(typed_answer, expected_answer, _gameplay_memory_text()))
            show_wrong_answer_label(answer_display_text)
            if game_active:
                game_current_word_wrong_attempts += 1
                set_gameplay_wrong_attempt_leds(game_current_word_wrong_attempts)
                _set_keyboard_answer_button_visible(True)
                if not game_current_word_hint_used:
                    _track_wrong_no_hint_word(expected_answer)
            play_result_feedback(False)
            clear_answer_text()
            if game_active and game_current_word_wrong_attempts >= 3:
                reveal_answer_for_current_word()
            else:
                update_keyboard_panel_image()
                if current_mode == MODE_AUDIO:
                    play_word_audio_for_current_image()
    elif len(key_text) == 1 and key_text.isalpha():
        answer_display_text += key_text

    refresh_answer_display()


def main():
    global pages
    tick_startup_progress_leds()
    displayio.release_displays()
    print("Displays released.")
    tick_startup_progress_leds()
    backlight = digitalio.DigitalInOut(TFT_BACKLIGHT)
    backlight.direction = digitalio.Direction.OUTPUT
    # Keep panel dark until the first frame is fully initialized.
    backlight.value = True
    print("Backlight pin initialized, backlight on.")
    tick_startup_progress_leds()
    prepare_spi_chip_selects()
    print("SPI chip select pins initialized.")
    time.sleep(.05)  # Let CS lines settle before bringing up SPI bus.
    spi = board.SPI()
    time.sleep(.05)  # Let SPI bus stabilize before first device access.
    init_sd_card(spi)
    print("SD card initialized and mounted.")
    tick_startup_progress_leds()
    time.sleep(.05)   # Allow SD card bus activity to clear before display init.
    display = init_display(spi)
    print("Display initialized: {}x{} @ {} baud".format(DISPLAY_WIDTH, DISPLAY_HEIGHT, DISPLAY_SPI_BAUDRATE))
    tick_startup_progress_leds()
    time.sleep(.05)   # Allow display to finish init before touch controller setup.
    _touch = init_touch(spi)
    print("Touch controller initialized: {}x{} mapped to {}x{}".format(_touch.width, _touch.height, DISPLAY_WIDTH, DISPLAY_HEIGHT))
    tick_startup_progress_leds()
    time.sleep(.05)  # Let touch controller settle.
    load_fonts()
    print("Fonts loaded: {}".format(", ".join(FONTS.keys())))
    tick_startup_progress_leds()
    init_real_time_clock()
    print("Real-time clock initialized.")
    tick_startup_progress_leds()
    load_keyboard_image_paths("/sd/imgs")
    tick_startup_progress_leds()
    load_audio_word_paths(AUDIO_WORDS_DIR)
    print("Media file paths loaded: {} images, {} audio prompts".format(len(keyboard_image_paths), len(audio_word_paths)))
    tick_startup_progress_leds()
    if ENABLE_WAV_FORMAT_CHECK:
        validate_audio_prompt_formats()
    time.sleep(.05)
    tick_startup_progress_leds()
    pages = PageLayout(x=0, y=0)
    pages.add_content(build_main_page(), page_name="main")
    time.sleep(.05)
    tick_startup_progress_leds()
    pages.add_content(build_name_entry_page(), page_name="name_entry")
    time.sleep(.05)
    tick_startup_progress_leds()
    pages.add_content(build_keyboard_page(), page_name="keyboard")
    pages.add_content(build_scores_page(), page_name="scores")
    pages.add_content(build_summary_lps_picture_page(), page_name=SUMMARY_PAGE_LPS_PICTURE)
    pages.add_content(build_summary_lps_sound_page(), page_name=SUMMARY_PAGE_LPS_SOUND)
    pages.add_content(build_summary_first_try_page(), page_name=SUMMARY_PAGE_FIRST_TRY)
    pages.add_content(build_summary_gpw_page(), page_name=SUMMARY_PAGE_GPW)
    tick_startup_progress_leds()
    load_player_names()
    time.sleep(.05)
    tick_startup_progress_leds()
    update_startup_ui()
    set_game_mode(MODE_PICTURE)
    show_page("main")
    update_status_line(force=True)
    tick_startup_progress_leds()

    display.root_group = pages
    time.sleep(.05)
    backlight.value = True
    set_startup_progress_complete()
    time.sleep(.05)  # Let the first frame render with backlight on before playing audio.
    tick_startup_progress_leds()
    if init_audio_output():
        play_startup_wav()
        shutdown_audio_output()
    print("UI scaffold ready: main, keyboard, and scores pages.")
    set_startup_progress_idle()
    np.fill((64, 32, 100))
    touch_held = False
    while True:
        try:
            point = _touch.get_coordinates()
        except ReadFailedException:
            point = None
        except Exception:
            point = None

        if point is None:
            touch_held = False
        else:
            tx, ty = map_touch_to_screen(point)
            pressed = button_from_touch(tx, ty)
            if pressed is not None and not touch_held:
                handle_button_press(pressed)
                touch_held = True

        update_status_line()

        time.sleep(0.05)


main()
