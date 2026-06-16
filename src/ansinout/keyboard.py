import sys
import os
import time
from typing import Tuple
from enum import Enum

_IS_WINDOWS = os.name == "nt"

if _IS_WINDOWS:
    import msvcrt
else:
    import select

ACCEPTED_CHARS = ["_", "-", ".", "/", "\\", ":", " ", "{", "}", "[", "]", "(", ")", "\"", ",", "?", "/", "&", "^", "%", "$", "#", "@", "!", "+", "=", "<", ">", "'", "*"]

def key_available(timeout: float = 0.0):
    if _IS_WINDOWS:
        # Windows `select` does not support stdin, so poll the console
        # keyboard buffer until a key shows up or the timeout elapses.
        if msvcrt.kbhit():
            return True
        if timeout <= 0:
            return False
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if msvcrt.kbhit():
                return True
            time.sleep(0.0005)
        return False
    rlist, _, _ = select.select([sys.stdin.fileno()], [], [], timeout)
    return bool(rlist)

class PressedKey(Enum):
    Alpha = "Alpha"
    ArrowUp = "ArrowUp"
    ArrowDown = "ArrowDown"
    ArrowLeft = "ArrowLeft"
    ArrowRight = "ArrowRight"
    Backspace = "Backspace"
    Enter = "Enter"
    Escape = "Escape"
    Delete = "Delete"
    PageUp = "PageUp"
    PageDown = "PageDown"
    Nop = "Nop"

# Maps the scancode byte that follows the \x00/\xe0 prefix returned by
# msvcrt for the Windows console's special keys.
_WINDOWS_SPECIAL_KEYS = {
    "H": PressedKey.ArrowUp,
    "P": PressedKey.ArrowDown,
    "K": PressedKey.ArrowLeft,
    "M": PressedKey.ArrowRight,
    "S": PressedKey.Delete,
    "I": PressedKey.PageUp,
    "Q": PressedKey.PageDown,
}

def _read_byte() -> str:
    data = os.read(sys.stdin.fileno(), 1)
    return data.decode("utf-8", errors="ignore") if data else ""

def _read_key_windows() -> Tuple[PressedKey, str]:
    ch = msvcrt.getwch()
    # Special keys (arrows, delete, page up/down, ...) are delivered as a
    # \x00 or \xe0 prefix followed by a scancode character.
    if ch in ("\x00", "\xe0"):
        code = msvcrt.getwch()
        key = _WINDOWS_SPECIAL_KEYS.get(code)
        if key is not None:
            return key, ch + code
        return PressedKey.Nop, ch + code
    if ch.isalpha() or ch.isnumeric() or ch in ACCEPTED_CHARS:
        return PressedKey.Alpha, ch
    if ch == "\r" or ch == "\n":
        return PressedKey.Enter, ch
    if ch == "\x08" or ch == "\x7f":
        return PressedKey.Backspace, ch
    if ch == "\x1b":
        return PressedKey.Escape, ch
    return PressedKey.Nop, ch

def read_key() -> Tuple[PressedKey, str]:
    if _IS_WINDOWS:
        return _read_key_windows()
    accepted_chars = ACCEPTED_CHARS
    ch = _read_byte()
    if ch.isalpha() or ch.isnumeric() or ch in accepted_chars:
        return PressedKey.Alpha, ch
    if ch == "\n" or ch == "\r":
        return PressedKey.Enter, ch
    if ch == "\x7f":
        return PressedKey.Backspace, ch
    if ch == "\x1b":
        # Distinguish bare Escape from escape sequences (arrows/delete/etc.)
        # by waiting briefly for continuation bytes.
        if not key_available(0.02):
            return PressedKey.Escape, ch

        seq = ""
        # Read a short sequence like "[A" or "[3~".
        while key_available(0.001) and len(seq) < 8:
            seq += _read_byte()
            # Common final bytes for CSI key sequences.
            if seq and (seq[-1].isalpha() or seq[-1] == "~"):
                break

        if seq == "[A":
            return PressedKey.ArrowUp, seq
        if seq == "[B":
            return PressedKey.ArrowDown, seq
        if seq == "[D":
            return PressedKey.ArrowLeft, seq
        if seq == "[C":
            return PressedKey.ArrowRight, seq
        if seq == "[3~":
            return PressedKey.Delete, seq
        if seq == "[5~":
            return PressedKey.PageUp, seq
        if seq == "[6~":
            return PressedKey.PageDown, seq

        # Fallback: unknown escape sequence acts as Escape.
        return PressedKey.Nop, seq
    return PressedKey.Nop, ""