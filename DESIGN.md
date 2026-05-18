# Spelling Game (Touchscreen Edition)

## Overview
A spelling game for a 4" 480x320 TFT touchscreen, currently running in portrait mode, using touch input and image prompts to help players practice spelling. The current build has the core UI scaffold in place, a working touch keyboard, and a simple visual spelling loop based on BMP filenames.

## Current Status
- Display, touch, and page navigation are working in the main app.
- The UI scaffold is live with `main`, `keyboard`, and `scores` pages.
- The keyboard page loads BMP images from `/img` and derives the expected answer from each filename.
- Entered answers are checked on-device; correct answers advance to the next image, and incorrect answers clear the current entry.
- SD card support is wired for CS `D25` and works with a known-good SD card.
- Audio, RTC-driven status text, persistent scores/stats, and full game-engine integration are still pending.

## Hardware Used
- **Microcontroller:** Adafruit Feather RP2040-class board
- **Display:** 4" 480x320 TFT (ST7796S SPI)
- **Touch:** XPT2046 SPI controller
- **Audio:** I2S DAC (TLV320DAC3100 or UDA1334A)
- **RTC:** DS3231 (I2C)
- **Storage:** SD card (SPI, CS D25)
- **Neopixels:** For visual feedback

## Confirmed SPI Pin Map
- **TFT CS:** `D11`
- **Touch CS:** `D5`
- **SD CS:** `D25`
- **D12:** currently unused

## UI Layout
- The app runs in portrait mode using a `320x480` logical layout.
- **Main Page:** title screen with shared navigation chrome.
- **Keyboard Page:** 4x7 grid (26 letters + `ENTER` + `BkSp`), `74x35` keys, `2px` gaps, alternating blue row fills, yellow vowel labels, green `ENTER`, and yellow `BkSp`.
- **Image Panel:** `96x96` BMP preview area near the top of the keyboard page.
- **Answer Line:** centered near the top of the keyboard page and updated live as letters are pressed.
- **Flow Buttons:** shared top-corner navigation buttons across pages.
- **Scores Page:** scaffolded placeholder page; score presentation still needs to be implemented.

## Game Modes
- **Visual Spelling:** active prototype mode. The game loads `.bmp` images from `/img` and expects the spelling to match the image filename.
- **Audio Spelling:** planned, not implemented yet.
- **Multiple Choice:** planned, not implemented yet.

## Development Plan
- [x] **Phase 1: UI Foundation**
    - Display driver initialized in the main app
    - Touch driver initialized in the main app
    - Main, keyboard, and scores pages scaffolded
    - On-screen keyboard layout implemented
    - Shared page chrome/navigation implemented
- [ ] **Phase 2: Core Gameplay Loop**
    - Image loading from `/img`
    - Filename-based answer validation
    - Correct/incorrect handling in the keyboard page
    - Remaining work: better feedback, skip/replay controls, player-facing status text
- [ ] **Phase 3: Storage, Scores, and Runtime Data**
    - SD card initialization integrated into startup
    - Remaining work: persistent stats, high scores, player data, and RTC-backed info line
- [ ] **Phase 4: Audio and Expanded Modes**
    - Planned: audio spelling mode
    - Planned: multiple choice mode
    - Planned: sound effects, neopixel feedback, and polish

## Feature List
- On-screen alpha keyboard
- Page-based UI scaffold
- BMP image loading from `/img`
- Filename-based spelling check
- Flow buttons for navigation
- Planned: audio playback for words
- Planned: score tracking and storage
- Planned: multiple game modes beyond the current visual prototype
- Planned: replay and skip functionality

## Assets
- Problem banks (audio, images, choices)
- Fonts
- Audio files (mp3)

## Future Ideas
- More game modes
- Multiplayer support
- Online scoreboards

## Notes From Current Bring-Up
- SD behavior was initially inconsistent because one card/adapter combination was unreliable. A known-good card now mounts successfully on `D25`.
- The current code uses `sdcardio` and retries SD initialization cleanly without leaving the CS pin busy after a failed attempt.
- The app currently loads keyboard images directly from `/img`, which means the visual prototype can run even before the full problem-bank/audio pipeline is finished.

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


## Archived Brainstorm Notes
These notes are preserved for project history. Some hardware assumptions and layout ideas below were from early planning and have been superseded by the current-state sections above.

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
