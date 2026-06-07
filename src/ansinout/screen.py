import os
import sys
from enum import Enum
from typing import Optional

_IS_WINDOWS = os.name == "nt"

if _IS_WINDOWS:
    import ctypes
    from ctypes import wintypes
else:
    import termios
    import tty

ESC = "\x1b["
ALT_SCR_ENTER = f"{ESC}?1049h"
ALT_SCR_EXIT  = f"{ESC}?1049l"
CLS = f"{ESC}2J"
HOME = f"{ESC}H"

# Windows console handle / mode constants
_STD_OUTPUT_HANDLE = -11
_ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

def write(s: str):
    sys.stdout.write(s)
    sys.stdout.flush()

def _enable_vt_mode_windows():
    # Turn on ANSI/VT escape sequence processing for stdout so the same
    # escape codes used on POSIX render correctly in the Windows console.
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(_STD_OUTPUT_HANDLE)
    old_mode = wintypes.DWORD()
    kernel32.GetConsoleMode(handle, ctypes.byref(old_mode))
    kernel32.SetConsoleMode(
        handle, old_mode.value | _ENABLE_VIRTUAL_TERMINAL_PROCESSING
    )
    write(ALT_SCR_ENTER + CLS + HOME)
    return (handle, old_mode.value)

def _exit_vt_mode_windows(handle, old_mode):
    write(ALT_SCR_EXIT)
    ctypes.windll.kernel32.SetConsoleMode(handle, old_mode)

def enable_vt_mode():
    if _IS_WINDOWS:
        return _enable_vt_mode_windows()
    fd_in = sys.stdin.fileno()
    old_in_attrs = termios.tcgetattr(fd_in)
    tty.setcbreak(fd_in)
    write(ALT_SCR_ENTER + CLS + HOME)
    return (fd_in, old_in_attrs)

def exit_vt_mode(handle, old_state):
    if _IS_WINDOWS:
        _exit_vt_mode_windows(handle, old_state)
        return
    write(ALT_SCR_EXIT)
    termios.tcsetattr(handle, termios.TCSADRAIN, old_state)

def print_pos(row: int, col: int, s: str, fg: Optional['Color'] = None, bg: Optional['BgColor'] = None, bold: bool = False):
    # ANSI positions are 1-based
    s = color(s, fg, bg, bold)
    write(f"{ESC}{row + 1};{col + 1}H{s}")

def move_cursor(row: int, col: int):
    try:
        write(f"{ESC}{row + 1};{col + 1}H")
    except Exception:
        pass

class CursorTypes(Enum):
    Default = 1
    Blinking_Block = 1
    Steady_Block = 2
    Blinking_Underline = 3
    Steady_Underline = 4
    Blinking_Bar = 5
    Steady_Bar = 6

def change_cursor(t: CursorTypes):
    write(f"\033[{t.value} q")

class Color(Enum):
    # Standard foreground colors (30-37)
    Black = 30
    Red = 31
    Green = 32
    Yellow = 33
    Blue = 34
    Magenta = 35
    Cyan = 36
    White = 37
    Default = 39
    # Bright foreground colors (90-97)
    BrightBlack = 90
    Gray = 90
    BrightRed = 91
    BrightGreen = 92
    BrightYellow = 93
    BrightBlue = 94
    BrightMagenta = 95
    BrightCyan = 96
    BrightWhite = 97


class BgColor(Enum):
    # Standard background colors (40-47)
    Black = 40
    Red = 41
    Green = 42
    Yellow = 43
    Blue = 44
    Magenta = 45
    Cyan = 46
    White = 47
    Default = 49
    # Bright background colors (100-107)
    BrightBlack = 100
    Gray = 100
    BrightRed = 101
    BrightGreen = 102
    BrightYellow = 103
    BrightBlue = 104
    BrightMagenta = 105
    BrightCyan = 106
    BrightWhite = 107


def color(text: str, fg: Optional[Color] = None, bg: Optional[BgColor] = None, bold: bool = False) -> str:
    codes = []
    if bold:
        codes.append("1")

    if isinstance(fg, Color):
        codes.append(str(fg.value))

    if isinstance(bg, BgColor):
        codes.append(str(bg.value))

    if len(codes) == 0:
        return text

    prefix = f"\033[{';'.join(codes)}m"
    reset = "\033[0m"
    return f"{prefix}{text}{reset}"
