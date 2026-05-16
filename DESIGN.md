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
