import time
import gc
import board
import digitalio
import displayio
import fourwire
import circuitpython_st7796s
import xpt2046_circuitpython
import adafruit_displayio_layout
import adafruit_bitmap_font.bitmap_font as bitmap_font
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
SD_CS = board.D25

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
TEST_FILE_PATH = "/sd/test.txt"

STATS_FILE_PATH = "/sd/stats.json"
DEFAULT_STATS = {"total_games": 0, "total_correct": 0, "high_score": 0}


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


def load_fonts():
    for font_key in FONT_PATHS:
        FONTS[font_key] = bitmap_font.load_font(FONT_PATHS[font_key])


def refresh_answer_display():
    if answer_display_label is not None:
        answer_display_label.text = answer_display_text if answer_display_text else "_"


def clear_answer_text():
    global answer_display_text
    answer_display_text = ""
    refresh_answer_display()


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
        if lower_name.endswith(".bmp"):
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


def current_image_answer():
    if not keyboard_image_paths:
        return ""

    image_path = keyboard_image_paths[keyboard_image_index]
    image_name = image_path.split("/")[-1]
    dot_index = image_name.rfind(".")
    if dot_index > 0:
        return image_name[:dot_index].lower()
    return image_name.lower()


def update_keyboard_panel_image():
    global keyboard_image_tile, keyboard_image_bitmap, keyboard_image_file

    if keyboard_page_group is None or not keyboard_image_paths:
        return False

    if keyboard_image_tile is not None:
        try:
            keyboard_page_group.remove(keyboard_image_tile)
        except Exception:
            pass
        keyboard_image_tile = None

    if keyboard_image_file is not None:
        try:
            keyboard_image_file.close()
        except Exception:
            pass
        keyboard_image_file = None

    keyboard_image_bitmap = None

    image_path = keyboard_image_paths[keyboard_image_index]
    try:
        keyboard_image_file = open(image_path, "rb")
        keyboard_image_bitmap = displayio.OnDiskBitmap(keyboard_image_file)
        keyboard_image_tile = displayio.TileGrid(
            keyboard_image_bitmap,
            pixel_shader=keyboard_image_bitmap.pixel_shader,
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

    if not keyboard_image_paths:
        return False

    keyboard_image_index = (keyboard_image_index + 1) % len(keyboard_image_paths)
    clear_answer_text()
    return update_keyboard_panel_image()


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
        text="TIME --:-- | Q 00/00 | MODE ---",
        color=STATUS_TEXT_COLOR,
    )
    status_line.anchor_point = (0.5, 1.0)
    status_line.anchored_position = (DISPLAY_WIDTH // 2, STATUS_LINE_Y)
    page_group.append(status_line)


def build_main_page():
    page = displayio.Group()
    add_background(page)
    add_shared_page_chrome(page, "main")

    title_label = label.Label(FONTS["title"], text="Spell Game", color=TITLE_TEXT_COLOR)
    title_label.anchor_point = (0.5, 0.5)
    title_label.anchored_position = (DISPLAY_WIDTH // 2, 95)
    page.append(title_label)
    return page


def build_keyboard_page():
    global answer_display_label, keyboard_page_group

    page = displayio.Group()
    keyboard_page_group = page
    add_background(page)
    add_shared_page_chrome(page, "keyboard")

    header = label.Label(FONTS["button"], text="Keyboard", color=TITLE_TEXT_COLOR)
    header.anchor_point = (0.5, 0.5)
    header.anchored_position = (DISPLAY_WIDTH // 2, 118)
    page.append(header)

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

    if button["role"] == "flow_next" and current_page_name == "main":
        show_page("keyboard")
        return

    if button["role"] == "flow_back" and current_page_name == "keyboard":
        show_page("main")
        return

    if button["role"] == "flow_next" and current_page_name == "keyboard":
        cycle_keyboard_panel_image()
        return

    if current_page_name != "keyboard":
        return

    key_text = button.get("text", "")
    if not key_text:
        return

    if key_text == "BkSp":
        answer_display_text = answer_display_text[:-1]
    elif key_text == "ENTER":
        expected_answer = current_image_answer()
        typed_answer = answer_display_text.lower()
        if expected_answer and typed_answer == expected_answer:
            print("Correct: {}".format(typed_answer))
            cycle_keyboard_panel_image()
        else:
            print("Incorrect: '{}' expected '{}'".format(typed_answer, expected_answer))
            clear_answer_text()
            update_keyboard_panel_image()
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

    prepare_spi_chip_selects()
    spi = board.SPI()
    init_sd_card(spi)
    load_keyboard_image_paths("/img")
    display = init_display(spi)
    _touch = init_touch(spi)

    pages = PageLayout(x=0, y=0)
    pages.add_content(build_main_page(), page_name="main")
    pages.add_content(build_keyboard_page(), page_name="keyboard")
    pages.add_content(build_scores_page(), page_name="scores")
    show_page("main")

    display.root_group = pages
    time.sleep(0.05)
    backlight.value = True
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

        time.sleep(0.05)


main()
