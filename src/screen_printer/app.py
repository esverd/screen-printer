from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk

from .icons import make_icon
from .image_ops import (
    ImageSettings,
    contain_image,
    load_source_image,
    render_develop_image,
    render_preview_image,
)
from .session import DevelopSessionTimer, TripleClickDetector
from .sidecar import (
    DevelopSessionMetadata,
    source_and_settings_from_sidecar,
    update_develop_session,
    write_new_sidecar,
)

BG = "#11161d"
PANEL_BG = "#171f28"
BUTTON_BG = "#22303d"
BUTTON_ACTIVE = "#315a72"
BUTTON_HOVER = "#4f7f9b"
BUTTON_BORDER = "#9fe3ff"
BUTTON_FG = "#f2f5f7"
MUTED = "#9da9b3"
ACCENT = "#60c2ff"
WARNING = "#ffb86b"
PREVIEW_CACHE_SIZE = (1024, 1024)


class Tooltip:
    def __init__(self, widget: tk.Widget, text: str) -> None:
        self._widget = widget
        self._text = text
        self._after_id: str | None = None
        self._tip: tk.Toplevel | None = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event: object | None = None) -> None:
        self._hide()
        self._after_id = self._widget.after(500, self._show)

    def _show(self) -> None:
        self._after_id = None
        if self._tip is not None:
            return
        x = self._widget.winfo_rootx() + 4
        y = self._widget.winfo_rooty() - 30
        tip = tk.Toplevel(self._widget)
        tip.overrideredirect(True)
        tip.geometry(f"+{x}+{max(0, y)}")
        tip.configure(bg="#05070a")
        label = tk.Label(
            tip,
            text=self._text,
            bg="#05070a",
            fg=BUTTON_FG,
            padx=8,
            pady=4,
            font=("TkDefaultFont", 9),
        )
        label.pack()
        self._tip = tip

    def _hide(self, _event: object | None = None) -> None:
        if self._after_id is not None:
            self._widget.after_cancel(self._after_id)
            self._after_id = None
        if self._tip is not None:
            self._tip.destroy()
            self._tip = None


