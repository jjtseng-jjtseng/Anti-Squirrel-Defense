"""
Squirrel Dataset Quality Checker
---------------------------------
Displays each image with YOLO bounding boxes drawn on it.
  Right arrow  → YES (approve) — copies image + label to squirrel detection folder
  Left  arrow  → NO  (reject)  — skips
  ESC / Q      → quit
"""

import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import shutil

DATASET_DIR = r"C:\Users\tseng\Downloads\Squirrel.v1i.yolov12"
OUTPUT_DIR  = r"C:\Users\tseng\OneDrive\Desktop\squirrel detection"

CANVAS_W, CANVAS_H = 900, 650
BOX_COLOR   = "#00ff44"
BOX_WIDTH   = 3
LABEL_COLOR = "#00ff44"


def collect_images(dataset_dir):
    items = []
    for split in ["train", "valid", "test"]:
        img_dir = os.path.join(dataset_dir, split, "images")
        lbl_dir = os.path.join(dataset_dir, split, "labels")
        if not os.path.isdir(img_dir):
            continue
        for fname in sorted(os.listdir(img_dir)):
            if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            img_path = os.path.join(img_dir, fname)
            lbl_name = os.path.splitext(fname)[0] + ".txt"
            lbl_path = os.path.join(lbl_dir, lbl_name)
            if not os.path.isfile(lbl_path):
                lbl_path = None
            items.append((img_path, lbl_path, split))
    return items


def draw_boxes(img, lbl_path):
    draw = ImageDraw.Draw(img)
    if lbl_path is None:
        return
    W, H = img.size
    with open(lbl_path) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) != 5:
                continue
            _, cx, cy, bw, bh = map(float, parts)
            x1 = int((cx - bw / 2) * W)
            y1 = int((cy - bh / 2) * H)
            x2 = int((cx + bw / 2) * W)
            y2 = int((cy + bh / 2) * H)
            draw.rectangle([x1, y1, x2, y2], outline=BOX_COLOR, width=BOX_WIDTH)
            draw.rectangle([x1, y1 - 18, x1 + 72, y1], fill=BOX_COLOR)
            draw.text((x1 + 3, y1 - 16), "Squirrel", fill="#000000")


class QCApp:
    def __init__(self, root, images):
        self.root = root
        self.images = images
        self.idx = 0
        self.approved = 0
        self.rejected = 0

        os.makedirs(os.path.join(OUTPUT_DIR, "images"), exist_ok=True)
        os.makedirs(os.path.join(OUTPUT_DIR, "labels"), exist_ok=True)

        root.title("Squirrel QC Tool")
        root.configure(bg="#111111")
        root.resizable(False, False)

        # Top status bar
        self.status_var = tk.StringVar()
        tk.Label(root, textvariable=self.status_var, bg="#111111", fg="#ffffff",
                 font=("Consolas", 12, "bold")).pack(pady=(10, 2))

        # Canvas
        self.canvas = tk.Canvas(root, width=CANVAS_W, height=CANVAS_H, bg="#222222",
                                highlightthickness=0)
        self.canvas.pack(padx=12, pady=4)

        # Bottom bar
        bottom = tk.Frame(root, bg="#111111")
        bottom.pack(fill="x", padx=12, pady=(4, 10))

        tk.Label(bottom, text="← NO / Reject", bg="#111111", fg="#ff5555",
                 font=("Arial", 11, "bold")).pack(side="left", padx=20)
        self.score_var = tk.StringVar()
        tk.Label(bottom, textvariable=self.score_var, bg="#111111", fg="#888888",
                 font=("Arial", 10)).pack(side="left", expand=True)
        tk.Label(bottom, text="YES / Approve →", bg="#111111", fg="#55ff55",
                 font=("Arial", 11, "bold")).pack(side="right", padx=20)

        root.bind("<Right>", self.approve)
        root.bind("<Left>",  self.reject)
        root.bind("<Escape>", lambda e: root.destroy())
        root.bind("q", lambda e: root.destroy())

        self.show_current()

    def show_current(self):
        if self.idx >= len(self.images):
            self._finish_screen()
            return

        img_path, lbl_path, split = self.images[self.idx]
        total = len(self.images)

        self.status_var.set(
            f"Image {self.idx + 1} / {total}   [{split.upper()}]   "
            f"{os.path.basename(img_path)}"
        )
        self.score_var.set(
            f"✓ {self.approved} approved   ✗ {self.rejected} rejected   "
            f"· {total - self.idx - 1} remaining"
        )

        img = Image.open(img_path).convert("RGB")
        draw_boxes(img, lbl_path)

        # Fit to canvas while keeping aspect ratio
        img.thumbnail((CANVAS_W, CANVAS_H), Image.LANCZOS)
        self._photo = ImageTk.PhotoImage(img)

        self.canvas.delete("all")
        off_x = (CANVAS_W - img.width)  // 2
        off_y = (CANVAS_H - img.height) // 2
        self.canvas.create_image(off_x, off_y, anchor="nw", image=self._photo)

    def approve(self, _event=None):
        img_path, lbl_path, _split = self.images[self.idx]
        shutil.copy2(img_path, os.path.join(OUTPUT_DIR, "images", os.path.basename(img_path)))
        if lbl_path:
            shutil.copy2(lbl_path, os.path.join(OUTPUT_DIR, "labels", os.path.basename(lbl_path)))
        self.approved += 1
        self.idx += 1
        self.show_current()

    def reject(self, _event=None):
        self.rejected += 1
        self.idx += 1
        self.show_current()

    def _finish_screen(self):
        for w in self.root.winfo_children():
            w.destroy()
        self.root.configure(bg="#111111")
        msg = (
            f"\nAll done!\n\n"
            f"✓  {self.approved} images approved\n"
            f"✗  {self.rejected} images rejected\n\n"
            f"Approved images + labels saved to:\n"
            f"{OUTPUT_DIR}\\images\\\n"
            f"{OUTPUT_DIR}\\labels\\"
        )
        tk.Label(self.root, text=msg, bg="#111111", fg="#ffffff",
                 font=("Arial", 13), justify="center").pack(expand=True)
        tk.Button(self.root, text="  Close  ", command=self.root.destroy,
                  bg="#333333", fg="white", font=("Arial", 11),
                  relief="flat", cursor="hand2").pack(pady=20)


def main():
    images = collect_images(DATASET_DIR)
    if not images:
        print("No images found in dataset directory.")
        return

    print(f"Found {len(images)} images to review.")

    # Check Pillow is available
    try:
        from PIL import Image
    except ImportError:
        print("ERROR: Pillow is not installed. Run: pip install Pillow")
        return

    root = tk.Tk()
    QCApp(root, images)
    root.mainloop()


if __name__ == "__main__":
    main()
