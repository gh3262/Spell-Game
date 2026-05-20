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
import math
import os
import sdcardio
import storage
import fourwire
import adafruit_imageload
import adafruit_ds3231
import circuitpython_st7796s
import xpt2046_circuitpython
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import label
from adafruit_displayio_layout.layouts.page_layout import PageLayout
from xpt2046_circuitpython.exceptions import ReadFailedException
from adafruit_ili9341 import ILI9341
from xpt2046_circuitpython import XPT2046

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
AUDIO_STARTUP_WAV = "/sd/wavs/about.wav"
AUDIO_WORDS_DIR = "/sd/wavs"
AUDIOMODE_IMAGE_CANDIDATES = ("/img/_audio.bmp", "/imgs/_audio.bmp")
MODE_PICTURE = "picture"
MODE_AUDIO = "audio"
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

FLOW_BUTTON_WIDTH = 64
FLOW_BUTTON_HEIGHT = 40
FLOW_BUTTON_MARGIN = 8

STATUS_LINE_Y = DISPLAY_HEIGHT - 12

START_ACTIONS_TOP_Y = 360
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
    "score": "/fonts/Calibri-17.pcf",
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
audio_mode_bitmap_cache = None
audio_mode_palette_cache = None
audio_mode_image_path_cache = None
audio_word_index = 0
audio_word_paths = []
current_mode = MODE_PICTURE
keyboard_mode_label = None
TEST_FILE_PATH = "/sd/test.txt"
PLAYERS_FILE_PATH = "/sd/players.txt"
TPLAYERS_FILE_PATH = "/sd/tplayers.txt"
SCORES_FILE_PATH = "/sd/scores.txt"

STATS_FILE_PATH = "/sd/stats.json"
DEFAULT_STATS = {"total_games": 0, "total_correct": 0, "high_score": 0}

audio_out = None
audio_enable = None
audio_session_active = False
system_rtc = rtc.RTC()
external_rtc = None
last_status_second = None

startup_title_label = None
startup_prompt_label = None
startup_summary_label = None
startup_start_button = None
startup_option_buttons = []
startup_option_actions = [None, None, None, None]

STARTUP_STEP_READY = "ready"
STARTUP_STEP_PLAYER = "player"
STARTUP_STEP_NAME_ENTRY = "name_entry"
STARTUP_STEP_MODE = "mode"
STARTUP_STEP_PROMPT_TYPE = "prompt_type"
STARTUP_STEP_WORD_COUNT = "word_count"

startup_step = STARTUP_STEP_READY
startup_player_names = []
startup_player_page = 0
startup_name_entry_page = 0
startup_new_player_text = ""
startup_selected_player = ""
startup_selected_mode = MODE_PICTURE
startup_selected_prompt_type = "random"
startup_selected_word_count = 10
MAX_PLAYER_NAME_LEN = 12

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


def _normalize_player_name(name_text):
    return name_text.strip()


def load_player_names(file_path=PLAYERS_FILE_PATH):
    global startup_player_names

    try:
        with open(file_path, "r") as players_file:
            lines = players_file.readlines()
    except Exception as exc:
        print("Player list read failed for {}: {}".format(file_path, exc))
        startup_player_names = ["PLAYER 1"]
        return False

    names = []
    for line in lines:
        candidate = _normalize_player_name(line)
        if candidate:
            names.append(candidate)

    if not names:
        names = ["PLAYER 1"]

    startup_player_names = names
    return True


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

    if page_index < 0:
        page_index = 0
    last_index = len(NAME_ENTRY_DYNAMIC_PAGES) - 1
    if page_index > last_index:
        page_index = last_index
    startup_name_entry_page = page_index


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


def _set_start_option(slot_index, text, action_data, fill_color):
    startup_option_actions[slot_index] = action_data
    _set_button_visual(startup_option_buttons[slot_index], text, fill_color)


def _clear_start_option(slot_index):
    startup_option_actions[slot_index] = None
    _set_button_visual(startup_option_buttons[slot_index], "", 0x2F3A44)


def _startup_summary_text():
    player_text = startup_selected_player if startup_selected_player else "-"
    mode_text = "PIC" if startup_selected_mode == MODE_PICTURE else "AUD"
    prompt_text = "RAND" if startup_selected_prompt_type == "random" else "CAT"
    return "{} | {} | {} | {}".format(player_text, mode_text, prompt_text, startup_selected_word_count)


