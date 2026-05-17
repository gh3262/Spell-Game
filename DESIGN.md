# Spelling Game (Touchscreen Edition)

## Overview
A spelling game for a 4" 480x320 TFT touchscreen, using audio and visual cues to help players practice spelling. Features an on-screen keyboard, audio playback, and multiple game modes.

## Hardware Used
- **Microcontroller:** Adafruit Feather RP2040 with PSRAM
- **Display:** 4" 480x320 TFT (ST7789s SPI)
- **Touch:** XPT2046 SPI controller
- **Audio:** I2S DAC (TLV320DAC3100 or UDA1334A)
- **RTC:** DS3231 (I2C)
- **Storage:** SD card (SPI, CS D25)
- **Neopixels:** For visual feedback

## UI Layout
- **Keyboard:** 7x4 grid (26 letters + ENTER + BkSp), 50x50px keys, 1px margin
- **Info Line:** Clock, question count, etc.
- **Answer Line:** Top of screen, shows current input
- **Flow Buttons:** Top left/right, always visible
- **Replay/Skip Buttons:** For audio replay and skipping questions

## Game Modes
- **Audio Spelling:** Hear a word (mp3), spell it
- **Visual Spelling:** See an image, spell the word
    - Initial test uses 100x100 pixel .bmp files
- **Multiple Choice:** Select correct spelling from options

## Development Plan
- [ ] **Phase 1: UI Foundation**
    - Set up display and touch drivers
    - Implement on-screen keyboard page
    - Add flow buttons and info/answer lines
    - Test touch accuracy and layout
- [ ] **Phase 2: Game Logic & Audio**
    - Add answer checking logic
    - Integrate audio playback and replay
    - Implement skip and feedback features
- [ ] **Phase 3: Storage & Scoring**
    - Integrate SD card for assets and scores
    - Add RTC for time display
- [ ] **Phase 4: Advanced Features**
    - Add visual/multiple choice modes
    - Add Neopixel feedback
    - Add muscle memory and polish UI

## Feature List
- On-screen alpha keyboard
- Audio playback for words
- Visual feedback (correct/incorrect, last wrong answer)
- Score tracking and storage
- Multiple game modes (audio, visual, multiple choice)
- Replay and skip functionality
- Flow buttons for navigation

## Assets
- Problem banks (audio, images, choices)
- Fonts
- Audio files (mp3)

## Future Ideas
- More game modes
- Multiplayer support
- Online scoreboards

## File Structure
- **code.py**: Main entry point, UI, and game flow
- **game_engine.py**: Game state and logic
- **logic_core.py**: Core logic for spelling, scoring, etc.
- **adapters.py**: Hardware abstraction
- **settings.toml**: Configuration
- **lib/**: Libraries (display, touch, audio, etc.)
- **files/**: Player and score data
- **problem_banks/**: Word/audio/image banks
- **fonts/**: Bitmap fonts

---

*Update this document as the project evolves. Add diagrams, UI sketches, and design decisions as needed.*


## Brainstorm Notes (Edited)
Let me explain my initial thoughts and then set up a plan and documentation based on this.

- The project will use a 4" 480x320 TFT touchscreen with an ST7789S SPI display driver and an XPT2046 SPI touchscreen controller.
- The microprocessor will be an Adafruit Feather RP2350 with PSRAM, so we have plenty of memory space.
- We will use I2S audio with either the TLV320DAC3100 I2S DAC or the UDA1334A I2S stereo decoder for audio output.
- There will be a DS3231 RTC connected via I2C.
- There will be an SD card for storage of assets and score tracking. It will also be on the SPI bus using CS pin D25.

We will need an alpha on-screen keyboard. I think we can do this in a 7x4 grid, which gives us 26 letters plus ENTER and BkSp keys. My first thought is a layout like the attached image. With a 480-wide display, I think we can make the keys 50x50 pixels with 1 px margins around each key. The keyboard will be near the bottom of the screen, leaving enough room for a text line for clock/game time, question counts, etc., just like in the Math Game.

The top of the screen will be a text label for answer entry, where the player will touch letters and then hit ENTER when done, or use BkSp to delete letters from the right for corrections, just like the keypad function in the Math Game.

We will use the adafruit_displayio_layout library and its page layout tools.

We will need two game flow control buttons in the top left and top right, like in the Math Game, and they should appear on all pages.

There will be:
- a start page,
- a keyboard gameplay page, and
- score pages.

Audio will be used to play mp3 files for the words the player needs to spell. While entering an answer, the player should have a replay button to hear the word again.

There will be NeoPixels for visual indication. The Math Game had one; however, we can add multiple if the logic supports it.

Since we will have I2S audio, we will use it to generate game sounds, so we will not need a piezo buzzer, and we will need code to generate those tones.

I am also thinking about a mode that displays small bitmap images rather than mp3 words for the player to spell, so that could be another mode.

We might also consider a multiple choice mode where the player is presented with one correct spelling and three incorrect spellings. This will require a problem bank. There will also need to be lists for audio and visual problem banks that include file names and correct spellings.

Regardless of mode, the player will need to correctly touch the letters and then hit ENTER. If they are correct, it will move on to the next question. If incorrect, the text line will clear and they will need to try again. We should also add a way to show the last incorrect spelling so the player can see what they entered previously. This text should be smaller and red. The player should also have the option to skip a question.

Alternatively, we might consider giving the player a set number of chances to spell it correctly and then displaying the correct spelling in the wrong-answer space with green text. The player would then need to type the correct spelling to proceed, reinforcing muscle memory for correct spelling.
