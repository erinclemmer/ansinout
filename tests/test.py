import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ansinout import (
    enable_vt_mode, exit_vt_mode,
    TuiWindow, TermText,
    read_key, key_available, PressedKey,
    Color, move_cursor
)

fd, attrs = enable_vt_mode()
try:
    win = TuiWindow(size=(40, 10), pos=(0, 0))
    key_enum_id = win.add_text(TermText("Enum: ", fg=Color.Cyan), pos=(0, 0))
    raw_id = win.add_text(TermText("Raw: ", fg=Color.Cyan), pos=(0, 1))
    win.paint()

    while True:
        if key_available(0.05):
            key, raw = read_key()
            if key == PressedKey.Escape:
                break
            win.update_text(key_enum_id, TermText("Enum: " + key.name))
            win.update_text(raw_id, TermText("Raw: " + raw))
        win.paint()
        move_cursor(2, 0)
        
finally:
    exit_vt_mode(fd, attrs)