def update_startup_ui():
    if startup_prompt_label is None or startup_summary_label is None or startup_start_button is None:
        return

    startup_summary_label.text = _startup_summary_text()

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

        _set_start_option(3, "NEW", {"kind": "new_player", "value": "NEW"}, MATH_GAME_ORANGE)
        return

    if startup_step == STARTUP_STEP_MODE:
        startup_prompt_label.text = "Select Game Mode"
        _set_start_option(0, "Picture", {"kind": "mode", "value": MODE_PICTURE}, MATH_GAME_BLUE)
        _set_start_option(1, "Audio", {"kind": "mode", "value": MODE_AUDIO}, MATH_GAME_ORANGE)
        _clear_start_option(2)
        _clear_start_option(3)
        return

    if startup_step == STARTUP_STEP_PROMPT_TYPE:
        startup_prompt_label.text = "Random or Category"
        _set_start_option(0, "Random", {"kind": "prompt_type", "value": "random"}, MATH_GAME_GREEN)
        _set_start_option(1, "Category", {"kind": "prompt_type", "value": "category"}, MATH_GAME_GOLD)
        _clear_start_option(2)
        _clear_start_option(3)
        return

    if startup_step == STARTUP_STEP_WORD_COUNT:
        startup_prompt_label.text = "How Many Words?"
        _set_start_option(0, "10", {"kind": "word_count", "value": 10}, MATH_GAME_BLUE)
        _set_start_option(1, "20", {"kind": "word_count", "value": 20}, MATH_GAME_ORANGE)
        _set_start_option(2, "35", {"kind": "word_count", "value": 35}, MATH_GAME_GREEN)
        _set_start_option(3, "50", {"kind": "word_count", "value": 50}, MATH_GAME_GOLD)
        return


def begin_startup_flow():
    global startup_step, startup_player_page, startup_name_entry_page, startup_new_player_text

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
        startup_step = STARTUP_STEP_PROMPT_TYPE
    elif startup_step == STARTUP_STEP_PROMPT_TYPE:
        startup_step = STARTUP_STEP_WORD_COUNT

    update_startup_ui()


def _goto_previous_startup_step():
    global startup_step

    if startup_step == STARTUP_STEP_WORD_COUNT:
        startup_step = STARTUP_STEP_PROMPT_TYPE
    elif startup_step == STARTUP_STEP_PROMPT_TYPE:
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


def finalize_startup_flow():
    print("[DEBUG] Entered finalize_startup_flow")  # Confirm function entry
    global game_word_list, game_word_index, game_total, game_correct, game_skipped, game_active
    set_game_mode(startup_selected_mode)
    # Select the correct asset list
    if startup_selected_mode == MODE_PICTURE:
        asset_list = keyboard_image_paths[:]
    else:
        asset_list = audio_word_paths[:]
    print("[DEBUG] Asset list prepared, selecting words...")  # Confirm asset list setup
    # Randomly select X unique words
    word_count = min(startup_selected_word_count, len(asset_list))
    game_word_list = _select_random_unique_items(asset_list, word_count)
    print("[DEBUG] Selected word list:")
    for i, w in enumerate(game_word_list):
        print("  {}: {}".format(i+1, w))
    game_word_index = 0
    game_total = word_count
    game_correct = 0
    game_skipped = 0
    game_active = True
    print(
        "Start game: player='{}' mode='{}' prompt='{}' words={}".format(
            startup_selected_player,
            startup_selected_mode,
            startup_selected_prompt_type,
            startup_selected_word_count,
        )
    )
    print("[DEBUG] finalize_startup_flow completed")  # Confirm function exit
    if startup_selected_mode == MODE_AUDIO:
        start_audio_session()
    else:
        stop_audio_session()
    show_page("keyboard")
    show_current_game_word()


def show_current_game_word():
    """Update the UI to show the current word/image/audio."""
    global game_word_list, game_word_index, game_active, keyboard_image_bitmap, keyboard_image_tile
    print(f"[DEBUG] Showing current word. Index: {game_word_index}, Active: {game_active}")
    if not game_active or game_word_index >= len(game_word_list):
        print("[DEBUG] No active game or index out of range.")
        return
    # Set the current asset index for answer checking and display
    if current_mode == MODE_PICTURE:
        # Load and display the image directly from the randomized list
        image_path = game_word_list[game_word_index]
        print(f"[DEBUG] Displaying image: {image_path}")
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
            print(f"[DEBUG] Image loaded and displayed successfully")
        except Exception as exc:
            print("Failed to load image {}: {}".format(image_path, exc))
    else:
        # Play audio directly from the randomized list
        audio_path = game_word_list[game_word_index]
        print(f"[DEBUG] Playing audio: {audio_path}")
        try:
            global audio_word_index
            audio_word_index = audio_word_paths.index(audio_path)
            update_keyboard_panel_image()
            play_word_audio_for_current_image()
        except Exception as exc:
            print("Failed to play audio {}: {}".format(audio_path, exc))
    clear_answer_text()
    refresh_answer_display()


