import time
import board
import digitalio
import displayio
import fourwire
import neopixel
import circuitpython_st7796s
import xpt2046_circuitpython
from xpt2046_circuitpython.exceptions import ReadFailedException
from adafruit_display_text import label
from terminalio import FONT

# Display SPI pins (updated for this hardware revision).
TFT_CS = board.D11
TFT_DC = board.D9
TFT_RST = board.D10
TFT_BACKLIGHT = board.D6

# Touch controller chip-select pin.
TOUCH_CS = board.D5

DISPLAY_WIDTH = 480
DISPLAY_HEIGHT = 320
DISPLAY_ROTATION = 180

# Touch orientation tuning.
TOUCH_SWAP_XY = True
TOUCH_INVERT_X = False
TOUCH_INVERT_Y = False

pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixel[0] = (0, 255, 0)  # Green to indicate

displayio.release_displays()

print("Initializing display and touch controller...")
backlight = digitalio.DigitalInOut(TFT_BACKLIGHT)
backlight.direction = digitalio.Direction.OUTPUT
backlight.value = True
print("Backlight on.")


spi = board.SPI()
display = circuitpython_st7796s.ST7796S(
    fourwire.FourWire(
        spi,
        command=TFT_DC,
        chip_select=TFT_CS,
        reset=TFT_RST,
    ),
    width=DISPLAY_WIDTH,
    height=DISPLAY_HEIGHT,
    rotation=DISPLAY_ROTATION,
)

root = displayio.Group()
background_bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 1)
background_palette = displayio.Palette(1)
background_palette[0] = 0x101820
root.append(displayio.TileGrid(background_bitmap, pixel_shader=background_palette, x=0, y=0))

status = label.Label(FONT, text="Display Test", color=0xFFFFFF)
status.anchor_point = (0.5, 0.5)
status.anchored_position = (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2)
root.append(status)

display.root_group = root

print("Display initialized.")
time.sleep(2)  # Pause to show the display test message.
status.text = "Initializing touch controller..."
time.sleep(2)  # Pause to show the touch initialization message.
print("Initializing touch controller...")
    # return spi


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


def touch_test(touch, status):
    """Visual touch test to help calibrate touchscreen."""
    # Add a touch indicator on top of the existing background/text group.
    dot_palette = displayio.Palette(1)
    dot_palette[0] = 0xFF0000  # Red
    dot_bitmap = displayio.Bitmap(5, 5, 1)
    dot = displayio.TileGrid(dot_bitmap, pixel_shader=dot_palette)
    dot.x = -10
    dot.y = -10
    root.append(dot)

    while True:
        try:
            point = touch.get_coordinates()
        except ReadFailedException:
            point = None
        except Exception as exc:
            print("touch read error:", exc)
            point = None

        if point is None:
            dot.x = -10  # Move off-screen when no touch detected.
            dot.y = -10
            status.text = "Waiting for touch..."
            pixel[0] = (255, 255, 0)
        else:
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

            dot.x = x
            dot.y = y
            status.text = "Touch: ({}, {})".format(x, y)
            pixel[0] = (0, 255, 0)  # Green to indicate touch detected
            print("Raw touch: {}, Mapped: ({}, {})".format(point, x, y))

        time.sleep(0.05)


# Ensure displayio.release_displays() is called before initializing the display.
def main():

    touch = init_touch(spi)
    print("Touch controller initialized.")
    status.text = "Touch controller initialized."
    time.sleep(1)  # Pause to show the touch initialization message.
    touch_test(touch, status)

main()
