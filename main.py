"""
To-Do List Application (Tkinter)
FILE: main.py
AUTHOR: AKHNAS FURQAN

Asset Attribution:
Icons sourced via Flaticon.com (Tick, Edit, Cross, To-Do Icon)
"""

import json
import os
import sys
import time
from tkinter import *
from tkinter import messagebox, ttk
from PIL import Image, ImageTk

# --- Utility Functions ---

def get_resource_path(relative_path):                                   # Checks if bunduled and correct directory for data file
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

#--- User Data Directory Management ---
def get_user_data_dir():                                                # Returns a platform-appropriate directory for storing user data files.
    app_name = "TodoApp"
    if sys.platform == "win32":                                         # Windows
        base_dir = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":                                      # macOS
        base_dir = os.path.expanduser("~/Library/Application Support")
    else:                                                               # Linux and other Unix-like systems
        base_dir = os.environ.get(
            "XDG_DATA_HOME", os.path.expanduser("~/.local/share")
        )

    data_dir = os.path.join(base_dir, app_name)
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


# UI Palette & Theme Constants
BG_COLOR = "#f8f9fa"
CARD_BG = "#ffffff"
PRIMARY_GREEN = "#4dae8a"
PRIMARY_GREEN_BG = "#eef8f4"
TEXT_COLOR = "#2c3e50"
COMPLETED_TEXT = "#a0aec0"
BLUE_ICON = "#3182ce"
RED_ICON = "#e53e3e"

#--- Platform-Specific Font Selection ---
if sys.platform.startswith("linux"):                                    # Linux
    FONT_FAMILY = "Ubuntu"
elif sys.platform == "darwin":                                          # macOS
    FONT_FAMILY = "Helvetica Neue"
else:
    FONT_FAMILY = "Segoe UI"                                            # Windows