class ScreenPrinterApp:
    def __init__(self, root: tk.Tk, *, initial_geometry: str | None = None) -> None:
        self.root = root
        self.root.title("Screen Printer")
        self.root.configure(bg=BG)
        self.root.minsize(360, 240)
        if initial_geometry:
            self.root.geometry(initial_geometry)

        self.source_path: Path | None = None
        self.source_image: Image.Image | None = None
        self.preview_source_image: Image.Image | None = None
        self.settings = ImageSettings()
        self.screen_size = (self.root.winfo_screenwidth(), self.root.winfo_screenheight())
        self.last_sidecar_path: Path | None = None
        self.last_exposure_seconds: float | None = None
        self.active_develop_sidecar: Path | None = None
        self._active_develop_screen_size = self.screen_size

        self._preview_image: ImageTk.PhotoImage | None = None
        self._develop_image: ImageTk.PhotoImage | None = None
        self._preview_after_id: str | None = None
        self._slider_after_id: str | None = None
        self._active_slider: str | None = None
        self._develop_window: tk.Toplevel | None = None
        self._confirm_window: tk.Toplevel | None = None
        self._confirm_after_id: str | None = None
        self._cursor_trap_after_id: str | None = None
        self._timer = DevelopSessionTimer()
        self._click_detector = TripleClickDetector()
        self._button_icons: dict[str, ImageTk.PhotoImage] = {}
        self._button_keys: dict[tk.Button, str | None] = {}
        self._hovered_buttons: set[tk.Button] = set()

        self._build_ui()
        self.root.bind("<Configure>", self._schedule_preview, add="+")

    def _build_ui(self) -> None:
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.preview = tk.Canvas(
            self.root,
            bg="#05070a",
            bd=0,
            highlightthickness=0,
            width=1,
            height=1,
        )
        self.preview.grid(row=0, column=0, sticky="nsew")

        self.slider_frame = tk.Frame(self.root, bg=PANEL_BG, height=52)
        self.slider_frame.grid(row=1, column=0, sticky="ew")
        self.slider_frame.grid_remove()
        self.slider_frame.grid_columnconfigure(1, weight=1)

        self.slider_title = tk.Label(
            self.slider_frame,
            text="",
            bg=PANEL_BG,
            fg=BUTTON_FG,
            width=4,
            font=("TkDefaultFont", 15, "bold"),
        )
        self.slider_title.grid(row=0, column=0, padx=(4, 2), pady=6)

        self.slider_value = tk.DoubleVar(value=0.0)
        self.slider = tk.Scale(
            self.slider_frame,
            orient="horizontal",
            showvalue=False,
            resolution=1,
            bg=PANEL_BG,
            fg=BUTTON_FG,
            troughcolor="#0a0e12",
            activebackground=ACCENT,
            highlightthickness=0,
            command=self._on_slider_changed,
        )
        self.slider.grid(row=0, column=1, sticky="ew", padx=2, pady=5)

        self.slider_readout = tk.Label(
            self.slider_frame,
            text="0",
            bg=PANEL_BG,
            fg=BUTTON_FG,
            width=5,
            font=("TkDefaultFont", 12, "bold"),
        )
        self.slider_readout.grid(row=0, column=2, padx=2, pady=6)

        self.reset_button = self._button(
            self.slider_frame,
            "reset",
            "Reset slider",
            self._reset_active_slider,
            min_width=44,
        )
        self.reset_button.grid(row=0, column=3, padx=(2, 6), pady=5, sticky="nsew")

        self.meta = tk.Label(
            self.root,
            text="Load image",
            bg=BG,
            fg=MUTED,
            anchor="w",
            padx=8,
            pady=2,
            font=("TkDefaultFont", 9),
        )
        self.meta.grid(row=2, column=0, sticky="ew")

        self.controls = tk.Frame(self.root, bg=PANEL_BG, height=52)
        self.controls.grid(row=3, column=0, sticky="ew")
        for column in range(11):
            self.controls.grid_columnconfigure(column, weight=1, uniform="controls")

        self.buttons: dict[str, tk.Button] = {}
        specs = [
            ("open", "folder", "Open image or sidecar", self.open_image_dialog),
            ("bw", "grayscale", "Toggle grayscale", self.toggle_grayscale),
            ("exposure", "exposure", "Exposure", lambda: self.toggle_slider("exposure")),
            ("contrast", "contrast", "Contrast", lambda: self.toggle_slider("contrast")),
            ("blur", "blur", "Blur", lambda: self.toggle_slider("blur")),
            ("rotate", "rotate", "Rotate clockwise", self.rotate_clockwise),
            ("flip_h", "flip_h", "Flip horizontal", self.toggle_flip_horizontal),
            ("flip_v", "flip_v", "Flip vertical", self.toggle_flip_vertical),
            ("save", "save", "Save settings", self.save_settings),
            ("invert", "invert", "Invert", self.toggle_invert),
            ("develop", "camera", "Develop", self.enter_develop_mode),
        ]
        for column, (key, icon_name, tooltip, command) in enumerate(specs):
            button = self._button(self.controls, icon_name, tooltip, command, key=key)
            button.grid(row=0, column=column, padx=1, pady=4, sticky="nsew")
            self.buttons[key] = button

        self._update_button_states()

    def _button(
        self,
        parent: tk.Widget,
        icon_name: str,
        tooltip: str,
        command: object,
        *,
        min_width: int = 44,
        key: str | None = None,
    ) -> tk.Button:
        icon_key = f"{icon_name}:{BUTTON_FG}"
        icon = self._button_icons.get(icon_key)
        if icon is None:
            icon = ImageTk.PhotoImage(make_icon(icon_name, color=BUTTON_FG))
            self._button_icons[icon_key] = icon
        button = tk.Button(
            parent,
            image=icon,
            command=command,
            bg=BUTTON_BG,
            activebackground=BUTTON_ACTIVE,
            fg=BUTTON_FG,
            activeforeground=BUTTON_FG,
            relief="flat",
            bd=0,
            highlightbackground=BUTTON_BG,
            highlightcolor=BUTTON_BORDER,
            highlightthickness=2,
            font=("TkDefaultFont", 14, "bold"),
            padx=0,
            pady=0,
            takefocus=True,
        )
        button.configure(width=max(34, min_width - 8), height=42)
        self._button_keys[button] = key
        button.bind("<Enter>", lambda _event, item=button: self._set_button_hover(item, True), add="+")
        button.bind("<Leave>", lambda _event, item=button: self._set_button_hover(item, False), add="+")
        button.bind("<FocusIn>", lambda _event, item=button: self._set_button_hover(item, True), add="+")
        button.bind("<FocusOut>", lambda _event, item=button: self._set_button_hover(item, False), add="+")
        Tooltip(button, tooltip)
        return button

    def _set_button_hover(self, button: tk.Button, hovered: bool) -> None:
        if hovered:
            self._hovered_buttons.add(button)
        else:
            self._hovered_buttons.discard(button)
        self._update_button_states()

    def _style_button(self, button: tk.Button, *, active: bool = False) -> None:
        hovered = button in self._hovered_buttons
        button.configure(
            bg=BUTTON_HOVER if hovered else BUTTON_ACTIVE if active else BUTTON_BG,
            activebackground=BUTTON_HOVER,
            highlightbackground=BUTTON_BORDER if hovered else BUTTON_BG,
            highlightcolor=BUTTON_BORDER,
            relief="solid" if hovered else "flat",
        )

    def open_image_dialog(self) -> None:
        filename = filedialog.askopenfilename(
            title="Open image or sidecar",
            filetypes=[
                ("Images and sidecars", "*.jpg *.jpeg *.png *.json"),
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("Screen Printer sidecar", "*.json"),
                ("All files", "*.*"),
            ],
        )
        if filename:
            self.load_path(Path(filename))

    def load_path(self, path: Path) -> None:
        if path.suffix.lower() == ".json":
            self.load_sidecar(path)
        else:
            self.load_image(path)

    def load_sidecar(self, path: Path) -> None:
        try:
            source_path, settings = source_and_settings_from_sidecar(path)
            self.load_image(source_path, settings=settings, sidecar_path=path)
        except Exception as exc:  # pragma: no cover - GUI message wrapper
            messagebox.showerror("Open sidecar", str(exc))

    def load_image(
        self,
        path: Path,
        *,
        settings: ImageSettings | None = None,
        sidecar_path: Path | None = None,
    ) -> None:
        try:
            image = load_source_image(path)
        except Exception as exc:  # pragma: no cover - GUI message wrapper
            messagebox.showerror("Open image", str(exc))
            return
        self.source_path = path
        self.source_image = image
        self.preview_source_image = contain_image(image, PREVIEW_CACHE_SIZE)
        self.last_sidecar_path = sidecar_path
        self.last_exposure_seconds = None
        self.active_develop_sidecar = None
        self.settings = (settings or ImageSettings()).sanitized()
        self._active_slider = None
        self.slider_frame.grid_remove()
        self._update_button_states()
        self._update_meta()
        self._schedule_preview()

    def _replace_settings(self, **changes: object) -> None:
        payload = self.settings.to_dict()
        payload.update(changes)
        self.settings = ImageSettings.from_dict(payload)
        self._update_button_states()
        self._update_meta()
        self._schedule_preview()

    def toggle_grayscale(self) -> None:
        self._replace_settings(grayscale=not self.settings.grayscale)

    def toggle_invert(self) -> None:
        self._replace_settings(invert=not self.settings.invert)

    def rotate_clockwise(self) -> None:
        self._replace_settings(rotation_degrees=self.settings.rotation_degrees + 90)

    def toggle_flip_horizontal(self) -> None:
        self._replace_settings(flip_horizontal=not self.settings.flip_horizontal)

    def toggle_flip_vertical(self) -> None:
        self._replace_settings(flip_vertical=not self.settings.flip_vertical)

    def _update_button_states(self) -> None:
        active = {
            "bw": self.settings.grayscale,
            "invert": self.settings.invert,
            "flip_h": self.settings.flip_horizontal,
            "flip_v": self.settings.flip_vertical,
            "exposure": self._active_slider == "exposure",
            "contrast": self._active_slider == "contrast",
            "blur": self._active_slider == "blur",
        }
        for key, button in self.buttons.items():
            self._style_button(button, active=active.get(key, False))
        if hasattr(self, "reset_button"):
            self._style_button(self.reset_button)

    def toggle_slider(self, kind: str) -> None:
        if self._active_slider == kind and self.slider_frame.winfo_ismapped():
            self._active_slider = None
            self.slider_frame.grid_remove()
            self._update_button_states()
            return
        self.show_slider(kind)

    def show_slider(self, kind: str) -> None:
        self._active_slider = kind
        self.slider_frame.grid()
        if kind == "exposure":
            self.slider_title.configure(image=self._button_icons["exposure:" + BUTTON_FG], text="")
            self.slider.configure(from_=-100, to=300, resolution=1)
            self.slider.set(self.settings.exposure_percent)
        elif kind == "contrast":
            self.slider_title.configure(image=self._button_icons["contrast:" + BUTTON_FG], text="")
            self.slider.configure(from_=-100, to=300, resolution=1)
            self.slider.set(self.settings.contrast_percent)
        else:
            self.slider_title.configure(image=self._button_icons["blur:" + BUTTON_FG], text="")
            self.slider.configure(from_=0, to=20, resolution=0.1)
            self.slider.set(self.settings.blur_radius)
        self.slider_readout.configure(text=self._format_slider_value(float(self.slider.get())))
        self._update_button_states()

    def _reset_active_slider(self) -> None:
        if self._active_slider == "blur":
            self.slider.set(0.0)
        elif self._active_slider:
            self.slider.set(0)

    def _format_slider_value(self, value: float) -> str:
        if self._active_slider == "blur":
            return f"{value:.1f}"
        return str(int(round(value)))

    def _on_slider_changed(self, raw_value: str) -> None:
        value = float(raw_value)
        self.slider_readout.configure(text=self._format_slider_value(value))
        if self._slider_after_id is not None:
            self.root.after_cancel(self._slider_after_id)
        self._slider_after_id = self.root.after(35, self._apply_slider_value)

    def _apply_slider_value(self) -> None:
        self._slider_after_id = None
        value = float(self.slider.get())
        if self._active_slider == "exposure":
            self.settings = ImageSettings.from_dict(
                {**self.settings.to_dict(), "exposure_percent": int(round(value))}
            )
        elif self._active_slider == "contrast":
            self.settings = ImageSettings.from_dict(
                {**self.settings.to_dict(), "contrast_percent": int(round(value))}
            )
        elif self._active_slider == "blur":
            self.settings = ImageSettings.from_dict({**self.settings.to_dict(), "blur_radius": value})
        self._update_button_states()
        self._update_meta()
        self._schedule_preview()

    def _schedule_preview(self, _event: object | None = None) -> None:
        if self._preview_after_id is not None:
            self.root.after_cancel(self._preview_after_id)
        self._preview_after_id = self.root.after(50, self._render_preview)

    def _render_preview(self) -> None:
        self._preview_after_id = None
        self.preview.delete("all")
        if self.preview_source_image is None:
            return
        width = max(1, self.preview.winfo_width())
        height = max(1, self.preview.winfo_height())
        preview = render_preview_image(
            self.preview_source_image,
            self.settings,
            max_size=(width, height),
        )
        self._preview_image = ImageTk.PhotoImage(preview)
        self.preview.create_image(
            width // 2,
            height // 2,
            image=self._preview_image,
            anchor="center",
        )

    def _source_size(self) -> tuple[int, int]:
        if self.source_image is None:
            return (0, 0)
        return (self.source_image.width, self.source_image.height)

    def _refresh_screen_size(self) -> tuple[int, int]:
        self.screen_size = (self.root.winfo_screenwidth(), self.root.winfo_screenheight())
        return self.screen_size

    def save_settings(self) -> None:
        if self.source_path is None or self.source_image is None:
            self._set_status("No image loaded")
            return
        path = write_new_sidecar(
            source_image_path=self.source_path,
            source_image_size=self._source_size(),
            screen_size=self._refresh_screen_size(),
            settings=self.settings,
        )
        self.last_sidecar_path = path
        self._update_meta()

    def enter_develop_mode(self) -> None:
        if self.source_path is None or self.source_image is None:
            self._set_status("No image loaded")
            return
        if self._develop_window is not None:
            return

        screen_size = self._refresh_screen_size()
        self._active_develop_screen_size = screen_size
        started = datetime.now(timezone.utc)
        session = DevelopSessionMetadata(
            started_at_utc=started.isoformat(timespec="seconds").replace("+00:00", "Z"),
            rendered_screen_width=screen_size[0],
            rendered_screen_height=screen_size[1],
        )
        self.active_develop_sidecar = write_new_sidecar(
            source_image_path=self.source_path,
            source_image_size=self._source_size(),
            screen_size=screen_size,
            settings=self.settings,
            develop_session=session,
            created_at=started,
        )
        self.last_sidecar_path = self.active_develop_sidecar

        rendered = render_develop_image(
            self.source_image,
            self.settings,
            screen_size=screen_size,
        )
        self._develop_image = ImageTk.PhotoImage(rendered)

        window = tk.Toplevel(self.root)
        window.configure(bg="black", cursor="none")
        window.overrideredirect(True)
        window.attributes("-topmost", True)
        try:
            window.attributes("-fullscreen", True)
        except tk.TclError:
            pass
        window.geometry(f"{screen_size[0]}x{screen_size[1]}+0+0")
        label = tk.Label(window, image=self._develop_image, bg="black", bd=0, highlightthickness=0, cursor="none")
        label.pack(fill="both", expand=True)
        label.bind("<Button-1>", self._handle_develop_click, add="+")
        label.bind("<Escape>", self._handle_develop_escape, add="+")
        window.bind("<Escape>", self._handle_develop_escape, add="+")
        window.protocol("WM_DELETE_WINDOW", lambda: None)
        window.focus_force()
        self._develop_window = window
        self._timer.start()
        self._update_meta()

    def _handle_develop_escape(self, _event: object | None = None) -> None:
        self._show_confirm_dialog()

    def _handle_develop_click(self, event: tk.Event | None = None) -> None:
        if self._click_detector.register_click():
            pointer = None
            if event is not None:
                pointer = (int(event.x_root), int(event.y_root))
            self._show_confirm_dialog(pointer=pointer)

    def _show_confirm_dialog(self, *, pointer: tuple[int, int] | None = None) -> None:
        if self._develop_window is None:
            return
        if self._confirm_window is not None:
            self._confirm_window.lift()
            return

        dialog = tk.Toplevel(self._develop_window)
        dialog.configure(bg="#05070a", cursor="arrow")
        dialog.overrideredirect(True)
        dialog.attributes("-topmost", True)
        width, height = 160, 64
        screen_width, screen_height = self._active_develop_screen_size
        if pointer is None:
            left = max(0, screen_width - width - 8)
            top = max(0, screen_height - height - 8)
        else:
            left = max(0, min(screen_width - width, pointer[0] - (width // 2)))
            top = max(0, min(screen_height - height, pointer[1] - (height // 2)))
        dialog.geometry(f"{width}x{height}+{left}+{top}")
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_columnconfigure(1, weight=1)
        confirm = tk.Button(
            dialog,
            text="✓",
            command=lambda: self.exit_develop_mode(confirm=True),
            bg="#23533a",
            fg=BUTTON_FG,
            activebackground="#2f714f",
            activeforeground=BUTTON_FG,
            relief="flat",
            bd=0,
            highlightthickness=2,
            highlightbackground=BUTTON_BORDER,
            font=("TkDefaultFont", 20, "bold"),
        )
        cancel = tk.Button(
            dialog,
            text="×",
            command=self._cancel_confirm_dialog,
            bg="#4b2930",
            fg=BUTTON_FG,
            activebackground="#713d48",
            activeforeground=BUTTON_FG,
            relief="flat",
            bd=0,
            highlightthickness=2,
            highlightbackground=BUTTON_BORDER,
            font=("TkDefaultFont", 20, "bold"),
        )
        confirm.grid(row=0, column=0, sticky="nsew", padx=(6, 3), pady=6)
        cancel.grid(row=0, column=1, sticky="nsew", padx=(3, 6), pady=6)
        self._confirm_window = dialog
        self._confirm_after_id = dialog.after(30_000, self._cancel_confirm_dialog)
        dialog.update_idletasks()
        cancel.focus_set()
        self._warp_pointer_to_button(cancel)
        self._trap_cursor_in_confirm_dialog()

    def _warp_pointer_to_button(self, button: tk.Widget) -> None:
        root_x = button.winfo_rootx()
        root_y = button.winfo_rooty()
        local_x = root_x - button.winfo_toplevel().winfo_rootx() + (button.winfo_width() // 2)
        local_y = root_y - button.winfo_toplevel().winfo_rooty() + (button.winfo_height() // 2)
        try:
            button.winfo_toplevel().event_generate("<Motion>", warp=True, x=local_x, y=local_y)
        except tk.TclError:
            pass

    def _trap_cursor_in_confirm_dialog(self) -> None:
        dialog = self._confirm_window
        if dialog is None:
            self._cursor_trap_after_id = None
            return
        root_x = dialog.winfo_rootx()
        root_y = dialog.winfo_rooty()
        width = max(1, dialog.winfo_width())
        height = max(1, dialog.winfo_height())
        pointer_x, pointer_y = dialog.winfo_pointerxy()
        clamped_x = max(root_x + 4, min(root_x + width - 5, pointer_x))
        clamped_y = max(root_y + 4, min(root_y + height - 5, pointer_y))
        if (clamped_x, clamped_y) != (pointer_x, pointer_y):
            try:
                dialog.event_generate(
                    "<Motion>",
                    warp=True,
                    x=clamped_x - root_x,
                    y=clamped_y - root_y,
                )
            except tk.TclError:
                pass
        self._cursor_trap_after_id = dialog.after(40, self._trap_cursor_in_confirm_dialog)

    def _cancel_confirm_dialog(self) -> None:
        if self._cursor_trap_after_id is not None and self._confirm_window is not None:
            try:
                self._confirm_window.after_cancel(self._cursor_trap_after_id)
            except tk.TclError:
                pass
        self._cursor_trap_after_id = None
        if self._confirm_after_id is not None and self._confirm_window is not None:
            try:
                self._confirm_window.after_cancel(self._confirm_after_id)
            except tk.TclError:
                pass
        self._confirm_after_id = None
        if self._confirm_window is not None:
            self._confirm_window.destroy()
            self._confirm_window = None

    def exit_develop_mode(self, *, confirm: bool) -> None:
        if not confirm:
            self._cancel_confirm_dialog()
            return
        elapsed = self._timer.stop()
        self.last_exposure_seconds = elapsed
        sidecar_path = self.active_develop_sidecar
        if sidecar_path is not None:
            update_develop_session(
                sidecar_path=sidecar_path,
                ended_at=datetime.now(timezone.utc),
                elapsed_seconds=elapsed,
                exit_reason="confirmed",
                rendered_screen_size=self._active_develop_screen_size,
            )
            self.last_sidecar_path = sidecar_path
        self._cancel_confirm_dialog()
        if self._develop_window is not None:
            self._develop_window.destroy()
            self._develop_window = None
        self._develop_image = None
        self.active_develop_sidecar = None
        self.root.deiconify()
        self.root.focus_force()
        self._update_meta()
        self._schedule_preview()

    def _set_status(self, status: str) -> None:
        self.meta.configure(text=status, fg=WARNING)

    def _update_meta(self) -> None:
        if self.source_path is None or self.source_image is None:
            self.meta.configure(text="Load image", fg=MUTED)
            return
        image_name = self.source_path.name
        if len(image_name) > 22:
            image_name = f"{image_name[:10]}...{image_name[-9:]}"
        parts = [image_name, f"{self.source_image.width}x{self.source_image.height}"]
        if self.last_exposure_seconds is not None:
            parts.append(f"{self.last_exposure_seconds:.1f}s")
        parts.append(
            " ".join(
                [
                    f"E{self.settings.exposure_percent}",
                    f"C{self.settings.contrast_percent}",
                    f"B{self.settings.blur_radius:.1f}",
                    f"R{self.settings.rotation_degrees}",
                ]
            )
        )
        if self.last_sidecar_path is not None:
            parts.append("sidecar")
        self.meta.configure(text="  |  ".join(parts), fg=MUTED)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lightweight screen negative exposure app")
    parser.add_argument("--geometry", help="Initial editor window geometry, for example 480x320")
    parser.add_argument("--image", type=Path, help="Image to load on startup")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = tk.Tk()
    app = ScreenPrinterApp(root, initial_geometry=args.geometry)
    if args.image:
        root.after(100, lambda: app.load_path(args.image))
    root.mainloop()
    return 0