def handle_skip_word():
    global game_skipped, game_word_index, game_active
    if game_active:
        game_skipped += 1
        advance_to_next_word()


def advance_to_next_word():
    global game_word_index, game_active, game_total
    print(f"[DEBUG] Advancing to next word. Current index: {game_word_index}, Total: {game_total}")
    game_word_index += 1
    if game_word_index >= game_total:
        print("[DEBUG] Word limit reached. Ending game.")
        game_active = False
        stop_audio_session()
        show_results_page()
    else:
        show_current_game_word()


def handle_startup_option(slot_index):
    global startup_selected_player, startup_selected_mode, startup_selected_prompt_type
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

    if action_kind == "mode":
        startup_selected_mode = action_value
        _goto_next_startup_step()
        return

    if action_kind == "prompt_type":
        startup_selected_prompt_type = action_value
        _goto_next_startup_step()
        return

    if action_kind == "word_count":
        startup_selected_word_count = action_value
        finalize_startup_flow()
        return


def build_status_line_text():
    mode_text = "PIC" if current_mode == MODE_PICTURE else "AUD"

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

    return "{} | Q 00/00 | MODE {}".format(clock_text, mode_text)


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


def play_startup_wav(file_path=AUDIO_STARTUP_WAV):
    if audio_out is None:
        return False

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
        keyboard_mode_label.text = ""


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


def update_keyboard_mode_label():
    """Called on mode change — clear the last-answer label for the new mode."""
    clear_last_answer_label()


def load_keyboard_image_paths(folder_path="/img"):
    global keyboard_image_paths, keyboard_image_index

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
    keyboard_image_index = 0

    if not keyboard_image_paths:
        print("No BMP images found in {}".format(folder_path))
        return False

    print("Loaded {} keyboard images from {}".format(len(keyboard_image_paths), folder_path))
    for image_path in keyboard_image_paths:
        print("  {}".format(image_path))
    return True


def load_audio_word_paths(folder_path=AUDIO_WORDS_DIR):
    global audio_word_paths, audio_word_index

    try:
        names = os.listdir(folder_path)
    except Exception as exc:
        audio_word_paths = []
        audio_word_index = 0
        print("Audio folder read failed for {}: {}".format(folder_path, exc))
        return False

    wav_names = []
    for name in names:
        if name.lower().endswith(".wav"):
            wav_names.append(name)

    wav_names.sort()
    audio_word_paths = ["{}/{}".format(folder_path, name) for name in wav_names]
    audio_word_index = 0

    if not audio_word_paths:
        print("No WAV files found in {}".format(folder_path))
        return False

    print("Loaded {} audio prompts from {}".format(len(audio_word_paths), folder_path))
    for wav_path in audio_word_paths:
        print("  {}".format(wav_path))
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

    if not keyboard_image_paths:
        clear_keyboard_panel_image()
        return False

    clear_keyboard_panel_image()

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
        "tile": button_tile,
        "label": button_label,
        "x0": x,
        "x1": x + w,
        "y0": y,
        "y1": y + h,
    }
    BUTTON_REGISTRY.append(button_info)
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


