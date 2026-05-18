# Spelling Game (Touchscreen Edition)

## Overview
A spelling game for a 4" 480x320 TFT touchscreen, currently running in portrait mode, using touch input with two active prompt modes: Picture and Audio. The current build includes a working page-based UI, touch keyboard, SD-backed image and WAV prompt loading, and gameplay feedback audio.

## Current Status
- Display, touch, and page navigation are working in the main app.
- The UI scaffold is live with `main`, `keyboard`, and `scores` pages.
- Main page now includes mode selection buttons: Picture and Audio.
- Picture mode loads BMP files from `/img` and derives the expected answer from the image filename.
- Audio mode loads WAV prompts from `/wavs`, plays the active file, and derives the expected answer from the WAV filename.
- In Audio mode, the keyboard panel displays a fixed speaker image (`/img/_audio.bmp`, with fallback `/imgs/_audio.bmp`).
- Entered answers are checked on-device; correct answers advance prompts and incorrect answers clear current entry.
- Success/fail beep feedback is implemented on `ENTER`.
- Replay button is implemented on the keyboard page for Audio mode.
- SD card support is wired for CS `D25` and works with a known-good SD card.
- RTC-driven status text, persistent scores/stats, and full game-engine integration are still pending.

## Hardware Used
- **Microcontroller:** Adafruit Feather RP2040-class board
- **Display:** 4" 480x320 TFT (ST7796S SPI)
- **Touch:** XPT2046 SPI controller
- **Audio Amplifier:** Adafruit MAX98357A I2S 3W Class-D mono amp
- **RTC:** DS3231 (I2C)
- **Storage:** SD card (SPI, CS D25)
- **Neopixels:** For visual feedback

## Confirmed Pin Map
- **TFT CS:** `D11`
- **Touch CS:** `D5`
- **SD CS:** `D25`
- **I2S BCLK:** `A0`
- **I2S LRC/WS:** `A1`
- **I2S DIN:** `A3`
- **MAX98357A SD/Enable:** `A2`
- **D12:** currently unused

## UI Layout
- The app runs in portrait mode using a `320x480` logical layout.
- **Main Page:** title screen with shared navigation chrome and mode selection buttons (Picture/Audio).
- **Keyboard Page:** 4x7 grid (26 letters + `ENTER` + `BkSp`), `74x35` keys, `2px` gaps, alternating blue row fills, yellow vowel labels, green `ENTER`, and yellow `BkSp`.
- **Image Panel:** `96x96` area near the top of the keyboard page.
- Picture mode displays the current prompt image.
- Audio mode displays a fixed speaker image.
- **Answer Line:** centered near the top of the keyboard page and updated live as letters are pressed.
- **Flow Buttons:** shared top-corner navigation buttons across pages.
- **Replay Button:** available on the keyboard page for replaying audio prompts in Audio mode.
- **Scores Page:** scaffolded placeholder page; score presentation still needs to be implemented.

## Game Modes
- **Picture Spelling (active):** loads `.bmp` images from `/img` and expects spelling to match the image filename.
- **Audio Spelling (active):** loads `.wav` prompts from `/wavs`, plays the prompt, and expects spelling to match the wav filename.
- **Multiple Choice:** planned, not implemented yet.

## Development Plan
- [x] **Phase 1: UI Foundation**
    - Display driver initialized in the main app
    - Touch driver initialized in the main app
    - Main, keyboard, and scores pages scaffolded
    - On-screen keyboard layout implemented
    - Shared page chrome/navigation implemented
- [x] **Phase 2: Core Gameplay Loop**
    - Image loading from `/img`
    - Filename-based answer validation
    - Correct/incorrect handling in the keyboard page
    - Picture mode and Audio mode selection implemented
    - Audio prompt replay implemented
    - Success/fail beep feedback implemented
- [ ] **Phase 3: Storage, Scores, and Runtime Data**
    - SD card initialization integrated into startup
    - WAV prompt loading from `/wavs` integrated
    - Remaining work: persistent stats, high scores, player data, and RTC-backed info line
- [ ] **Phase 4: Audio and Expanded Modes**
    - Planned: multiple choice mode
    - Planned: richer audio cue set and polish
    - Planned: neopixel feedback integration

## Feature List
- On-screen alpha keyboard
- Page-based UI scaffold
- BMP image loading from `/img`
- WAV audio prompt loading from `/wavs`
- Filename-based spelling checks (image mode and audio mode)
- Flow buttons for navigation
- Audio replay button on keyboard page
- Audio success/fail beep feedback
- Startup WAV + beep hardware verification path
- Planned: score tracking and storage
- Planned: multiple game modes beyond the current visual prototype
- Planned: skip/question pacing controls

## Assets
- Prompt assets in `/img` and `/wavs`
- Problem banks (audio, images, choices)
- Fonts
- Audio files (wav currently active, mp3 planned later)

## Future Ideas
- More game modes
- Multiplayer support
- Online scoreboards

## Notes From Current Bring-Up
- SD behavior was initially inconsistent because one card/adapter combination was unreliable. A known-good card now mounts successfully on `D25`.
- The current code uses `sdcardio` and retries SD initialization cleanly without leaving the CS pin busy after a failed attempt.
- Audio hardware is confirmed working with MAX98357A using `A0/A1/A3` plus `A2` enable control.
- WAV playback plus generated beep sequences are both confirmed working without breaking touchscreen input.
- Picture mode excludes underscore-prefixed BMP files so reserved images (for example `_audio.bmp`) are not used as Picture prompts.

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
These notes are preserved for project history only.

Do not use this section for current wiring or implementation decisions.
For active hardware and software behavior, use:
- `Current Status`
- `Hardware Used`
- `Confirmed Pin Map`

Legacy assumptions retained below are intentionally marked as superseded where needed.

- [Superseded] Early display-driver assumption: ST7789S (current build uses ST7796S).
- [Superseded] Early board wording: RP2350 mention (current project notes use RP2040-class board wording).
- [Superseded] Early audio-device assumption: TLV320/UDA1334A path (current build uses MAX98357A on I2S).
- DS3231 RTC connected via I2C.
- SD card storage on SPI using CS pin D25.

Retained concept notes from early planning:
- Keep an on-screen alpha keyboard as the primary input surface.
- Keep dedicated start, gameplay, and scores pages.
- Keep replay support for spoken prompts.
- Keep optional visual feedback paths (including neopixel cues) for future polish.
- Keep multiple-choice and expanded problem-bank modes on the roadmap.
- Keep reinforcement-oriented feedback ideas (wrong-answer display, retries, and guided correction) for future iteration.
