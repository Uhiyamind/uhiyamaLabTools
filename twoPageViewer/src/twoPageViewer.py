import os
import math
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    dnd_enabled = True
except ImportError:
    dnd_enabled = False

# バージョン情報
__version__ = "1.0.0"

class ImageViewerApp:
    def __init__(self, root):
        self.root = root
        # タイトルにバージョン番号を表示
        self.root.title(f"TwoPage Viewer v{__version__}")
        self.root.geometry("800x600")

        # スタイル設定
        self.style = ttk.Style("flatly")

        # 読み方向 (True: 右綴じ, False: 左綴じ)
        self.read_right_to_left = True

        self.images = []
        self.current_page = 0
        self.total_pages = 0

        # リサイズ後の再描画デバウンス用ID
        self.resize_after_id = None
        self.resize_delay = 500  # ミリ秒

        # メインフレーム
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # タイトルラベル
        self.title_label = ttk.Label(self.main_frame, text="TwoPage Viewer", anchor=tk.CENTER, font=("Arial", 20, "bold"))
        self.title_label.pack(pady=(0,20))

        # 説明ラベル
        self.label = ttk.Label(self.main_frame, text="画像フォルダをここにドラッグ＆ドロップ\nまたは「フォルダを開く」で指定してください", 
                               anchor=tk.CENTER, font=("Arial", 12))
        self.label.pack(pady=10)

        # フォルダ選択ボタン
        self.select_btn = ttk.Button(self.main_frame, text="フォルダを開く", command=self.open_folder_dialog, bootstyle="outline-primary")
        self.select_btn.pack(pady=10)

        # D&Dサポート
        if dnd_enabled:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.drop_folder)

        # ビューアフレーム(後で作成)
        self.viewer_frame = None
        self.progress_bar = None
        self.page_label = None

        # リサイズイベントバインド
        self.root.bind("<Configure>", self.on_window_resize)

    def open_folder_dialog(self):
        folder = filedialog.askdirectory()
        if folder:
            # もしすでに表示中なら戻る
            if self.viewer_frame:
                self.back_to_main()
            self.prepare_viewer(folder)

    def drop_folder(self, event):
        path = event.data.strip("{}")
        if os.path.isdir(path):
            # もしすでに表示中なら戻る
            if self.viewer_frame:
                self.back_to_main()
            self.prepare_viewer(path)
        else:
            messagebox.showerror("エラー", "有効なフォルダをドロップしてください。")

    def prepare_viewer(self, folder):
        # 画像読み込み
        exts = [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
        files = [f for f in os.listdir(folder) if os.path.splitext(f)[1].lower() in exts]
        files.sort()
        if not files:
            messagebox.showerror("エラー", "このフォルダには画像がありません。")
            return

        self.images = [os.path.join(folder, f) for f in files]
        self.total_pages = math.ceil(len(self.images)/2)
        self.current_page = 0

        # メイン非表示
        self.main_frame.pack_forget()

        self.viewer_frame = ttk.Frame(self.root, padding=10)
        self.viewer_frame.pack(fill=tk.BOTH, expand=True)

        # ナビゲーション
        nav_frame = ttk.Frame(self.viewer_frame)
        nav_frame.pack(side=tk.TOP, fill=tk.X, pady=(0,5))

        self.back_to_main_btn = ttk.Button(nav_frame, text="戻る", command=self.back_to_main, bootstyle="secondary")
        self.back_to_main_btn.pack(side=tk.LEFT, padx=5)

        self.first_page_btn = ttk.Button(nav_frame, text="最初に戻る", command=self.go_first_page, bootstyle="secondary")
        self.first_page_btn.pack(side=tk.LEFT, padx=5)

        self.prev_btn = ttk.Button(nav_frame, text="前へ", command=self.prev_page, bootstyle="secondary")
        self.prev_btn.pack(side=tk.LEFT, padx=5)

        self.next_btn = ttk.Button(nav_frame, text="次へ", command=self.next_page, bootstyle="secondary")
        self.next_btn.pack(side=tk.LEFT, padx=5)

        # 読み方向トグル
        self.dir_var = tk.BooleanVar(value=self.read_right_to_left)
        self.dir_check = ttk.Checkbutton(nav_frame, text="右綴じ", variable=self.dir_var, command=self.toggle_direction, bootstyle="round-toggle")
        self.dir_check.pack(side=tk.LEFT, padx=5)

        # ファイル名表示トグル
        self.watermark_var = tk.BooleanVar(value=False)
        self.watermark_check = ttk.Checkbutton(nav_frame, text="ファイル名表示", variable=self.watermark_var, command=self.update_page, bootstyle="round-toggle")
        self.watermark_check.pack(side=tk.LEFT, padx=5)

        self.progress_bar = ttk.Progressbar(nav_frame, mode='determinate', maximum=self.total_pages, bootstyle="info-striped")
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10,5))

        self.page_label = ttk.Label(nav_frame, text="", font=("Arial", 10))
        self.page_label.pack(side=tk.LEFT, padx=5)

        # 画像表示領域
        self.image_frame = ttk.Frame(self.viewer_frame)
        self.image_frame.pack(fill=tk.BOTH, expand=True)

        self.image_frame.columnconfigure(0, weight=1)
        self.image_frame.columnconfigure(1, weight=1)
        self.image_frame.rowconfigure(0, weight=1)

        self.left_frame = ttk.Frame(self.image_frame)
        self.right_frame = ttk.Frame(self.image_frame)
        self.left_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        self.right_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)

        self.left_canvas = tk.Canvas(self.left_frame, bg="white")
        self.right_canvas = tk.Canvas(self.right_frame, bg="white")
        self.left_canvas.pack(fill=tk.BOTH, expand=True)
        self.right_canvas.pack(fill=tk.BOTH, expand=True)

        self.bind_keys()  # キーバインド

        self.update_page()

    def bind_keys(self):
        self.root.unbind("<MouseWheel>")
        self.root.unbind("<Button-4>")
        self.root.unbind("<Button-5>")
        self.root.unbind("<Left>")
        self.root.unbind("<Right>")

        self.root.bind("<MouseWheel>", self.on_mouse_wheel)
        self.root.bind("<Button-4>", self.on_mouse_wheel)
        self.root.bind("<Button-5>", self.on_mouse_wheel)

        if self.read_right_to_left:
            self.root.bind("<Left>", lambda e: self.next_page())   # ←で次へ
            self.root.bind("<Right>", lambda e: self.prev_page())  # →で前へ
        else:
            self.root.bind("<Left>", lambda e: self.prev_page())
            self.root.bind("<Right>", lambda e: self.next_page())

    def toggle_direction(self):
        self.read_right_to_left = self.dir_var.get()
        self.dir_check.configure(text="右綴じ" if self.read_right_to_left else "左綴じ")
        self.bind_keys()
        self.update_page()

    def on_mouse_wheel(self, event):
        if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            self.prev_page()
        elif event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
            self.next_page()

    def update_page(self):
        if not self.images:
            return

        idx_left = self.current_page * 2
        idx_right = idx_left + 1

        if self.read_right_to_left:
            right_img_path = self.images[idx_left] if idx_left < len(self.images) else None
            left_img_path = self.images[idx_right] if idx_right < len(self.images) else None
        else:
            left_img_path = self.images[idx_left] if idx_left < len(self.images) else None
            right_img_path = self.images[idx_right] if idx_right < len(self.images) else None

        self.left_canvas.update_idletasks()
        self.right_canvas.update_idletasks()

        left_w = self.left_canvas.winfo_width()
        left_h = self.left_canvas.winfo_height()
        right_w = self.right_canvas.winfo_width()
        right_h = self.right_canvas.winfo_height()

        if left_w < 1: left_w = 400
        if left_h < 1: left_h = 600
        if right_w < 1: right_w = 400
        if right_h < 1: right_h = 600

        def load_and_resize(pth, width, height):
            if pth is None:
                return None
            img = Image.open(pth).convert("RGB")
            img_ratio = img.width / img.height
            frame_ratio = width / height
            if img_ratio > frame_ratio:
                new_width = width
                new_height = int(new_width / img_ratio)
            else:
                new_height = height
                new_width = int(new_height * img_ratio)
            img = img.resize((new_width, new_height), Image.LANCZOS)

            if self.watermark_var.get() and pth is not None:
                draw = ImageDraw.Draw(img)
                filename = os.path.basename(pth)
                font = ImageFont.load_default()
                text_color = (128, 128, 128)
                margin = 10
                draw.text((margin, margin), filename, font=font, fill=text_color)

            return ImageTk.PhotoImage(img)

        left_img_obj = load_and_resize(left_img_path, left_w, left_h)
        right_img_obj = load_and_resize(right_img_path, right_w, right_h)

        self.left_canvas.delete("all")
        self.right_canvas.delete("all")

        if left_img_obj:
            self.left_canvas.create_image(left_w/2, left_h/2, image=left_img_obj, anchor="center")
        if right_img_obj:
            self.right_canvas.create_image(right_w/2, right_h/2, image=right_img_obj, anchor="center")

        self.left_canvas.image = left_img_obj
        self.right_canvas.image = right_img_obj

        self.progress_bar['value'] = self.current_page + 1
        self.page_label.configure(text=f"{self.current_page + 1}/{self.total_pages}")

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_page()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page()

    def go_first_page(self):
        self.current_page = 0
        self.update_page()

    def back_to_main(self):
        if self.viewer_frame:
            self.viewer_frame.pack_forget()
            self.viewer_frame.destroy()
            self.viewer_frame = None

        self.images = []
        self.current_page = 0
        self.total_pages = 0

        self.root.unbind("<MouseWheel>")
        self.root.unbind("<Button-4>")
        self.root.unbind("<Button-5>")
        self.root.unbind("<Left>")
        self.root.unbind("<Right>")

        self.main_frame.pack(fill=tk.BOTH, expand=True)

    def on_window_resize(self, event):
        if self.resize_after_id is not None:
            self.root.after_cancel(self.resize_after_id)
        
        if self.viewer_frame and self.images:
            self.resize_after_id = self.root.after(self.resize_delay, self.update_page)


if __name__ == "__main__":
    if dnd_enabled:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = ImageViewerApp(root)
    root.mainloop()
