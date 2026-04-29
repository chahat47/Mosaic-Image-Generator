import sys
from sys import stdin


def read_int():
    return int(stdin.readline())

def read_arr():
    return list(map(int, stdin.readline().split()))

def read_str():
    return stdin.readline().strip()

def read_arr_str():
    return stdin.readline().strip().split()

def read_ints():
    return map(int,stdin.readline().split())


import os
import math
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import numpy as np



def load_tile_images(folder, tile_size):
    """Load and resize all images from a folder into tiles."""
    supported = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}
    tiles = []
    tile_colors = []

    paths = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if os.path.splitext(f)[1].lower() in supported
    ]
    if not paths:
        return [], []

    for path in paths:
        try:
            img = Image.open(path).convert("RGB")
            # Crop to square from center before resizing
            w, h = img.size
            side = min(w, h)
            left = (w - side) // 2
            top = (h - side) // 2
            img = img.crop((left, top, left + side, top + side))
            img = img.resize((tile_size, tile_size), Image.LANCZOS)
            avg_color = np.array(img).mean(axis=(0, 1))
            tiles.append(img)
            tile_colors.append(avg_color)
        except Exception:
            continue

    return tiles, np.array(tile_colors)


def best_tile_index(target_color, tile_colors):
    """Return index of tile whose average color is closest to target_color."""
    diffs = np.linalg.norm(tile_colors - target_color, axis=1)
    return int(np.argmin(diffs))


