# To-Do List App

A lightweight, cross-platform desktop To-Do List application built with **Python** and **Tkinter**. It features task creation, editing, completion toggling, single-level undo, persistent JSON storage, and a clean, minimal UI.

![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-green)

---

## Features

- ✅ Add, edit, complete, and delete tasks
- ↩️ Undo the last deletion with `Ctrl+Z` (or `Cmd+Z` on macOS)
- 💾 Automatic, crash-safe JSON persistence (atomic writes via temp file + `os.replace`)
- 🛡️ Corrupted save-file detection with automatic backup and recovery
- 🖱️ Scrollable task list with mouse wheel / trackpad support on all platforms
- 🎨 Clean UI with platform-appropriate fonts (Segoe UI on Windows, Helvetica Neue on macOS, Ubuntu on Linux)
- 📦 Packageable into a standalone executable with PyInstaller

---

## Project Structure

```
todo-app/
├── main.py        # Main application source file
├── README.md
└── assets/
    ├── icon.png              # Window/app icon
    ├── tick.png              # "Complete" icon
    ├── edit.png              # "Edit" icon
    ├── cross.png             # "Delete" icon

```

> **Note:** Icon assets (`tick.png`, `edit.png`, `cross.png`, `icon.png`) are sourced from [Flaticon.com](https://www.flaticon.com). If any icon is missing, the app falls back to unicode text/emoji symbols (✓, ✎, ✕) instead of crashing.

---

## Requirements

- Python **3.8+**
- [Pillow](https://pypi.org/project/Pillow/) (for icon loading)
- Tkinter (bundled with most Python installations — see platform notes below)

Install dependencies:

```bash
pip install Pillow pyinstaller
```

---

## Running from Source

1. Clone or download this repository.
2. Install dependencies.
3. Run:

```bash
python main.py
```

Task data is **not** stored next to the script — it's saved to a platform-specific user data directory (see [Data Storage Location](#data-storage-location) below), so your tasks persist even after rebuilding or moving the app.

---

## Data Storage Location

The app stores `tasks.json` in a standard per-OS application data folder:

| Platform | Location |
|----------|----------|
| Windows  | `%APPDATA%\TodoApp\tasks.json` |
| macOS    | `~/Library/Application Support/TodoApp/tasks.json` |
| Linux    | `~/.local/share/TodoApp/tasks.json` (or `$XDG_DATA_HOME/TodoApp/tasks.json` if set) |

If the save file becomes corrupted, the app automatically renames it to `tasks.json.corrupt_<timestamp>` and starts fresh, rather than losing data silently.

---

## Building a Standalone Executable with PyInstaller

PyInstaller bundles the Python interpreter, script, and dependencies into a single distributable executable so end users don't need Python installed.

Install PyInstaller first:

```bash
pip install pyinstaller
```

Build commands must be run **on the target OS** — PyInstaller does not cross-compile. To build for Windows, macOS, and Linux, you need to run the corresponding command on each platform (or use CI/virtual machines).

### 🪟 Windows

Open Command Prompt or PowerShell in the project folder:

```powershell
pyinstaller --noconfirm --onefile --windowed ^
  --icon=icon.png ^
  --add-data "assets/icon.png;." ^
  --add-data "assets/tick.png;." ^
  --add-data "assets/edit.png;." ^
  --add-data "assets/cross.png;." ^
  --name "TodoApp" ^
  main.py
```

- `--windowed` suppresses the console window (GUI-only app).
- `--onefile` produces a single `.exe`.
- The output binary will be at `dist\TodoApp.exe`.
- Note: `--icon` on Windows requires a `.ico` file for the taskbar/exe icon; convert `icon.png` to `icon.ico` first (e.g. with an online converter or Pillow) if you want a proper app icon — the in-app `iconphoto` call will still use the `.png` at runtime.

**Install & use:**
1. Run `dist\TodoApp.exe` directly, or copy it anywhere (e.g. Desktop, `C:\Program Files\TodoApp\`).
2. Optional: right-click → **Send to → Desktop (create shortcut)** for a launcher icon.
3. Double-click to launch. Windows Defender SmartScreen may warn on first run of an unsigned executable — click **More info → Run anyway**.

---

### 🐧 Linux

Ensure Tkinter is installed system-wide first (it's not always bundled with Python on Linux):

```bash
sudo apt install python3-tk       # Debian/Ubuntu
sudo dnf install python3-tkinter  # Fedora
sudo pacman -S tk                 # Arch
```

Then build:

```bash
pyinstaller --noconfirm --onefile --windowed \
  --add-data "assets/icon.png:." \
  --add-data "assets/tick.png:." \
  --add-data "assets/edit.png:." \
  --add-data "assets/cross.png:." \
  --name "TodoApp" \
  main.py
```

- Note the `:` separator in `--add-data` on Linux/macOS (Windows uses `;`).
- The output binary will be at `dist/TodoApp`.

**Install & use:**
1. Make it executable and move it into your PATH:
   ```bash
   chmod +x dist/TodoApp
   sudo mv dist/TodoApp /usr/local/bin/todo-app
   ```
2. Launch from a terminal with `todo-app`, or create a `.desktop` launcher:
   ```bash
   cat > ~/.local/share/applications/todo-app.desktop <<EOF
   [Desktop Entry]
   Name=To-Do List
   Exec=/usr/local/bin/todo-app
   Icon=/usr/local/bin/icon.png
   Type=Application
   Categories=Utility;
   EOF
   ```
3. The app should now appear in your application launcher/menu.

---

### 🍎 macOS

Build a standard onefile binary, or a proper `.app` bundle for a native feel.

**Onefile binary:**

```bash
pyinstaller --noconfirm --onefile --windowed \
  --add-data "assets/icon.png:." \
  --add-data "assets/tick.png:." \
  --add-data "assets/edit.png:." \
  --add-data "assets/cross.png:." \
  --name "TodoApp" \
  main.py
```

**Native `.app` bundle** (recommended for macOS, gives a proper Dock icon and Finder integration):

```bash
pyinstaller --noconfirm --windowed \
  --add-data "assets/icon.png:." \
  --add-data "assets/tick.png:." \
  --add-data "assets/edit.png:." \
  --add-data "assets/cross.png:." \
  --name "TodoApp" \
  main.py
```

(Omitting `--onefile` produces `dist/TodoApp.app` instead of a raw binary — `.app` bundles typically launch faster and behave more like native macOS apps.)

**Install & use:**
1. Move `dist/TodoApp.app` to `/Applications`:
   ```bash
   mv dist/TodoApp.app /Applications/
   ```
2. Since the app is unsigned/not notarized, the first launch will likely be blocked by Gatekeeper. Right-click (or Control-click) the app → **Open** → **Open** again in the confirmation dialog. This only needs to be done once.
3. Launch from Spotlight (`Cmd+Space`, type "TodoApp") or Launchpad going forward.

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Add task (when input field is focused) |
| `Ctrl+Z` / `Cmd+Z` | Undo last task deletion |
| `Enter` (in edit popup) | Save edited task |
| `Escape` (in edit popup) | Cancel edit |

---

## Troubleshooting

- **Icons not showing:** Confirm `tick.png`, `edit.png`, `cross.png`, and `icon.png` are in the assets folder (or bundled via `--add-data` in the PyInstaller build). The app falls back to unicode symbols if an icon fails to load.
- **"No module named tkinter" (Linux):** Install the `python3-tk` / `python3-tkinter` package for your distro (see Linux build section above).
- **App won't open on macOS:** This is Gatekeeper blocking an unsigned app — right-click → **Open** to bypass once.
- **Corrupted task data:** Check your user data directory (see [Data Storage Location](#data-storage-location)) for a `tasks.json.corrupt_<timestamp>` backup file.

---

## Credits

- **Author:** Akhnas Furqan
- **Icons:** Tick, Edit, Cross, and To-Do icons sourced via [Flaticon.com](https://www.flaticon.com)

## License

{blank}