#--- Main Application Class ---
class TodoApp:

    def __init__(self, root):                                           # Initializes the main application window and sets up UI components, state, and data persistence.
        self.root = root
        self.root.title("To-Do List")
        self.root.geometry("600x650")                                   # Set initial window size
        self.root.configure(bg=BG_COLOR)

        self.root.resizable(True, True)
        self.root.minsize(400, 450)                                     # Set minimum window size to prevent layout breakage

        # File paths
        self.data_dir = get_user_data_dir()
        self.json_path = os.path.join(self.data_dir, "tasks.json")      # Path for JSON persistence of tasks

        # Application state
        self.tasks = []                                                 # List of dicts: [{'text': str, 'completed': bool}]
        self.task_widgets = []                                          # Track active row UI elements
        self.undo_stack = []                                            # Single-task deletion undo history

        # Reference holder to prevent app icon garbage collection
        self.app_icon = None

        # Load image assets safely
        self.load_icon_assets()

        # Build interface and load persisted tasks
        self.setup_ui()
        self.bind_global_shortcuts()
        self.load_tasks_from_file()


    #--- Asset Loading ---
    def load_icon_assets(self):
        icon_size = (22, 22)

        def safe_load_image(filename):                                  # Safely loads and resizes an image asset, returning a PhotoImage or None if loading fails.
            path = get_resource_path(filename)
            if not os.path.exists(path):
                return None
            try:
                with Image.open(path) as img:
                    img.verify()                                        # Check for header/file corruption
                img = Image.open(path)
                img = img.resize(icon_size, Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Warning: Failed to load asset image '{filename}': {e}")
                return None

        # Load icons
        self.check_icon = safe_load_image("assets/tick.png")
        self.edit_icon = safe_load_image("assets/edit.png")
        self.cross_icon = safe_load_image("assets/cross.png")

    def bind_global_shortcuts(self):                                    # Bind universal keyboard shortcuts (Ctrl+Z etc)
        self.root.bind("<Control-z>", lambda e: self.undo_delete())
        self.root.bind("<Command-z>", lambda e: self.undo_delete())

    def setup_ui(self):                                                 # Sets up main UI Layout, titles, input area, scroll, list, and actions
        icon_path = get_resource_path("assets/icon.png")                       # Getting window Icon
        if os.path.exists(icon_path):
            try:
                self.app_icon = PhotoImage(file=icon_path)
                self.root.iconphoto(True, self.app_icon)
            except Exception as e:
                print(f"Warning: Could not set application icon: {e}")

        title_label = Label(                                            # Title Header
            self.root,
            text="TO DO LIST",
            font=(FONT_FAMILY, 22, "bold"),
            bg=BG_COLOR,
            fg=TEXT_COLOR,
        )
        title_label.pack(pady=(25, 15))

        # Top Task Input Area
        input_frame = Frame(self.root, bg=BG_COLOR, highlightthickness=0)
        input_frame.pack(fill=X, padx=40, pady=(0, 20))

        border_frame = Frame(
            input_frame,
            bg="#ffffff",
            highlightthickness=0,
            bd=1,
        )
        border_frame.pack(fill=X, ipady=3)

        self.task_entry = Entry(                                        # Input field
            border_frame,
            font=(FONT_FAMILY, 12),
            bg="#ffffff",
            fg="#9ca3af",
            relief=FLAT,
            highlightthickness=0,
        )
        self.task_entry.insert(0, "To-do...")
        self.task_entry.pack(side=LEFT, fill=BOTH, expand=True, padx=12, pady=5)

        #--- Entry Placeholder Behavior ---
        self.task_entry.bind("<FocusIn>", self.on_entry_focus_in)
        self.task_entry.bind("<FocusOut>", self.on_entry_focus_out)
        self.task_entry.bind("<Return>", lambda e: self.add_task())

        add_btn = Button(                                               # Add Task Button
            border_frame,
            text="Add Item",
            font=(FONT_FAMILY, 11),
            fg=PRIMARY_GREEN,
            bg="#ffffff",
            activebackground=PRIMARY_GREEN_BG,
            activeforeground=PRIMARY_GREEN,
            bd=0,
            cursor="hand2",
            command=self.add_task,
            padx=15,
            highlightthickness=0,
        )
        add_btn.pack(side=RIGHT, fill=Y)

        # Scrollable Task Container
        list_container = Frame(self.root, bg=BG_COLOR)
        list_container.pack(fill=BOTH, expand=True, padx=40, pady=10)

        style = ttk.Style()                                             # Styling the scrollbar
        style.configure(
            "Vertical.TScrollbar",
            gripcount=0,
            background=PRIMARY_GREEN_BG,
            darkcolor=PRIMARY_GREEN_BG,
            lightcolor=PRIMARY_GREEN_BG,
            troughcolor=BG_COLOR,
            bordercolor=BG_COLOR,
            arrowcolor=PRIMARY_GREEN,
        )

        #--- Scrollable Canvas Setup ---
        self.canvas = Canvas(list_container, bg=BG_COLOR, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(                                 #scrollbar for the task list
            list_container, orient=VERTICAL, command=self.canvas.yview
        )

        self.scrollable_frame = Frame(self.canvas, bg=BG_COLOR)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            ),
        )

        self.canvas_window = self.canvas.create_window(                 # Window to hold the items
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(
                self.canvas_window, width=e.width                       #canvas frame resizeable and wrapping
            ),
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        # Hover-based mouse wheel event binding
        list_container.bind("<Enter>", self._bind_mousewheel)
        list_container.bind("<Leave>", self._unbind_mousewheel)

        # Bottom Actions Frame
        bottom_frame = Frame(self.root, bg=BG_COLOR)
        bottom_frame.pack(fill=X, pady=20)

        clear_btn = Button(                                             # Clear All Button
            bottom_frame,
            text="Clear Items",
            font=(FONT_FAMILY, 11),
            fg=PRIMARY_GREEN,
            bg=BG_COLOR,
            activebackground=PRIMARY_GREEN_BG,
            activeforeground=PRIMARY_GREEN,
            bd=0,
            relief=SOLID,
            highlightbackground="#a3e6cd",
            cursor="hand2",
            command=self.clear_list,
            padx=20,
            pady=4,
            highlightthickness=0,
        )
        clear_btn.pack()

    # --- Mousewheel Event Handling ---
    def _bind_mousewheel(self, event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, event=None):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        """Cross-platform scroll step calculation."""
        if sys.platform == "darwin":                                    # macOS trackpad handling done on sugestion by forums
            self.canvas.yview_scroll(int(-1 * event.delta), "units")
        elif event.num == 4:                                            # Linux scroll up (scroll did not work without separate handling)
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:                                            # Linux scroll down (scroll did not work without separate handling)
            self.canvas.yview_scroll(1, "units")
        else:                                                           # Windows mouse handling for redundancy
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # --- Entry Placeholder Logic ---
    def on_entry_focus_in(self, event):
        if self.task_entry.get() == "To-do...":
            self.task_entry.delete(0, END)
            self.task_entry.config(fg=TEXT_COLOR)

    def on_entry_focus_out(self, event):
        if not self.task_entry.get().strip():
            self.task_entry.insert(0, "To-do...")
            self.task_entry.config(fg="#9ca3af")

    # --- Task List Rendering & Manipulations ---
    def create_task_row(self, index, task):                             # Task UI item with auto-wrapping of text
        row_frame = Frame(self.scrollable_frame, bg=BG_COLOR)
        row_frame.pack(fill=X, expand=True, pady=8)

        text_style = (                                                  
            (FONT_FAMILY, 13, "overstrike")
            if task["completed"]
            else (FONT_FAMILY, 13)
        )
        text_color = COMPLETED_TEXT if task["completed"] else TEXT_COLOR

        task_lbl = Label(
            row_frame,
            text=task["text"],
            font=text_style,
            fg=text_color,
            bg=BG_COLOR,
            anchor="w",
            justify=LEFT,
        )
        task_lbl.pack(side=LEFT, fill=X, expand=True)

        def update_label_wrap(event):                                   # Dynamic wrap margin calculation based on width minus button space
            new_wrap = max(event.width - 110, 100)
            task_lbl.config(wraplength=new_wrap)

        row_frame.bind("<Configure>", update_label_wrap)

        actions_frame = Frame(row_frame, bg=BG_COLOR)
        actions_frame.pack(side=RIGHT)

        check_btn = Button(                                             # task done button
            actions_frame,
            image=self.check_icon if self.check_icon else None,
            text="✓" if not self.check_icon else "",                    # fallback icon fail
            font=(FONT_FAMILY, 12, "bold"),
            fg=PRIMARY_GREEN if task["completed"] else "#a0aec0",
            bg=BG_COLOR,
            activebackground=BG_COLOR,
            bd=0,
            cursor="hand2",
            command=lambda i=index: self.toggle_task(i),
            highlightthickness=0,
        )
        check_btn.pack(side=LEFT, padx=3)

        edit_btn = Button(                                              # edit task button
            actions_frame,
            image=self.edit_icon if self.edit_icon else None,
            text="✎" if not self.edit_icon else "",                     # fallback icon fail
            font=(FONT_FAMILY, 12),
            fg=BLUE_ICON,
            bg=BG_COLOR,
            activebackground=BG_COLOR,
            bd=0,
            cursor="hand2",
            command=lambda i=index: self.edit_task(i),
            highlightthickness=0,
        )
        edit_btn.pack(side=LEFT, padx=3)

        delete_btn = Button(                                            # delete task button
            actions_frame,
            image=self.cross_icon if self.cross_icon else None,
            text="✕" if not self.cross_icon else "",                    # fallback icon fail
            font=(FONT_FAMILY, 12, "bold"),
            fg=RED_ICON,
            bg=BG_COLOR,
            activebackground=BG_COLOR,
            bd=0,
            cursor="hand2",
            command=lambda i=index: self.delete_task(i),
            highlightthickness=0,
        )
        delete_btn.pack(side=LEFT, padx=3)

        return {
            "frame": row_frame,
            "label": task_lbl,
            "check_btn": check_btn,
            "edit_btn": edit_btn,
            "del_btn": delete_btn,
        }

    def update_button_commands(self):                                   # rebuilds button commands after task deletion to ensure correct indexing
        for idx, w in enumerate(self.task_widgets):
            w["check_btn"].config(command=lambda i=idx: self.toggle_task(i))
            w["edit_btn"].config(command=lambda i=idx: self.edit_task(i))
            w["del_btn"].config(command=lambda i=idx: self.delete_task(i))

    def render_tasks(self):                                             # builds task list
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.task_widgets.clear()

        for index, task in enumerate(self.tasks):
            w = self.create_task_row(index, task)
            self.task_widgets.append(w)

    def add_task(self):                                                 # add task logic
        text = self.task_entry.get().strip()
        if text and text != "To-do...":
            new_task = {"text": text, "completed": False}
            self.tasks.append(new_task)
            self.task_entry.delete(0, END)

            index = len(self.tasks) - 1
            w = self.create_task_row(index, new_task)
            self.task_widgets.append(w)

            self.save_tasks_to_file()
        else:
            messagebox.showwarning("Add Item", "Task text cannot be empty.")    # check if empty attempt to add

    def toggle_task(self, index):                                               # task completion toggle logic
        task = self.tasks[index]
        task["completed"] = not task["completed"]

        text_style = (
            (FONT_FAMILY, 13, "overstrike")                                     # "strikethrough" for completed tasks
            if task["completed"]
            else (FONT_FAMILY, 13)
        )
        text_color = COMPLETED_TEXT if task["completed"] else TEXT_COLOR

        w = self.task_widgets[index]
        w["label"].config(font=text_style, fg=text_color)
        w["check_btn"].config(
            fg=PRIMARY_GREEN if task["completed"] else "#a0aec0"
        )

        self.save_tasks_to_file()

    def edit_task(self, index):                                                 # edit task logic
        current_text = self.tasks[index]["text"]

        popup = Toplevel(self.root)                                             # toplevel window for editing task
        popup.title("Edit Task")
        popup.geometry("320x130")
        popup.configure(bg=BG_COLOR)
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        entry_var = StringVar(value=current_text)
        entry = Entry(                                                          # entry field for top level window
            popup,
            textvariable=entry_var,
            font=(FONT_FAMILY, 11),
            width=30,
            bd=1,
            relief=SOLID,
        )
        entry.pack(padx=15, pady=(20, 10))
        entry.focus_set()
        entry.select_range(0, END)

        def save_and_close():                                                   # saves task and closes toplevel window
            new_text = entry_var.get().strip()
            if new_text:
                self.tasks[index]["text"] = new_text
                self.task_widgets[index]["label"].config(text=new_text)
                self.save_tasks_to_file()
                popup.destroy()
            else:
                messagebox.showwarning("Edit Item", "Task text cannot be empty.")   # checks if empty attempt to edit

        # Keybindings for edit modal
        popup.bind("<Return>", lambda e: save_and_close())
        popup.bind("<KP_Enter>", lambda e: save_and_close())
        popup.bind("<Escape>", lambda e: popup.destroy())

        btn_frame = Frame(popup, bg=BG_COLOR)
        btn_frame.pack(pady=5)

        ok_btn = Button(                                                        # ok button for toplevel
            btn_frame,
            text="OK",
            width=8,
            bg=PRIMARY_GREEN,
            fg="white",
            bd=0,
            command=save_and_close,
        )
        ok_btn.pack(side=LEFT, padx=5)

        cancel_btn = Button(                                                    # cancel button for toplevel
            btn_frame, text="Cancel", width=8, command=popup.destroy
        )
        cancel_btn.pack(side=LEFT, padx=5)

    def delete_task(self, index):                                               # delete task logic
        deleted_task = self.tasks.pop(index)
        self.undo_stack.append((index, deleted_task))                           # pushes deleted tasks to undo stack for undo

        w = self.task_widgets.pop(index)
        w["frame"].destroy()

        self.update_button_commands()
        self.save_tasks_to_file()

    def undo_delete(self):                                                      # undo delete logic
        if not self.undo_stack:
            return

        index, restored_task = self.undo_stack.pop()
        # Handle cases where list size shrunk past the original position
        index = min(index, len(self.tasks))
        self.tasks.insert(index, restored_task)

        self.render_tasks()
        self.save_tasks_to_file()

    def clear_list(self):                                                       # clear all tasks logic
        if not self.tasks:
            return
        if messagebox.askyesno(                                                 # user confirmation
            "Clear List", "Are you sure you want to clear all tasks?"
        ):
            self.tasks.clear()
            self.undo_stack.clear()
            self.render_tasks()
            self.save_tasks_to_file()

    # --- Persistence & Data Integrity ---
    
    def validate_schema(self, data):                                            # validates JSON schema to prevent runtime crash from manually edited or corrupted JSON files
        if not isinstance(data, list):
            return False
        for item in data:
            if not isinstance(item, dict):
                return False
            if "text" not in item or "completed" not in item:
                return False
            if not isinstance(item["text"], str) or not isinstance(
                item["completed"], bool
            ):
                return False
        return True

    def save_tasks_to_file(self):                                               # tempsave to prevent data loss on write failure
        temp_path = f"{self.json_path}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as file:
                json.dump(self.tasks, file, ensure_ascii=False, indent=2)
            os.replace(temp_path, self.json_path)                               # atomic file save replacing the origial file after validation of temp file
        except Exception as e:
            messagebox.showerror(
                "Save Error", f"Failed to save task data safely:\n{e}"
            )
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def load_tasks_from_file(self):                                             # loads tasks from file
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, "r", encoding="utf-8") as file:
                    data = json.load(file)

                if self.validate_schema(data):
                    self.tasks = data
                else:
                    raise ValueError("JSON content violates schema format.")

            except Exception as e:                                              # Backup corrupted file with timestamp
                corrupt_backup = (
                    f"{self.json_path}.corrupt_{int(time.time())}"
                )
                try:
                    os.rename(self.json_path, corrupt_backup)
                    err_msg = (
                        f"Your task file was corrupted and backed up to:\n"
                        f"{os.path.basename(corrupt_backup)}\n\n"
                        f"Error detail: {e}"
                    )
                except Exception:
                    err_msg = f"Task file is corrupted:\n{e}"

                messagebox.showerror("Corrupted File Error", err_msg)
                self.tasks = []

        self.render_tasks()

# main start block
if __name__ == "__main__":
    root = Tk()
    app = TodoApp(root)
    root.mainloop()