def build_mosaic(target_path, tile_folder, tile_size, grid_cols,
                 progress_cb=None, cancel_flag=None):
    """
    Build and return a PIL Image mosaic.
    progress_cb(pct: float) is called with 0-100 during processing.
    cancel_flag is a threading.Event; if set, abort early.
    """
    target = Image.open(target_path).convert("RGB")

    tiles, tile_colors = load_tile_images(tile_folder, tile_size)
    if not tiles:
        raise ValueError("No valid images found in the tile folder.")

    # Resize target so it fits exactly grid_cols tiles wide
    target_w = grid_cols * tile_size
    aspect = target.height / target.width
    target_h = int(target_w * aspect)
    target_h = max(tile_size, (target_h // tile_size) * tile_size)
    target = target.resize((target_w, target_h), Image.LANCZOS)

    grid_rows = target_h // tile_size
    mosaic = Image.new("RGB", (target_w, target_h))

    total = grid_rows * grid_cols
    done = 0

    for row in range(grid_rows):
        for col in range(grid_cols):
            if cancel_flag and cancel_flag.is_set():
                return None

            # Crop the region from the target
            x0, y0 = col * tile_size, row * tile_size
            region = target.crop((x0, y0, x0 + tile_size, y0 + tile_size))
            avg = np.array(region).mean(axis=(0, 1))

            idx = best_tile_index(avg, tile_colors)
            mosaic.paste(tiles[idx], (x0, y0))

            done += 1
            if progress_cb:
                progress_cb(done / total * 100)

    return mosaic


# ──────────────────────────────────────────────
# GUI
# ──────────────────────────────────────────────

BG       = "#0f0f13"
SURFACE  = "#1a1a22"
BORDER   = "#2e2e3e"
ACCENT   = "#7c6af7"
ACCENT2  = "#c084fc"
TEXT     = "#e8e6f0"
MUTED    = "#7a7890"
SUCCESS  = "#4ade80"
DANGER   = "#f87171"


class MosaicApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Photo Mosaic Generator")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(820, 600)

        self._target_path = tk.StringVar()
        self._tile_folder  = tk.StringVar()
        self._tile_size    = tk.IntVar(value=32)
        self._grid_cols    = tk.IntVar(value=60)
        self._output_path  = tk.StringVar()
        self._progress     = tk.DoubleVar(value=0)
        self._status       = tk.StringVar(value="Ready")

        self._cancel_flag  = threading.Event()
        self._result_image = None   # PIL image of last mosaic
        self._preview_ref  = None   # keep PhotoImage alive

        self._build_ui()

    # ── layout ────────────────────────────────

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        root = tk.Frame(self, bg=BG)
        root.grid(sticky="nsew", padx=20, pady=20)
        root.columnconfigure(1, weight=1)

        # ── Title
        title = tk.Label(root, text="✦ Photo Mosaic Generator",
                         font=("Georgia", 22, "bold"),
                         fg=ACCENT2, bg=BG)
        title.grid(row=0, column=0, columnspan=3, pady=(0, 18), sticky="w")

        # ── Left panel (inputs)
        left = tk.Frame(root, bg=SURFACE, bd=0, relief="flat",
                        highlightbackground=BORDER, highlightthickness=1)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 14))
        left.columnconfigure(1, weight=1)
        root.rowconfigure(1, weight=1)

        self._section(left, "INPUT", 0)
        self._file_row(left, "Target Image",  self._target_path, 1, file=True)
        self._file_row(left, "Tile Folder",   self._tile_folder,  2, file=False)

        self._section(left, "SETTINGS", 3)
        self._slider_row(left, "Tile size (px)", self._tile_size, 8, 128, 4)
        self._slider_row(left, "Grid columns",   self._grid_cols, 10, 200, 5)

        self._section(left, "OUTPUT", 6)
        self._file_row(left, "Save to", self._output_path, 7, save=True)

        # buttons
        btn_frame = tk.Frame(left, bg=SURFACE)
        btn_frame.grid(row=8, column=0, columnspan=2, pady=16, padx=14)

        self._btn_run = self._button(btn_frame, "▶  Generate Mosaic",
                                     self._start, ACCENT)
        self._btn_run.pack(side="left", padx=(0, 8))

        self._btn_cancel = self._button(btn_frame, "✕  Cancel",
                                        self._cancel, DANGER, state="disabled")
        self._btn_cancel.pack(side="left")

        # Progress
        prog_frame = tk.Frame(left, bg=SURFACE)
        prog_frame.grid(row=9, column=0, columnspan=2, sticky="ew", padx=14, pady=(0, 4))
        prog_frame.columnconfigure(0, weight=1)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Mosaic.Horizontal.TProgressbar",
                        troughcolor=BORDER, background=ACCENT,
                        bordercolor=BORDER, lightcolor=ACCENT, darkcolor=ACCENT)

        self._pbar = ttk.Progressbar(prog_frame, variable=self._progress,
                                     maximum=100, length=260,
                                     style="Mosaic.Horizontal.TProgressbar")
        self._pbar.grid(row=0, column=0, sticky="ew")

        tk.Label(left, textvariable=self._status, font=("Courier", 9),
                 fg=MUTED, bg=SURFACE, anchor="w")\
            .grid(row=10, column=0, columnspan=2, sticky="ew", padx=14, pady=(2, 14))

        # ── Right panel (preview)
        right = tk.Frame(root, bg=SURFACE, bd=0, relief="flat",
                         highlightbackground=BORDER, highlightthickness=1)
        right.grid(row=1, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        tk.Label(right, text="P R E V I E W", font=("Courier", 9, "bold"),
                 fg=MUTED, bg=SURFACE)\
            .grid(row=0, column=0, pady=(12, 4))

        self._canvas = tk.Canvas(right, bg="#0a0a10", bd=0,
                                 highlightthickness=0, width=480, height=400)
        self._canvas.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 8))

        self._btn_save_preview = self._button(right, "⬇  Save Image",
                                              self._save_result, ACCENT2,
                                              state="disabled")
        self._btn_save_preview.grid(row=2, column=0, pady=(0, 12))

        self._draw_placeholder()

    # ── widget helpers ─────────────────────────

    def _section(self, parent, label, row):
        f = tk.Frame(parent, bg=BORDER, height=1)
        f.grid(row=row, column=0, columnspan=2, sticky="ew",
               padx=14, pady=(14, 0))
        tk.Label(parent, text=label, font=("Courier", 8, "bold"),
                 fg=MUTED, bg=SURFACE)\
            .grid(row=row, column=0, columnspan=2, sticky="w", padx=16, pady=(6, 2))

    def _file_row(self, parent, label, var, row, file=False, save=False):
        tk.Label(parent, text=label, font=("Helvetica", 10),
                 fg=TEXT, bg=SURFACE, width=14, anchor="w")\
            .grid(row=row, column=0, sticky="w", padx=(14, 4), pady=4)

        entry = tk.Entry(parent, textvariable=var,
                         bg="#252530", fg=TEXT, insertbackground=TEXT,
                         relief="flat", font=("Courier", 9),
                         highlightbackground=BORDER, highlightthickness=1)
        entry.grid(row=row, column=1, sticky="ew", padx=(0, 6), pady=4)

        def browse():
            if save:
                p = filedialog.asksaveasfilename(
                    defaultextension=".jpg",
                    filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")])
            elif file:
                p = filedialog.askopenfilename(
                    filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.webp")])
            else:
                p = filedialog.askdirectory()
            if p:
                var.set(p)

        tk.Button(parent, text="…", command=browse,
                  bg=BORDER, fg=TEXT, relief="flat",
                  activebackground=ACCENT, activeforeground="white",
                  font=("Helvetica", 10), padx=6)\
            .grid(row=row, column=2, padx=(0, 14), pady=4)

    def _slider_row(self, parent, label, var, mn, mx, row):
        tk.Label(parent, text=label, font=("Helvetica", 10),
                 fg=TEXT, bg=SURFACE, width=14, anchor="w")\
            .grid(row=row, column=0, sticky="w", padx=(14, 4), pady=4)

        val_lbl = tk.Label(parent, textvariable=var, font=("Courier", 10),
                           fg=ACCENT2, bg=SURFACE, width=4)
        val_lbl.grid(row=row, column=2, padx=(0, 14))

        sl = tk.Scale(parent, from_=mn, to=mx, orient="horizontal",
                      variable=var, showvalue=False,
                      bg=SURFACE, fg=MUTED, troughcolor=BORDER,
                      activebackground=ACCENT, highlightthickness=0,
                      relief="flat", sliderlength=16)
        sl.grid(row=row, column=1, sticky="ew", padx=(0, 4), pady=4)

    def _button(self, parent, text, cmd, color, state="normal"):
        return tk.Button(parent, text=text, command=cmd,
                         bg=color, fg="white", relief="flat",
                         font=("Helvetica", 10, "bold"),
                         activebackground=ACCENT2, activeforeground="white",
                         padx=14, pady=7, cursor="hand2", state=state,
                         disabledforeground="#555")

    # ── preview ────────────────────────────────

    def _draw_placeholder(self):
        self._canvas.delete("all")
        w, h = 480, 400
        self._canvas.create_rectangle(0, 0, w, h, fill="#0a0a10", outline="")
        # subtle grid
        for x in range(0, w, 40):
            self._canvas.create_line(x, 0, x, h, fill="#141420")
        for y in range(0, h, 40):
            self._canvas.create_line(0, y, w, y, fill="#141420")
        self._canvas.create_text(w//2, h//2,
                                 text="Mosaic preview will appear here",
                                 font=("Georgia", 13, "italic"), fill=MUTED)

    def _show_preview(self, pil_img):
        cw = self._canvas.winfo_width()  or 480
        ch = self._canvas.winfo_height() or 400
        pil_img.thumbnail((cw, ch), Image.LANCZOS)
        photo = ImageTk.PhotoImage(pil_img)
        self._preview_ref = photo
        self._canvas.delete("all")
        self._canvas.create_image(cw//2, ch//2, anchor="center", image=photo)

    # ── run / cancel ───────────────────────────

    def _start(self):
        target = self._target_path.get().strip()
        folder = self._tile_folder.get().strip()

        if not target or not os.path.isfile(target):
            messagebox.showerror("Error", "Please select a valid target image.")
            return
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid tile folder.")
            return

        self._cancel_flag.clear()
        self._result_image = None
        self._progress.set(0)
        self._status.set("Loading tiles…")
        self._btn_run.config(state="disabled")
        self._btn_cancel.config(state="normal")
        self._btn_save_preview.config(state="disabled")

        thread = threading.Thread(target=self._run_worker, daemon=True)
        thread.start()

    def _run_worker(self):
        try:
            def on_progress(pct):
                self._progress.set(pct)
                self._status.set(f"Building mosaic… {pct:.0f}%")

            result = build_mosaic(
                target_path  = self._target_path.get().strip(),
                tile_folder  = self._tile_folder.get().strip(),
                tile_size    = self._tile_size.get(),
                grid_cols    = self._grid_cols.get(),
                progress_cb  = on_progress,
                cancel_flag  = self._cancel_flag,
            )

            if result is None:
                self.after(0, lambda: self._status.set("Cancelled."))
                return

            self._result_image = result

            out = self._output_path.get().strip()
            if out:
                result.save(out)
                self.after(0, lambda: self._status.set(f"Saved → {out}"))
            else:
                self.after(0, lambda: self._status.set("Done! (no output path set)"))

            self.after(0, lambda: self._show_preview(result.copy()))
            self.after(0, lambda: self._btn_save_preview.config(state="normal"))

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.after(0, lambda: self._status.set(f"Error: {e}"))
        finally:
            self.after(0, lambda: self._btn_run.config(state="normal"))
            self.after(0, lambda: self._btn_cancel.config(state="disabled"))

    def _cancel(self):
        self._cancel_flag.set()
        self._status.set("Cancelling…")

    def _save_result(self):
        if not self._result_image:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")])
        if path:
            self._result_image.save(path, quality=92)
            self._status.set(f"Saved → {path}")


if __name__ == "__main__":
    app = MosaicApp()
    app.mainloop()