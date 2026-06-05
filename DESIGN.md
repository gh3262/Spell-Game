# Spelling Game (Touchscreen Edition)

## Overview
A spelling game for a 4" 480x320 TFT touchscreen, currently running in portrait mode, using touch input with two active prompt modes: Picture and Audio. The current build includes a working page-based UI, touch keyboard, manifest-first image/WAV prompt loading with SD fallback, and gameplay feedback audio.

Active runtime asset locations on SD card:
- Picture prompts: `/sd/imgs/*.bmp`
- Audio prompts: `/sd/wavs/*.wav`
    - Underscore-prefixed WAVs are reserved for startup/system use and are excluded from gameplay prompt loading.

Primary gameplay prompt index sources (board root):
- `pictures.py` (`PICTURES_BY_LENGTH`)
- `sounds.py` (`SOUNDS_BY_LENGTH`)

Runtime behavior:
- Manifest indexes are preferred for gameplay prompt loading.
- If manifest import/shape/contents are invalid, runtime falls back to SD directory scans.

Runtime data files on SD card root:
- `/sd/players.txt` (current active player list)
- `/sd/scores.txt` (saved score data)

Runtime template file on board root:
- `/tplayers.txt` (template player list used to heal missing/empty `/sd/players.txt`)

Repository sample data files:
- Sample copies are kept in the repo `files/` folder: `files/players.txt`, `files/tplayers.txt`, and `files/scores.txt`.

## Current Status
- Display, touch, and page navigation are working in the main app.
- The UI scaffold is live with `main`, `keyboard`, and `scores` pages.
- Startup display bring-up now releases any previous display bus ownership before SPI chip-select setup.
- Main page now includes mode selection buttons: Picture and Audio.
- Player selection now pages names in groups of three, with the fourth button switching between `MORE` and `NEW` based on remaining pages.
- Picture mode loads BMP files from `/sd/imgs` and derives the expected answer from the image filename.
- Audio mode loads WAV prompts from `/sd/wavs`, ignores underscore-prefixed reserved files, plays the active file, and derives the expected answer from the WAV filename.
- In Audio mode, the keyboard panel displays a fixed speaker image (`/img/_audio.bmp`, with fallback `/imgs/_audio.bmp`).
- Entered answers are checked on-device; correct answers advance prompts and incorrect answers clear current entry.
- Success/fail beep feedback is implemented on `ENTER`.
- Replay button is implemented on the keyboard page for Audio mode.
- SD card support is wired for CS `D12` and mounts at `/sd` in the current build.
- RTC-driven status text is active; when the DS3231 is absent, boot falls back to `2026-01-01 13:00:00`.
- Summary pages now use a dynamic lifecycle: unload during startup/gameplay flow and rebuild on demand when summary views are opened.

## Session Updates (2026-05-19)
- Startup flow now supports staged configuration before play:
    - Player select
    - New player name entry
    - Mode select (Picture/Audio)
    - Prompt type select
    - Word count select
- Finalize/start now builds a per-round active list (`game_word_list`) and resets round counters/indexes.
- Random selection uses a CircuitPython-compatible unique picker (no dependency on `random.sample`).
- Active gameplay prompt/answer flow now reads from the round list rather than raw file-order indices.
- Next-word advancement now enforces the configured round length (`game_total`) and exits to results when complete.
- Skip path is integrated into round progression and skip counting.
- Audio-mode duplicate prompt playback was fixed by removing secondary replay calls after advancement.
- Runtime import set was repaired after refactor drift so startup and hardware init paths resolve correctly.

