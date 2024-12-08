import os
import datetime
import re
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinterdnd2 import DND_FILES, TkinterDnD

def natural_sort_key(s: str):
    """文字列を自然順（数値部分は数値としてソート）で並べるためのキー生成関数。"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

class ImageRenameApp(TkinterDnD.Tk):
    """
    ファイルをドラッグ＆ドロップし、指定したテンプレートやモードで一括リネームを行うGUIアプリ。
    対応拡張子を持つ画像、動画、音声ファイルの名前を連番付きなどで変換可能。
    """

    def __init__(self):
        super().__init__()
        self.title("MultiFileRename")
        self.geometry("900x600")

        # テーマ・スタイル設定
        self.style = tb.Style(theme="cosmo")
        self.configure(background=self.style.colors.bg)

        # DnD対応
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.drop_files)

        # 状態変数
        self.file_paths = []
        self.has_images = False
        self.sort_states = {"original": True, "converted": True}

        # モード・テンプレート関連変数
        self.mode_var = tk.StringVar(value="serial_only")
        self.template_var = tk.StringVar(value="{filename}_{date:%Y%m%d}_{num}")
        self.start_number_var = tk.IntVar(value=1)

        # 対応拡張子セット
        self.supported_exts = {
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tga", ".tif", ".tiff", ".psd",
            ".mp4", ".mov", ".avi", ".mkv", ".webm", ".wmv", ".flv", ".f4v", ".m4v",
            ".ogg", ".mp3", ".wav", ".webp", ".svg"
        }

        self.create_widgets()
        self.bind_events()

    def create_widgets(self):
        """GUIウィジェットの生成と配置を行うメソッド。"""
        main_frame = tb.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ツリービュー: 元名、矢印、変換後名
        self.tree = tb.Treeview(main_frame, columns=("original", "arrow", "converted"), show="headings", bootstyle=DEFAULT)
        self.tree.heading("original", text="元ファイル名", command=lambda: self.sort_by("original"))
        self.tree.heading("arrow", text="→")
        self.tree.heading("converted", text="変換後ファイル名(プレビュー)")
        self.tree.column("original", width=300, anchor="w")
        self.tree.column("arrow", width=50, anchor="center")
        self.tree.column("converted", width=450, anchor="w")

        vsb = tb.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        vsb.pack(fill=tk.Y, side=tk.RIGHT)

        # オプションフレーム（技術者向け）
        self.option_frame = tb.Labelframe(self, text="カスタムオプション (技術者向け)", padding=10)

        tb.Label(self.option_frame, text="ファイル名テンプレート:", anchor="e").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        template_entry = tb.Entry(self.option_frame, textvariable=self.template_var, width=60)
        template_entry.grid(row=0, column=1, columnspan=3, sticky="w", padx=5, pady=5)

        def reset_template():
            self.template_var.set("{filename}_{date:%Y%m%d}_{num}")
        tb.Button(self.option_frame, text="初期化", command=reset_template, bootstyle="outline").grid(row=0, column=4, sticky="w", padx=5, pady=5)

        placeholder_examples = (
            "{filename} -> 元ファイル名（拡張子なし）\n"
            "{num} または {num:03d} -> 連番（未指定なら'1','2','3'...）\n"
            "{date} または {date:%Y-%m-%d} -> 日付（:以降はstrftimeフォーマット）\n\n"
            "例:\n"
            "{filename}_{num} -> '元ファイル名_1.jpg'\n"
            "{filename}_{num:03d} -> '元ファイル名_001.jpg'\n"
            "{date:%Y%m%d}_{filename}_{num} -> '20241231_元ファイル名_1.jpg'\n"
            "{date:%Y-%m-%d}_{filename}_{num} -> '2024-12-31_元ファイル名_1.jpg'\n"
            "固定文字列も直接指定可 (例: MyProject_{filename}_{num:03d})"
        )
        example_label = tb.Label(self.option_frame, text=placeholder_examples, anchor="w", justify="left", bootstyle="secondary")
        example_label.grid(row=1, column=0, columnspan=5, sticky="w", padx=5, pady=5)

        tb.Label(self.option_frame, text="連番開始番号:", anchor="e").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        tb.Entry(self.option_frame, textvariable=self.start_number_var, width=5).grid(row=2, column=1, sticky="w", padx=5, pady=5)

        # モード切替ボタンフレーム
        mode_frame = tb.Frame(self, padding=10)
        mode_frame.pack(side=tk.BOTTOM, fill=tk.X)

        btn_style = {"bootstyle": "outline", "padding": 10}

        tb.Button(mode_frame, text="連番化のみ", command=lambda: self.set_mode("serial_only"), **btn_style).pack(side=tk.LEFT, padx=5)
        tb.Button(mode_frame, text="連番+ファイル名", command=lambda: self.set_mode("serial_prefix"), **btn_style).pack(side=tk.LEFT, padx=5)
        tb.Button(mode_frame, text="ファイル名+連番", command=lambda: self.set_mode("serial_suffix"), **btn_style).pack(side=tk.LEFT, padx=5)
        tb.Button(mode_frame, text="カスタム", command=lambda: self.set_mode("custom"), **btn_style).pack(side=tk.LEFT, padx=5)

        tb.Button(mode_frame, text="クリア", command=self.clear_list, bootstyle="warning", padding=10).pack(side=tk.LEFT, padx=5)

        execute_button = tb.Button(mode_frame, text="実行", bootstyle="primary", command=self.rename_files, padding=(20, 10))
        execute_button.pack(side=tk.RIGHT, padx=5)

        hint_label = tb.Label(
            self,
            text=(
                "※ 画像・動画・音声ファイルおよびwebp,svgをここにドラッグ＆ドロップして追加できます\n"
                "Deleteキーで選択項目削除、クリアボタンで全削除可能です。"
            ),
            bootstyle="light"
        )
        hint_label.pack(side=tk.BOTTOM, pady=5)

    def bind_events(self):
        """イベントバインドを行うメソッド。"""
        self.tree.bind("<Delete>", self.delete_selected_items)
        # テンプレートや連番開始番号が変更されたらプレビュー更新
        self.template_var.trace_add("write", lambda *args: self.update_tree_preview())
        self.start_number_var.trace_add("write", lambda *args: self.update_tree_preview())

    def set_mode(self, mode: str):
        """
        リネームモードを設定する。
        modeが'custom'の場合はカスタムオプションフレームを表示し、それ以外なら非表示にする。
        """
        self.mode_var.set(mode)
        if mode == "custom":
            self.option_frame.pack(fill=tk.X, pady=10, padx=10, side=tk.BOTTOM)
        else:
            self.option_frame.pack_forget()
        self.update_tree_preview()

    def drop_files(self, event):
        """ファイルをドロップした際に対応拡張子ならリストへ追加し、表示を更新。"""
        files = self.tk.splitlist(event.data)
        added = False
        for file_path in files:
            ext = os.path.splitext(file_path)[1].lower()
            if ext in self.supported_exts:
                self.file_paths.append(file_path)
                added = True
        self.update_tree_preview()

        self.sort_states["original"] = True
        self.sort_by("original")

        if added and not self.has_images:
            self.has_images = True
            # ヘッダテキストを変更する例（不要なら削除可能）
            new_text = "元ファイル名 (クリックでソート)"
            self.tree.heading("original", text=new_text, command=lambda: self.sort_by("original"))

    def sort_by(self, column: str):
        """ツリービューを指定カラムでソートする。"""
        if not self.file_paths:
            return
        ascending = self.sort_states[column]

        if column == "original":
            # 元ファイル名でソート
            self.file_paths.sort(key=lambda p: natural_sort_key(os.path.basename(p)), reverse=not ascending)
        elif column == "converted":
            # 変換後ファイル名でソート
            converted_names = self.generate_preview_names()
            combined = list(zip(self.file_paths, converted_names))
            combined.sort(key=lambda x: natural_sort_key(x[1]), reverse=not ascending)
            self.file_paths = [c[0] for c in combined]

        self.sort_states[column] = not ascending
        self.update_tree_preview()

    def update_tree_preview(self, *args):
        """ツリービューを現在のファイルリストと設定でプレビューを更新。"""
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        converted_names = self.generate_preview_names()
        for original_path, converted in zip(self.file_paths, converted_names):
            filename = os.path.basename(original_path)
            self.tree.insert("", "end", values=(filename, "→", converted))

    def generate_preview_names(self):
        """
        現在のファイルリストに対して、設定されたモード・テンプレートを用いて
        プレビュー用の変換後ファイル名リストを生成する。
        """
        converted_names = []
        mode = self.mode_var.get()
        start_num = self.start_number_var.get()
        # 一度だけ現在日時を取得し、同一プレビュー生成処理内で一貫性を保つ
        now = datetime.datetime.now()

        for index, path in enumerate(self.file_paths):
            base_name = os.path.basename(path)
            root, ext = os.path.splitext(base_name)
            seq_num = start_num + index

            if mode == "serial_only":
                # 連番のみ
                new_name = f"{seq_num}{ext}"
            elif mode == "serial_prefix":
                # 連番_元ファイル名
                new_name = f"{seq_num}_{root}{ext}"
            elif mode == "serial_suffix":
                # 元ファイル名_連番
                new_name = f"{root}_{seq_num}{ext}"
            else:
                # カスタムテンプレート
                template = self.template_var.get()
                new_name = self.apply_template(template, root, seq_num, now) + ext

            converted_names.append(new_name)
        return converted_names

    def apply_template(self, template: str, root: str, seq_num: int, now: datetime.datetime) -> str:
        """
        テンプレート文字列に{filename}, {num}, {date}を適用するヘルパーメソッド。
        """
        result = template.replace("{filename}", root)

        # {num}置換
        num_pattern = r"{num(?::(.*?))?}"
        def replace_num(match):
            fmt = match.group(1)
            if fmt:
                # 指定されたフォーマットで整形
                return ("{:" + fmt + "}").format(seq_num)
            else:
                return str(seq_num)
        result = re.sub(num_pattern, replace_num, result)

        # {date}置換
        date_pattern = r"{date(?::(.*?))?}"
        def replace_date(match):
            fmt = match.group(1)
            if fmt:
                return now.strftime(fmt)
            else:
                return now.strftime("%Y%m%d")
        result = re.sub(date_pattern, replace_date, result)

        return result

    def rename_files(self):
        """ファイル名変更を実行する。重複チェック、存在チェック、ユーザ確認を行ったうえでリネーム。"""
        if not self.file_paths:
            messagebox.showwarning("警告", "リネーム対象のファイルがありません。")
            return

        converted_names = self.generate_preview_names()

        # 重複チェック
        if len(converted_names) != len(set(converted_names)):
            messagebox.showerror("エラー", "同名のファイル名が発生します。テンプレートやモードを見直してください。")
            return

        # ファイル存在チェック
        for src, dst_name in zip(self.file_paths, converted_names):
            dst_path = os.path.join(os.path.dirname(src), dst_name)
            if os.path.exists(dst_path):
                messagebox.showerror("エラー", f"ファイル '{dst_name}' がすでに存在します。")
                return

        # 実行確認
        if not messagebox.askyesno("確認", "ファイル名を変更しますか？（元に戻せません）"):
            return

        # リネーム実行
        for src, dst_name in zip(self.file_paths, converted_names):
            dst_path = os.path.join(os.path.dirname(src), dst_name)
            try:
                os.rename(src, dst_path)
            except Exception as e:
                # 一件でも失敗したら処理停止しエラー表示
                # (ここでロールバック処理を入れるなら、別途対応可能)
                messagebox.showerror("エラー", f"ファイルのリネーム中にエラーが発生しました:\n{e}")
                return

        messagebox.showinfo("完了", "すべてのファイル名変更が完了しました。")
        self.file_paths.clear()
        self.update_tree_preview()

    def delete_selected_items(self, event):
        """Deleteキー押下で選択中のファイルをリストから削除。"""
        selected = self.tree.selection()
        if not selected:
            return

        all_items = self.tree.get_children()
        indexes_to_remove = [all_items.index(sel) for sel in selected]
        for index in sorted(indexes_to_remove, reverse=True):
            del self.file_paths[index]
        self.update_tree_preview()

    def clear_list(self):
        """ファイルリストをクリアしてプレビュー更新。"""
        self.file_paths.clear()
        self.update_tree_preview()

if __name__ == "__main__":
    app = ImageRenameApp()
    app.mainloop()