def build_main_page():
    global startup_title_label, startup_prompt_label, startup_summary_label
    global startup_start_button, startup_option_buttons

    page = displayio.Group()
    add_background(page)
    add_shared_page_chrome(page, "main")

    startup_title_label = label.Label(FONTS["title"], text="Spell Game", color=TITLE_TEXT_COLOR)
    startup_title_label.anchor_point = (0.5, 0.5)
    startup_title_label.anchored_position = (DISPLAY_WIDTH // 2, 88)
    page.append(startup_title_label)

    startup_prompt_label = label.Label(FONTS["button"], text="Press START", color=TITLE_TEXT_COLOR)
    startup_prompt_label.anchor_point = (0.5, 0.5)
    startup_prompt_label.anchored_position = (DISPLAY_WIDTH // 2, 148)
    page.append(startup_prompt_label)

    startup_summary_label = label.Label(FONTS["score"], text="- | PIC | RAND | 10", color=STATUS_TEXT_COLOR)
    startup_summary_label.anchor_point = (0.5, 0.5)
    startup_summary_label.anchored_position = (DISPLAY_WIDTH // 2, 182)
    page.append(startup_summary_label)

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

    add_button(
        page,
        "main",
        DISPLAY_WIDTH - FLOW_BUTTON_MARGIN - 88,
        58,
        88,
        34,
        "MODE",
        "main_mode_hint",
        "main_mode_hint",
        font_key="small_button",
        fill_color=0x2F3A44,
    )

    update_startup_ui()
    return page


def build_keyboard_page():
    global answer_display_label, keyboard_page_group, keyboard_mode_label

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

    add_button(
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
        ("NEXT", "name_entry_next", "ne_next", MATH_GAME_GREEN),
        ("BKSP", "name_entry_bksp", "ne_bksp", MATH_GAME_ORANGE),
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
    page = displayio.Group()
    add_background(page)
    add_shared_page_chrome(page, "scores")

    header = label.Label(FONTS["button"], text="Scores", color=TITLE_TEXT_COLOR)
    header.anchor_point = (0.5, 0.5)
    header.anchored_position = (DISPLAY_WIDTH // 2, 95)
    page.append(header)
    return page


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
    try:
        with open(STATS_FILE_PATH, "r") as stats_file:
            return json.loads(stats_file.read())
    except Exception:
        return dict(DEFAULT_STATS)


def save_game_stats(stats):
    try:
        with open(STATS_FILE_PATH, "w") as stats_file:
            stats_file.write(json.dumps(stats))
        print("Stats saved: {}".format(stats))
        return True
    except Exception as exc:
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
        if button["x0"] <= x < button["x1"] and button["y0"] <= y < button["y1"]:
            return button
    return None


def show_page(page_name):
    global current_page_name
    pages.show_page(page_name)
    current_page_name = page_name


def handle_button_press(button):
    global answer_display_text, startup_player_page, startup_step, startup_new_player_text
    global game_active, game_word_index, game_total, game_correct

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
        stop_audio_session()
        show_page("main")
        return

    if button["role"] == "flow_next" and current_page_name == "keyboard":
        if game_active:
            handle_skip_word()
        else:
            cycle_keyboard_panel_image()
        if current_mode == MODE_AUDIO and not game_active:
            play_word_audio_for_current_image()
        return

    if button["role"] == "audio_replay" and current_page_name == "keyboard":
        if current_mode == MODE_AUDIO:
            play_word_audio_for_current_image()
        return

    if button["role"] == "show_answer" and current_page_name == "keyboard":
        clear_answer_text()
        show_correct_answer_hint()
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
        if expected_answer and typed_answer == expected_answer:
            print("Correct: {}".format(typed_answer))
            if game_active:
                game_correct += 1
            play_result_feedback(True)
            clear_last_answer_label()
            cycle_keyboard_panel_image()
            if current_mode == MODE_AUDIO and not game_active:
                play_word_audio_for_current_image()
        else:
            print("Incorrect: '{}' expected '{}'".format(typed_answer, expected_answer))
            show_wrong_answer_label(answer_display_text)
            play_result_feedback(False)
            clear_answer_text()
            if game_active:
                # Keep the displayed prompt aligned with the current randomized game word.
                show_current_game_word()
            else:
                update_keyboard_panel_image()
                if current_mode == MODE_AUDIO:
                    play_word_audio_for_current_image()
    elif len(key_text) == 1 and key_text.isalpha():
        answer_display_text += key_text

    refresh_answer_display()


def main():
    global pages

    displayio.release_displays()

    backlight = digitalio.DigitalInOut(TFT_BACKLIGHT)
    backlight.direction = digitalio.Direction.OUTPUT
    # Keep panel dark until the first frame is fully initialized.
    backlight.value = False

    load_fonts()

    init_real_time_clock()
    prepare_spi_chip_selects()
    time.sleep(0.05)  # Let CS lines settle before bringing up SPI bus.
    spi = board.SPI()
    time.sleep(0.05)  # Let SPI bus stabilize before first device access.
    init_sd_card(spi)
    load_keyboard_image_paths("/sd/imgs")
    load_audio_word_paths(AUDIO_WORDS_DIR)
    if ENABLE_WAV_FORMAT_CHECK:
        validate_audio_prompt_formats()
    time.sleep(0.1)   # Allow SD card bus activity to clear before display init.
    display = init_display(spi)
    time.sleep(0.1)   # Allow display to finish init before touch controller setup.
    _touch = init_touch(spi)
    time.sleep(0.05)  # Let touch controller settle.

    pages = PageLayout(x=0, y=0)
    pages.add_content(build_main_page(), page_name="main")
    pages.add_content(build_name_entry_page(), page_name="name_entry")
    pages.add_content(build_keyboard_page(), page_name="keyboard")
    pages.add_content(build_scores_page(), page_name="scores")
    load_player_names()
    update_startup_ui()
    set_game_mode(MODE_PICTURE)
    show_page("main")
    update_status_line(force=True)

    display.root_group = pages
    time.sleep(0.05)
    backlight.value = True
    if init_audio_output():
        play_startup_wav()
        play_startup_beep_sequence()
        shutdown_audio_output()
    print("UI scaffold ready: main, keyboard, and scores pages.")

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
