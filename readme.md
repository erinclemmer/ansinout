## ANSINOUT (ANSI + IN + OUT)

A small, dependency-free Python library for building Terminal User Interfaces.

Ansinout provides a thin layer over raw ANSI escape codes without the weight of a full framework.

* **Zero dependencies.** Only uses the standard library.
* **Keyboard input utils** Easy to use functions for reading user input.
* **Easy styling** Foreground/background colors and bold are arguments on the text primitive.
* **Diff-based rendering.** Only cells that have changed since the last frame are written to the terminal.

## Usage

A typical program follows this lifecycle: enter VT mode, build a window, loop on input and repaint, then restore the terminal on exit.

```python
from ansinout import (
    enable_vt_mode, exit_vt_mode,
    TuiWindow, TuiText, TermText,
    read_key, key_available, PressedKey,
    Color, BgColor,
)

fd, attrs = enable_vt_mode()
try:
    win = TuiWindow(size=(40, 10), pos=(0, 0))
    hello = win.add_text(TermText("Hello, world!", fg=Color.Cyan), pos=(0, 0))
    win.paint()

    while True:
        if key_available(0.05):
            key, raw = read_key()
            if key == PressedKey.Escape:
                break
        win.paint()
finally:
    exit_vt_mode(fd, attrs)
```

### Screen lifecycle

#### `enable_vt_mode() -> (fd, old_attrs)`

Prepares the terminal for interactive use. The function captures the current termios attributes of standard input, switches the input file descriptor into cbreak mode so that key presses are delivered without line buffering, enters the alternate screen buffer, clears it, and moves the cursor to the home position. It returns a tuple containing the standard input file descriptor and the original termios attributes, which must be retained and passed to `exit_vt_mode` during shutdown.

```python
fd, attrs = enable_vt_mode()
```

#### `exit_vt_mode(fd, old_attrs)`

Restores the terminal to the state it was in before `enable_vt_mode` was called. The function leaves the alternate screen buffer, returning the terminal to the primary screen, and restores the original termios attributes captured by `enable_vt_mode`. The `fd` and `old_attrs` arguments must be the values returned from that call. It should typically be invoked inside a `finally` block to ensure the terminal is restored regardless of how the program exits.

```python
exit_vt_mode(fd, attrs)
```

### TUI building blocks

#### `TermText(value, fg=None, bg=None, bold=False)`

A `TermText` pairs a string with an optional foreground color, an optional background color, and a bold flag. It is accepted by every TUI primitive that renders text. The styling applies uniformly to the entire string.

```python
title = TermText("Inbox", fg=Color.White, bg=BgColor.Blue, bold=True)
```

#### `TuiText`

The object returned by `TuiWindow.get_text`. It wraps a `TermText` value together with an `id`, a `position`, a derived `size`, and a `hidden` flag. Instances are created by `TuiWindow.add_text` rather than constructed directly.

#### `TuiWindow(size, pos)`

The main container. A `TuiWindow` owns a grid of cells with dimensions equal to `size` and a list of `TuiText` objects positioned within it. The window itself is anchored at `pos`, which is interpreted as an absolute `(column, row)` offset in the terminal. All `TuiText` positions are relative to the window's anchor.

```python
win = TuiWindow(size=(80, 24), pos=(0, 0))
```

##### `add_text(value, pos) -> int`

Adds a `TermText` to the window at the given relative `(column, row)` position and returns an integer id. The id is used by every other method that operates on a specific text object.

```python
tid = win.add_text(TermText("Press Esc to quit", fg=Color.Gray), pos=(0, 23))
```

##### `update_text(id, value, pos=None)`

Replaces the contents and/or position of an existing text object. If `value` is `None`, the existing text is preserved and only the position is changed. If `pos` is `None`, the position is preserved. Cells previously occupied by the old text are cleared so the next `paint()` removes any stale characters.

```python
win.update_text(tid, TermText("Bye!", fg=Color.Red))
win.update_text(tid, None, pos=(10, 5))
win.update_text(tid, TermText("Hi"), (0, 0))
```

##### `get_text(id) -> TuiText`

Returns the underlying `TuiText` instance for the given id or `None` if not found.

```python
obj = win.get_text(tid)
```

##### `hide_txt(id)` and `show_txt(id)`

`hide_txt` marks the text object as hidden and clears the cells it currently occupies so the next paint erases it from the terminal. The text object and its id remain in the window and can be redisplayed with `show_txt`, which clears the hidden flag and rewrites the text into the grid.

```python
win.hide_txt(tid)
win.show_txt(tid)
```

##### `hide_all()` and `show_all()`

Hide or show every text object currently in the window.

```python
win.hide_all()
win.show_all()
```

##### `remove_txt(id)` and `remove_all()`

`remove_txt` clears the cells occupied by the text object and removes it from the window's text list. `remove_all` performs the same operation for every text object in the window.

```python
win.remove_txt(tid)
win.remove_all()
```

##### `update_position(pos)`

Moves the window to a new absolute `(column, row)` anchor. The function hides all currently visible text objects, paints the cleared state to remove the old rendering, updates the anchor, and restores visibility at the new location.

