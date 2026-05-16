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
4. Reset the board and verify the title screen appears.

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