## Session Updates (2026-05-20)
- Startup sequencing was tightened so `displayio.release_displays()` runs before SPI chip-select setup, preventing `D11 in use` failures at boot.
- DS3231 boot failure now seeds the CircuitPython RTC with `2026-01-01 13:00:00` so time/status formatting remains usable without external RTC hardware.
- Startup audio now randomly selects one `_start*.wav` greeting clip from the reserved startup pool.
- The normal startup beep/tone verification path was removed.
- Gameplay WAV discovery now excludes underscore-prefixed files, matching the reserved-asset rule used for BMP prompt loading.
- Player selection paging now surfaces additional name pages through a `MORE` action before exposing `NEW` on the final page.
- Placeholder image during startup explicitly set to `/sd/imgs/_sbee.bmp`.
- Removed unused `MODE` button from the startup screen.
- Fixed Audio mode replay issue where the last word would replay after the game ended.
- Improved hint/wrong-answer label handling to clear stale text when advancing prompts.

## Session Updates (2026-05-31)
- Keyboard image panel now uses the active gameplay word image during rounds (`game_word_list[game_word_index]`) instead of static preview indexing.
- Main startup page now renders a dark 120x120 panel and attempts to load `_sbee.bmp` with fallback path handling.
- Startup title vertical position was moved lower to accommodate startup image placement.
- Player-file recovery now restores `/sd/players.txt` from board-root `/tplayers.txt` when players data is missing/empty.
- Recovery now includes a template-read guard so missing `/tplayers.txt` does not trigger unnecessary restore-write errors.
- Branching workflow note: features can be iterated on one hardware platform first and back-ported after validation.

## Session Updates (2026-06-05)
- Ported gameplay indexing updates from alternate hardware branch into this project.
- Prompt lists now prefer static manifest modules (`pictures.py`, `sounds.py`) rather than scanning all SD assets each load.
- Added manifest path normalization and filtering safeguards:
    - accepted length buckets (`3`, `4`, `5`, `6+`)
    - file suffix enforcement (`.bmp` / `.wav`)
    - reserved underscore-prefix exclusion
    - stable sorting before flattened list build
- Added dynamic summary-page load/unload behavior to reduce memory pressure affecting audio stability during gameplay.
- Hardware mappings and device bring-up paths were intentionally not changed as part of this port.

## Deployment Checklist
1. Save and deploy updated `code.py` to board root.
    - Deploy updated `pictures.py` and `sounds.py` to board root when changed.
2. Verify `lib/` contains required runtime modules used by current code paths:
    - `adafruit_bitmap_font.bitmap_font`
    - `adafruit_display_text`
    - `adafruit_displayio_layout`
    - `adafruit_imageload`
    - `adafruit_ds3231`
    - `circuitpython_st7796s.py`
    - `xpt2046_circuitpython`
    - supporting CircuitPython core modules (`fourwire`, etc.)
3. Verify SD mount prerequisites:
    - `/sd/players.txt`
    - `/sd/scores.txt`
    - `/sd/imgs/*.bmp`
    - `/sd/wavs/*.wav`
4. Verify board-root template file exists:
    - `/tplayers.txt`
5. Verify board-root gameplay manifest files exist:
    - `/pictures.py`
    - `/sounds.py`
6. Boot validation:
    - RTC init logs expected state
    - SD mounts without retries/failures
    - Display init completes without CS pin conflicts
    - UI scaffold initializes (`main`, `keyboard`, `scores`)
    - One reserved startup WAV plays
7. Gameplay validation:
    - Picture mode uses randomized round list and stops at selected word count
    - Audio mode plays one prompt per word (no duplicate play), advances correctly, and respects round limit
8. Before push:
    - Remove or reduce temporary debug prints not needed for field diagnostics
    - Confirm README/DESIGN notes reflect current behavior

## Known Good Test Script (2-3 Minutes)
1. Reset board and capture startup logs.
2. Confirm bring-up sequence:
    - RTC init path logs expected state
    - SD mount succeeds
    - Display init completes without `D11 in use`
    - One startup `_start*.wav` clip completes
    - UI scaffold initialized
3. Execute Picture mode smoke test:
    - Player -> Picture -> Random -> 10
    - Verify selected 10-word debug list appears
    - Verify current displayed prompt is from selected list
    - Verify one correct answer advances to the next selected prompt
4. Execute skip behavior check:
    - Trigger skip once in active round
    - Verify index advances and round remains bounded by selected count
