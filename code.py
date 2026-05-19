import time
import gc
import array
import math
import board
import audiobusio
import audiocore
import digitalio
import displayio
import fourwire
import circuitpython_st7796s
import xpt2046_circuitpython
import adafruit_displayio_layout
import adafruit_bitmap_font.bitmap_font as bitmap_font
import adafruit_ds3231
import adafruit_imageload
import rtc
import sdcardio
import storage
import json
import os
from adafruit_display_text import label
from adafruit_displayio_layout.layouts.page_layout import PageLayout
from xpt2046_circuitpython.exceptions import ReadFailedException

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

FLOW_BUTTON_WIDTH = 64
FLOW_BUTTON_HEIGHT = 40
FLOW_BUTTON_MARGIN = 8

STATUS_LINE_Y = DISPLAY_HEIGHT - 12

KEYBOARD_COLS = 4
KEYBOARD_ROWS = 7
KEY_WIDTH = 74
KEY_HEIGHT = 35
KEY_GAP = 2
KEYBOARD_TOTAL_WIDTH = (KEYBOARD_COLS * KEY_WIDTH) + ((KEYBOARD_COLS - 1) * KEY_GAP)
KEYBOARD_TOTAL_HEIGHT = (KEYBOARD_ROWS * KEY_HEIGHT) + ((KEYBOARD_ROWS - 1) * KEY_GAP)
KEYBOARD_START_X = (DISPLAY_WIDTH - KEYBOARD_TOTAL_WIDTH) // 2
KEYBOARD_START_Y = 190

IMAGE_PANEL_SIZE = 96
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
audio_word_index = 0
audio_word_paths = []
current_mode = MODE_PICTURE
keyboard_mode_label = None
TEST_FILE_PATH = "/sd/test.txt"

STATS_FILE_PATH = "/sd/stats.json"
DEFAULT_STATS = {"total_games": 0, "total_correct": 0, "high_score": 0}

audio_out = None
audio_enable = None
system_rtc = rtc.RTC()
external_rtc = None
last_status_second = None


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
        print("I2S audio initialized")
        return True
    except Exception as exc:
        print("I2S audio init failed: {}".format(exc))
        shutdown_audio_output()
        return False


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

    if not init_audio_output():
        return False

    try:
        return play_startup_wav(wav_path)
    finally:
        shutdown_audio_output()


def play_result_feedback(is_correct):
    if not init_audio_output():
        return False

    try:
        if is_correct:
            sequence = ((660, 0.12, 0.05), (880, 0.18, 0.05))
        else:
            sequence = ((220, 0.16, 0.05), (180, 0.22, 0.05))
        return play_beep_sequence(sequence)
    finally:
        shutdown_audio_output()


def play_button_feedback():
    """Play a very short click tone for any button press."""
    if not init_audio_output():
        return False

    try:
        return play_beep_sequence(((960, 0.025, 0.0),))
    finally:
        shutdown_audio_output()


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


def current_image_answer():
    if not keyboard_image_paths:
        return ""

    image_path = keyboard_image_paths[keyboard_image_index]
    image_name = image_path.split("/")[-1]
    dot_index = image_name.rfind(".")
    if dot_index > 0:
        return image_name[:dot_index].lower()
    return image_name.lower()


def current_audio_answer():
    if not audio_word_paths:
        return ""

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
    if keyboard_page_group is None:
        return False

    if current_mode == MODE_AUDIO:
        clear_keyboard_panel_image()
        audio_mode_image_path = resolve_audio_mode_image_path()
        if audio_mode_image_path is None:
            print("Audio mode image not found (tried: {})".format(AUDIOMODE_IMAGE_CANDIDATES))
            return False

        try:
            global keyboard_image_tile, keyboard_image_bitmap, keyboard_image_file
            with open(audio_mode_image_path, "rb") as f:
                keyboard_image_bitmap, keyboard_image_palette = adafruit_imageload.load(f)
            keyboard_image_tile = displayio.TileGrid(
                keyboard_image_bitmap,
                pixel_shader=keyboard_image_palette,
                x=IMAGE_PANEL_X,
                y=IMAGE_PANEL_Y,
            )
            keyboard_page_group.append(keyboard_image_tile)
            print("Audio mode image loaded: {}".format(audio_mode_image_path))
            return True
        except Exception as exc:
            print("Audio mode image load failed for {}: {}".format(audio_mode_image_path, exc))
            clear_keyboard_panel_image()
            return False

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

    if not keyboard_image_paths:
        return False

    keyboard_image_index = (keyboard_image_index + 1) % len(keyboard_image_paths)
    clear_answer_text()
    clear_last_answer_label()
    return update_keyboard_panel_image()


def cycle_audio_prompt():
    global audio_word_index

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
    page = displayio.Group()
    add_background(page)
    add_shared_page_chrome(page, "main")

    title_label = label.Label(FONTS["title"], text="Spell Game", color=TITLE_TEXT_COLOR)
    title_label.anchor_point = (0.5, 0.5)
    title_label.anchored_position = (DISPLAY_WIDTH // 2, 95)
    page.append(title_label)

    mode_label = label.Label(FONTS["button"], text="Select Mode", color=TITLE_TEXT_COLOR)
    mode_label.anchor_point = (0.5, 0.5)
    mode_label.anchored_position = (DISPLAY_WIDTH // 2, 154)
    page.append(mode_label)

    add_button(
        page,
        "main",
        56,
        176,
        96,
        44,
        "Picture",
        "main_mode_picture",
        "mode_picture",
        font_key="button",
        fill_color=0x26547C,
    )

    add_button(
        page,
        "main",
        168,
        176,
        96,
        44,
        "Audio",
        "main_mode_audio",
        "mode_audio",
        font_key="button",
        fill_color=0xB85C00,
    )
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
    global answer_display_text

    play_button_feedback()

    if button["role"] == "mode_picture" and current_page_name == "main":
        set_game_mode(MODE_PICTURE)
        show_page("keyboard")
        return

    if button["role"] == "mode_audio" and current_page_name == "main":
        set_game_mode(MODE_AUDIO)
        show_page("keyboard")
        play_word_audio_for_current_image()
        return

    if button["role"] == "flow_next" and current_page_name == "main":
        show_page("keyboard")
        if current_mode == MODE_AUDIO:
            play_word_audio_for_current_image()
        return

    if button["role"] == "flow_back" and current_page_name == "keyboard":
        show_page("main")
        return

    if button["role"] == "flow_next" and current_page_name == "keyboard":
        cycle_keyboard_panel_image()
        if current_mode == MODE_AUDIO:
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
            play_result_feedback(True)
            clear_last_answer_label()
            cycle_keyboard_panel_image()
            if current_mode == MODE_AUDIO:
                play_word_audio_for_current_image()
        else:
            print("Incorrect: '{}' expected '{}'".format(typed_answer, expected_answer))
            show_wrong_answer_label(answer_display_text)
            play_result_feedback(False)
            clear_answer_text()
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
    time.sleep(0.1)   # Allow SD card bus activity to clear before display init.
    display = init_display(spi)
    time.sleep(0.1)   # Allow display to finish init before touch controller setup.
    _touch = init_touch(spi)
    time.sleep(0.05)  # Let touch controller settle.

    pages = PageLayout(x=0, y=0)
    pages.add_content(build_main_page(), page_name="main")
    pages.add_content(build_keyboard_page(), page_name="keyboard")
    pages.add_content(build_scores_page(), page_name="scores")
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
