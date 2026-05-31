# Spelling Game (Touchscreen Edition)

A spelling game for a 4" 480x320 TFT touchscreen, using audio and visual cues to help players practice spelling. See DESIGN.md for full details.

## Quick Start
1. Install CircuitPython on your Feather RP2040.
2. Copy project files to the device:
    - code.py, adapters.py, game_engine.py, logic_core.py, settings.toml
    - lib/ (required libraries)
    - fonts/ (bitmap fonts)
    - files/ (player and score data)
    - problem_banks/ (word/audio/image banks)
3. Insert SD card with assets and data files.
    - Picture prompts: `/sd/imgs/*.bmp`
    - Audio prompts: `/sd/wavs/*.wav`
        - Underscore-prefixed WAVs are reserved for startup/system use and are ignored during gameplay prompt loading.
        - Runtime data files in SD root:
            - `/sd/players.txt` (active players)
            - `/sd/scores.txt` (saved scores)
        - Runtime template file on board root:
            - `/tplayers.txt` (template players used to heal missing/empty `/sd/players.txt`)
        - Sample copies for these text files are in repo folder: `files/`
4. Reset the board and verify the title screen appears.

## Expected SD Card Layout
```text
/sd/
    players.txt
    scores.txt
    imgs/
    wavs/

/
    tplayers.txt
```

## Session Updates (2026-05-19)
- Startup flow now runs in stages: player select, optional new-name entry, mode select, prompt type select, and word-count select.
- Gameplay now uses a randomized per-round word list in both Picture and Audio modes.
- Round length is enforced using the selected word count (for example 10 words ends at 10).
- Correct answers advance through the active randomized list instead of file-order cycling.
- Skip now advances through the same active round list and updates skip tracking.
- Audio prompt double-play in Audio mode was fixed so each prompt is played once during active gameplay.
- Critical runtime imports were restored/verified after refactors (display, touch, RTC, SD, audio, font, and utility modules).

## Session Updates (2026-05-20)
- Placeholder image during startup explicitly set to `/sd/imgs/_sbee.bmp`.
- Removed unused `MODE` button from the startup screen.
- Fixed Audio mode replay issue where the last word would replay after the game ended.
- Improved hint/wrong-answer label handling to clear stale text when advancing prompts.
- Startup display initialization now releases display resources before SPI chip-select setup, avoiding the `D11 in use` failure.
- If the DS3231 is not present, the system RTC now falls back to `2026-01-01 13:00:00`.
- Startup audio now randomly selects one reserved `_start*.wav` greeting clip.
- The startup beep/tone test was removed from the normal boot path.
- Gameplay audio prompt loading now ignores underscore-prefixed WAVs, matching the reserved-asset rule already used for underscore-prefixed BMPs.
- Player selection now pages through names using `MORE` until the final page, where the fourth button becomes `NEW`.

## Session Updates (2026-05-31)
- Gameplay image panel now binds to the active round word during gameplay, so displayed image always matches `game_word_list[game_word_index]`.
- Main startup page now renders a dark image panel plus `_sbee.bmp` placeholder with fallback path handling.
- Startup title was repositioned lower to fit the startup image treatment.
- Player-list self-heal now restores `/sd/players.txt` from board-root `/tplayers.txt` when players file is missing or empty.
- Restore path now includes a guard: if `/tplayers.txt` cannot be read, restore is skipped and normal fallback behavior continues.
- Ongoing workflow note: gameplay improvements may land on one hardware platform first, then get ported to the other after validation.

## Deployment Checklist
1. Confirm local `code.py` saves cleanly and contains no syntax errors.
2. Copy updated app code to the board (`D:\code.py`).
3. Verify required libraries exist on device `lib/`:
    - `adafruit_bitmap_font`
    - `adafruit_display_text`
    - `adafruit_displayio_layout`
    - `adafruit_imageload`
    - `adafruit_ds3231`
    - `circuitpython_st7796s.py`
    - `xpt2046_circuitpython`
    - plus board-support libs already used by this project
4. Verify SD card root files exist:
    - `/sd/players.txt`
    - `/sd/scores.txt`
5. Verify board-root template exists:
    - `/tplayers.txt`
6. Verify SD card asset folders exist and are populated:
    - `/sd/imgs/*.bmp`
    - `/sd/wavs/*.wav`
    - Reserved startup/system clips may exist as `/sd/wavs/_*.wav`; these are excluded from gameplay prompt lists
7. Hardware sanity check after reboot:
    - Display initializes
    - Touch responds
    - One startup `_start*.wav` clip plays
    - RTC initializes (or logs a clear fallback message)
8. Functional smoke test:
    - Picture mode: select 10 words, confirm randomized list behavior and stop at 10
    - Audio mode: confirm no duplicate prompt playback and prompt advances correctly
9. Optional pre-push cleanup:
    - Reduce debug logging volume if no longer needed
    - Keep only diagnostics needed for field troubleshooting

## Known Good Test Script (2-3 Minutes)
1. Power-cycle or reset the board.
2. Wait for startup verification:
    - One startup `_start*.wav` clip completes
    - UI scaffold reports ready
3. Start a Picture round:
    - Select a player
    - Select `Picture`
    - Select `Random`
    - Select `10`
4. Confirm Picture behavior:
    - Debug output shows a 10-item selected list
    - First displayed prompt matches the selected list item
    - Enter one correct answer and verify advance to next selected prompt
    - Use skip once and verify round continues and index advances
5. Finish or fast-forward to end of round:
    - Verify the game stops at 10 total prompts and goes to Results
6. Start an Audio round:
    - Select `Audio`, `Random`, `10`
    - Confirm each prompt plays once (no double playback)
    - Confirm replay button still plays prompt on demand
7. If all checks pass, deploy/push is green.

## Project Structure
- code.py: Main entry point, UI, and game flow
- game_engine.py: Game state and logic
- logic_core.py: Core logic for spelling, scoring, etc.
- adapters.py: Hardware abstraction
- settings.toml: Configuration
- lib/: Libraries (display, touch, audio, etc.)
- files/: Player and score data
- problem_banks/: Word/audio/image banks
- fonts/: Bitmap fonts

## Credits
- Uses Adafruit libraries and hardware

---

*For design, hardware, and development plan, see DESIGN.md.*