5. Execute round-end check:
    - Verify transition to Results at configured total (`game_total`)
6. Execute Audio mode smoke test:
    - Player -> Audio -> Random -> 10
    - Verify each prompt plays once on advance
    - Verify replay button triggers prompt playback on demand
7. If all checks pass, mark build as known-good for push.

## Hardware Used
- **Microcontroller:** Adafruit Feather RP2040-class board
- **Display:** 4" 480x320 TFT (ST7796S SPI)
- **Touch:** XPT2046 SPI controller
- **Audio Amplifier:** Adafruit MAX98357A I2S 3W Class-D mono amp
- **RTC:** DS3231 (I2C)
- **Storage:** SD card (SPI, CS D12)
- **Neopixels:** For visual feedback

## Confirmed Pin Map
- **TFT CS:** `D11`
- **Touch CS:** `D5`
- **SD CS:** `D12`
- **I2S BCLK:** `A0`
- **I2S LRC/WS:** `A1`
- **I2S DIN:** `A3`
- **MAX98357A SD/Enable:** `A2`
- **D12:** SD card CS in current build

## UI Layout
- The app runs in portrait mode using a `320x480` logical layout.
- **Main Page:** title screen with shared navigation chrome and mode selection buttons (Picture/Audio).
- **Keyboard Page:** 4x7 grid (26 letters + `ENTER` + `BkSp`), `74x35` keys, `2px` gaps, alternating blue row fills, yellow vowel labels, green `ENTER`, and yellow `BkSp`.
- **Image Panel:** `120x120` area near the top of the keyboard page.
- Picture mode displays the current prompt image.
- Audio mode displays a fixed speaker image.
- **Answer Line:** centered near the top of the keyboard page and updated live as letters are pressed.
- **Flow Buttons:** shared top-corner navigation buttons across pages.
- **Replay Button:** available on the keyboard page for replaying audio prompts in Audio mode.
- **Scores Page:** scaffolded placeholder page; score presentation still needs to be implemented.

## Game Modes
- **Picture Spelling (active):** loads `.bmp` images from `/sd/imgs` and expects spelling to match the image filename.
- **Audio Spelling (active):** loads `.wav` prompts from `/sd/wavs`, plays the prompt, and expects spelling to match the wav filename.
- **Multiple Choice:** planned, not implemented yet.

## Development Plan
- [x] **Phase 1: UI Foundation**
    - Display driver initialized in the main app
    - Touch driver initialized in the main app
    - Main, keyboard, and scores pages scaffolded
    - On-screen keyboard layout implemented
    - Shared page chrome/navigation implemented
- [x] **Phase 2: Core Gameplay Loop**
    - Image loading from `/sd/imgs`
    - Filename-based answer validation
    - Correct/incorrect handling in the keyboard page
    - Picture mode and Audio mode selection implemented
    - Audio prompt replay implemented
    - Success/fail beep feedback implemented
- [ ] **Phase 3: Storage, Scores, and Runtime Data**
    - SD card initialization integrated into startup
    - WAV prompt loading from `/sd/wavs` integrated
    - Remaining work: persistent stats, high scores, player data, and RTC-backed info line
- [ ] **Phase 4: Audio and Expanded Modes**
    - Planned: multiple choice mode
    - Planned: richer audio cue set and polish
    - Planned: neopixel feedback integration

## Feature List
- On-screen alpha keyboard
- Page-based UI scaffold
- BMP image loading from `/sd/imgs`
- WAV audio prompt loading from `/sd/wavs`
- Manifest-first prompt indexing from board-root `pictures.py` / `sounds.py` with SD fallback
- Reserved `_*.wav` files excluded from gameplay prompt selection
- Filename-based spelling checks (image mode and audio mode)
- Flow buttons for navigation
- Audio replay button on keyboard page
- Audio success/fail beep feedback
- Random startup greeting WAV selected from reserved `_start*.wav` files
- Planned: score tracking and storage
- Planned: multiple game modes beyond the current visual prototype
- Planned: skip/question pacing controls