```python
win.update_position((5, 2))
```

##### `clear_screen()`

Replaces every cell in the window's grid with a space. This stages a full erase that takes effect on the next `paint()`. It does not remove text objects from the window.

```python
win.clear_screen()
```

##### `paint()`

Flushes pending changes to the terminal. The method walks the grid and writes only the cells whose contents differ from what was last painted, then returns the cursor to the origin. Because the operation is incremental, `paint()` is safe to call in a tight render loop.

```python
win.paint()
```

### Keyboard input

#### `key_available(timeout=0.0) -> bool`

Reports whether standard input has data ready to be read. The call blocks for at most `timeout` seconds and returns `True` as soon as input becomes available, or `False` if the timeout elapses first. A timeout of `0.0` performs a non-blocking poll. The function is typically used in a render loop to wait briefly for input without preventing periodic repaints.

```python
if key_available(0.05):
    key, raw = read_key()
```

#### `read_key() -> (PressedKey, str)`

Reads a single key press from standard input and returns a tuple of `(PressedKey, raw)`, where `PressedKey` is the categorized key and `raw` is the underlying byte sequence as a string. The function handles multi-byte escape sequences for the arrow keys and the Delete key, and distinguishes a bare Escape press from the start of an escape sequence by waiting briefly for continuation bytes. Unknown escape sequences are reported as `PressedKey.Nop` with the full received sequence as the raw value.

```python
key, raw = read_key()
if key == PressedKey.Alpha:
    buffer += raw
elif key == PressedKey.Backspace:
    buffer = buffer[:-1]
```

#### `PressedKey`

An enumeration of the key categories produced by `read_key`. The members are `Alpha`, `ArrowUp`, `ArrowDown`, `ArrowLeft`, `ArrowRight`, `Backspace`, `Enter`, `Escape`, `Delete`, and `Nop`. The `Alpha` category covers letters, digits, and a set of punctuation characters (`_`, `-`, `.`, `/`, `\`, and `:`). Bytes that do not match any recognized category are reported as `Nop`.

### Cursor functions

#### `move_cursor(row, col)`

Moves the terminal cursor to the given zero-based `(row, col)` position without writing any text. The function is useful for placing the cursor after a series of direct writes, or for positioning a visible cursor over an input field. Errors raised while writing the escape sequence are suppressed.

```python
move_cursor(0, 0)
```

#### `change_cursor(cursor_type)`

Changes the shape of the terminal cursor. The `cursor_type` argument is a member of the `CursorTypes` enumeration, which defines six shapes: `Default`, `Blinking_Block`, `Steady_Block`, `Blinking_Underline`, `Steady_Underline`, `Blinking_Bar`, and `Steady_Bar`. The effect persists until the next call to `change_cursor` or until the terminal is reset.

```python
from ansinout.screen import CursorTypes, change_cursor
change_cursor(CursorTypes.Steady_Bar)
```

### Direct drawing

#### `print_pos(row, col, s, fg=None, bg=None, bold=False)`

Writes the string `s` at the given zero-based `(row, col)` position. The function emits the ANSI cursor-positioning sequence followed by the styled text and flushes standard output. Coordinates are translated to the terminal's one-based addressing internally, so the caller should pass zero-based values. Styling arguments behave as on `TermText`: omitting `fg`, `bg`, and `bold` produces unstyled output.

```python
print_pos(2, 5, "status: ok", fg=Color.Green, bold=True)
```


### Colors

#### `Color` and `BgColor`

Enumerations of the sixteen standard ANSI color codes for foreground and background respectively. Each enum covers the eight base colors and their eight bright variants, along with a `Default` member that maps to the terminal's configured default. The two enums are kept distinct so that the type system can prevent a background color from being passed where a foreground color is expected. Values are accepted by `TermText`, `print_pos`, and any other function that takes `fg` or `bg` arguments.

```python
TermText("warning", fg=Color.BrightYellow, bg=BgColor.Black, bold=True)
```

#### Standard colors

| Name | ANSI (fg) | ANSI (bg) |
| --- | --- | --- |
| `Black` | 30 | 40 |
| `Red` | 31 | 41 |
| `Green` | 32 | 42 |
| `Yellow` | 33 | 43 |
| `Blue` | 34 | 44 |
| `Magenta` | 35 | 45 |
| `Cyan` | 36 | 46 |
| `White` | 37 | 47 |
| `Default` | 39 | 49 |

#### Bright colors

| Name | ANSI (fg) | ANSI (bg) |
| --- | --- | --- |
| `BrightBlack` | 90 | 100 |
| `Gray` | 90 | 100 |
| `BrightRed` | 91 | 101 |
| `BrightGreen` | 92 | 102 |
| `BrightYellow` | 93 | 103 |
| `BrightBlue` | 94 | 104 |
| `BrightMagenta` | 95 | 105 |
| `BrightCyan` | 96 | 106 |
| `BrightWhite` | 97 | 107 |

`Gray` is an alias for `BrightBlack`. The exact rendering of each color is determined by the terminal's color scheme.