## Assets
- Prompt assets are expected on the SD card at `/sd/imgs` and `/sd/wavs`
- Prompt manifests are expected on board root as `pictures.py` and `sounds.py`
- Images should be 120x120 .bmp files
- Audio prompt files should be `.wav`; underscore-prefixed WAVs are treated as reserved system assets and excluded from gameplay prompt rotation
- Reserved audio-mode speaker image is currently loaded from SD candidates: `/sd/img/_audio.bmp` then `/sd/imgs/_audio.bmp`
- Problem banks (audio, images, choices)
- Fonts
- Audio files (wav currently active, mp3 planned later)

## SD Card Layout (Expected)
```text
/sd/
    players.txt      # active player list used by runtime
    scores.txt       # saved scores
    imgs/            # picture prompts (*.bmp)
    wavs/            # audio prompts (*.wav)

/
    tplayers.txt     # template player list for healing /sd/players.txt
```

Repo-side sample files for SD root data:
- `files/players.txt`
- `files/tplayers.txt`
- `files/scores.txt`

## Troubleshooting (Manifest Loading)
- Symptom: No prompts loaded from manifests.
    - Confirm board-root files exist: `/pictures.py`, `/sounds.py`.
    - Confirm exported names are exact: `PICTURES_BY_LENGTH`, `SOUNDS_BY_LENGTH`.
    - Confirm manifest values are dictionaries of lists/tuples.
- Symptom: Some manifest entries do not appear in gameplay lists.
    - Only `.bmp` entries are accepted for pictures and `.wav` for sounds.
    - Underscore-prefixed filenames are intentionally excluded from gameplay prompt pools.
    - Invalid bucket keys are ignored; use `"3"`, `"4"`, `"5"`, `"6+"`.
- Symptom: Runtime appears to ignore manifests and use SD scan ordering.
    - This indicates manifest import/validation fallback occurred.
    - Re-check syntax and runtime validity of board copies of `pictures.py` and `sounds.py`.
- Symptom: Prompt asset fails when selected during gameplay.
    - Verify the manifest path exactly matches an existing SD file path.
    - Verify SD mount is healthy and `/sd/imgs` and `/sd/wavs` are readable.

## Future Ideas
- More game modes
- Multiplayer support
- Online scoreboards

## Notes From Current Bring-Up
- SD behavior was initially inconsistent because one card/adapter combination was unreliable. A known-good card now mounts successfully on `D12`.
- The current code uses `sdcardio` and retries SD initialization cleanly without leaving the CS pin busy after a failed attempt.
- Startup now releases any existing display bus before reasserting SPI chip-select pins, preventing the `D11 in use` failure seen during bring-up.
- Audio hardware is confirmed working with MAX98357A using `A0/A1/A3` plus `A2` enable control.
- Startup now plays one random reserved `_start*.wav` clip, while gameplay excludes underscore-prefixed WAVs from prompt rotation.
- WAV playback plus gameplay feedback beeps are both confirmed working without breaking touchscreen input.
- Picture mode excludes underscore-prefixed BMP files so reserved images (for example `_audio.bmp`) are not used as Picture prompts.

## File Structure
- **code.py**: Main entry point, UI, and game flow
- **pictures.py**: Static picture prompt manifest (`PICTURES_BY_LENGTH`)
- **sounds.py**: Static audio prompt manifest (`SOUNDS_BY_LENGTH`)
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
- SD card storage on SPI using CS pin D12.

Retained concept notes from early planning:
- Keep an on-screen alpha keyboard as the primary input surface.
- Keep dedicated start, gameplay, and scores pages.
- Keep replay support for spoken prompts.
- Keep optional visual feedback paths (including neopixel cues) for future polish.
- Keep multiple-choice and expanded problem-bank modes on the roadmap.
- Keep reinforcement-oriented feedback ideas (wrong-answer display, retries, and guided correction) for future iteration.
