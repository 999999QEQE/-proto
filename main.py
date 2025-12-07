import json
import os
import random
import subprocess
import sys
import tkinter as tk
from dataclasses import dataclass, asdict
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

try:  # Optional image scaling
    from PIL import Image, ImageTk  # type: ignore
except Exception:  # pillow not required for basic usage
    Image = None
    ImageTk = None

DATA_FILE = "pages.json"


def resource_path(path: str) -> str:
    return os.path.abspath(path)


@dataclass
class Page:
    title: str = "示例页面"
    subtitle: str = "副标题"
    media_path: str = ""
    paragraphs: List[str] = None
    random_min: int = 1
    random_max: int = 10

    def __post_init__(self):
        if self.paragraphs is None:
            self.paragraphs = [
                "在这里填写你的长篇描述，空行分隔多个段落。",
                "点击随机高亮可以在段落间做动画效果，方便抽取。",
            ]


def load_pages() -> List[Page]:
    if not os.path.exists(DATA_FILE):
        return [Page()]
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return [Page(**item) for item in raw]
    except Exception as exc:
        messagebox.showwarning("读取失败", f"无法读取 {DATA_FILE}: {exc}\n将使用默认页面。")
        return [Page()]


def save_pages(pages: List[Page]):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([asdict(p) for p in pages], f, ensure_ascii=False, indent=2)


class RouletteApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("本地轮盘随机器")
        self.pages: List[Page] = load_pages()
        self.current_index: int = 0
        self.background_image: Optional[ImageTk.PhotoImage] = None

        self.build_layout()
        self.render_page_list()
        self.load_page(0)

    def build_layout(self):
        self.root.geometry("1200x720")
        self.root.minsize(960, 640)

        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.sidebar = ttk.Frame(self.root, padding=10)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.rowconfigure(1, weight=1)

        ttk.Label(self.sidebar, text="页面", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w")
        self.page_list = tk.Listbox(self.sidebar, height=20)
        self.page_list.grid(row=1, column=0, sticky="nsew", pady=6)
        self.page_list.bind("<<ListboxSelect>>", self.on_page_select)

        btn_frame = ttk.Frame(self.sidebar)
        btn_frame.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(btn_frame, text="添加页面", command=self.add_page).grid(row=0, column=0, padx=2)
        ttk.Button(btn_frame, text="删除页面", command=self.delete_page).grid(row=0, column=1, padx=2)

        # Main area
        self.main = ttk.Frame(self.root, padding=10)
        self.main.grid(row=0, column=1, sticky="nsew")
        for i in range(2):
            self.main.columnconfigure(i, weight=1)
        self.main.rowconfigure(3, weight=1)

        self.preview_canvas = tk.Canvas(self.main, height=240, highlightthickness=0, bg="#10121a")
        self.preview_canvas.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        form = ttk.Frame(self.main)
        form.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="标题").grid(row=0, column=0, sticky="w")
        self.title_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.title_var).grid(row=0, column=1, sticky="ew", padx=6)

        ttk.Label(form, text="副标题").grid(row=1, column=0, sticky="w")
        self.subtitle_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.subtitle_var).grid(row=1, column=1, sticky="ew", padx=6)

        ttk.Label(form, text="图片或视频路径").grid(row=2, column=0, sticky="w")
        self.media_var = tk.StringVar()
        media_row = ttk.Frame(form)
        media_row.grid(row=2, column=1, sticky="ew", padx=6)
        media_row.columnconfigure(0, weight=1)
        ttk.Entry(media_row, textvariable=self.media_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(media_row, text="浏览", command=self.browse_media).grid(row=0, column=1, padx=4)
        ttk.Button(media_row, text="打开视频", command=self.open_media).grid(row=0, column=2)

        self.save_btn = ttk.Button(form, text="保存当前页面", command=self.save_current_page)
        self.save_btn.grid(row=3, column=1, sticky="e", pady=6, padx=6)

        # Paragraph editor and randomizer
        editor_frame = ttk.Frame(self.main)
        editor_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        editor_frame.rowconfigure(0, weight=1)
        editor_frame.columnconfigure(0, weight=1)

        ttk.Label(editor_frame, text="段落内容 (空行分隔)").grid(row=0, column=0, sticky="w")
        text_container = ttk.Frame(editor_frame)
        text_container.grid(row=1, column=0, sticky="nsew")
        text_container.rowconfigure(0, weight=1)
        text_container.columnconfigure(0, weight=1)

        self.paragraph_text = tk.Text(text_container, wrap="word")
        self.paragraph_text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(text_container, command=self.paragraph_text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.paragraph_text.configure(yscrollcommand=scroll.set)

        actions_frame = ttk.Frame(editor_frame)
        actions_frame.grid(row=2, column=0, sticky="ew", pady=4)
        ttk.Button(actions_frame, text="刷新段落列表", command=self.refresh_paragraph_list).grid(row=0, column=0, padx=4)
        ttk.Button(actions_frame, text="随机高亮段落", command=self.animate_pick).grid(row=0, column=1, padx=4)

        list_frame = ttk.Frame(self.main)
        list_frame.grid(row=2, column=1, sticky="nsew", padx=(10, 0), pady=(0, 10))
        list_frame.rowconfigure(1, weight=1)
        list_frame.columnconfigure(0, weight=1)

        ttk.Label(list_frame, text="段落列表").grid(row=0, column=0, sticky="w")
        self.paragraph_list = tk.Listbox(list_frame, height=10)
        self.paragraph_list.grid(row=1, column=0, sticky="nsew")

        random_frame = ttk.Labelframe(self.main, text="随机器")
        random_frame.grid(row=3, column=0, columnspan=2, sticky="ew")
        for i in range(4):
            random_frame.columnconfigure(i, weight=1)

        ttk.Label(random_frame, text="最小值").grid(row=0, column=0, padx=4, pady=6)
        self.min_var = tk.IntVar(value=1)
        ttk.Entry(random_frame, textvariable=self.min_var, width=10).grid(row=0, column=1, padx=4)

        ttk.Label(random_frame, text="最大值").grid(row=0, column=2, padx=4, pady=6)
        self.max_var = tk.IntVar(value=10)
        ttk.Entry(random_frame, textvariable=self.max_var, width=10).grid(row=0, column=3, padx=4)

        ttk.Button(random_frame, text="生成随机数", command=self.generate_number).grid(row=0, column=4, padx=6)
        self.random_result = ttk.Label(random_frame, text="结果将显示在此", font=("Arial", 12, "bold"))
        self.random_result.grid(row=0, column=5, padx=8)

    def render_page_list(self):
        self.page_list.delete(0, tk.END)
        for idx, page in enumerate(self.pages):
            label = page.title or f"页面 {idx+1}"
            self.page_list.insert(tk.END, label)
        if self.pages:
            self.page_list.select_set(self.current_index)

    def on_page_select(self, _event=None):
        selection = self.page_list.curselection()
        if selection:
            self.save_current_page()
            self.load_page(selection[0])

    def load_page(self, index: int):
        self.current_index = max(0, min(index, len(self.pages) - 1))
        page = self.pages[self.current_index]
        self.title_var.set(page.title)
        self.subtitle_var.set(page.subtitle)
        self.media_var.set(page.media_path)
        self.min_var.set(page.random_min)
        self.max_var.set(page.random_max)
        self.paragraph_text.delete("1.0", tk.END)
        self.paragraph_text.insert(tk.END, "\n\n".join(page.paragraphs))
        self.refresh_paragraph_list()
        self.update_preview()

    def save_current_page(self):
        if not self.pages:
            return
        paragraphs = self.parse_paragraphs()
        if not paragraphs:
            paragraphs = ["请输入至少一个段落"]
        page = self.pages[self.current_index]
        page.title = self.title_var.get().strip() or "未命名页面"
        page.subtitle = self.subtitle_var.get().strip()
        page.media_path = self.media_var.get().strip()
        page.paragraphs = paragraphs
        page.random_min = self.min_var.get()
        page.random_max = self.max_var.get()
        save_pages(self.pages)
        self.render_page_list()

    def parse_paragraphs(self) -> List[str]:
        raw = self.paragraph_text.get("1.0", tk.END)
        blocks = [p.strip() for p in raw.split("\n\n")]
        return [b for b in blocks if b]

    def refresh_paragraph_list(self):
        items = self.parse_paragraphs()
        self.paragraph_list.delete(0, tk.END)
        for p in items:
            display = (p[:80] + "...") if len(p) > 80 else p
            self.paragraph_list.insert(tk.END, display)

    def animate_pick(self):
        items = self.parse_paragraphs()
        if not items:
            messagebox.showinfo("提示", "请先填写至少一个段落。")
            return
        loops = max(12, len(items) * 3)
        for i in range(loops):
            idx = i % len(items)
            self.highlight_paragraph(idx)
            self.root.update()
            self.root.after(60)
        final_index = random.randrange(len(items))
        for _ in range(10):  # slow down for suspense
            self.highlight_paragraph(final_index)
            self.root.update()
            self.root.after(120)
        messagebox.showinfo("抽取结果", items[final_index])

    def highlight_paragraph(self, index: int):
        self.paragraph_list.selection_clear(0, tk.END)
        self.paragraph_list.activate(index)
        self.paragraph_list.selection_set(index)
        self.paragraph_list.see(index)

    def generate_number(self):
        try:
            low = int(self.min_var.get())
            high = int(self.max_var.get())
            if low > high:
                low, high = high, low
            value = random.randint(low, high)
            self.random_result.config(text=f"结果：{value}")
        except Exception as exc:
            messagebox.showerror("错误", f"请输入有效数字: {exc}")

    def add_page(self):
        self.save_current_page()
        self.pages.append(Page(title=f"页面 {len(self.pages)+1}"))
        self.render_page_list()
        self.load_page(len(self.pages) - 1)

    def delete_page(self):
        if len(self.pages) <= 1:
            messagebox.showinfo("提示", "至少需要保留一个页面。")
            return
        if messagebox.askyesno("删除页面", "确定要删除当前页面吗？"):
            self.pages.pop(self.current_index)
            self.current_index = max(0, self.current_index - 1)
            save_pages(self.pages)
            self.render_page_list()
            self.load_page(self.current_index)

    def browse_media(self):
        path = filedialog.askopenfilename(title="选择图片或视频")
        if path:
            self.media_var.set(resource_path(path))
            self.update_preview()

    def open_media(self):
        path = self.media_var.get().strip()
        if not path:
            messagebox.showinfo("提示", "请填写或选择一个媒体路径。")
            return
        absolute = resource_path(path)
        if not os.path.exists(absolute):
            messagebox.showerror("错误", f"文件不存在: {absolute}")
            return
        if sys.platform.startswith("darwin"):
            subprocess.Popen(["open", absolute])
        elif os.name == "nt":
            os.startfile(absolute)  # type: ignore
        else:
            subprocess.Popen(["xdg-open", absolute])

    def update_preview(self):
        self.preview_canvas.delete("all")
        page = self.pages[self.current_index]
        self.preview_canvas.configure(bg="#0f131c")
        width = self.preview_canvas.winfo_width() or 1200
        height = self.preview_canvas.winfo_height() or 240
        media_path = page.media_path

        if media_path and os.path.exists(media_path) and Image and ImageTk:
            try:
                img = Image.open(media_path)
                img = img.resize((width, height))
                self.background_image = ImageTk.PhotoImage(img)
                self.preview_canvas.create_image(0, 0, image=self.background_image, anchor="nw")
            except Exception:
                self.preview_canvas.configure(bg="#1b1e29")
        elif media_path:
            self.preview_canvas.create_text(
                20,
                20,
                anchor="nw",
                fill="#9ea6ff",
                font=("Arial", 12),
                text=f"媒体预览不可用: {media_path}",
            )

        overlay = self.preview_canvas.create_rectangle(0, height - 100, width, height, fill="#0b0d14", stipple="gray50")
        self.preview_canvas.tag_lower(overlay)

        self.preview_canvas.create_text(
            24,
            height - 90,
            anchor="nw",
            fill="white",
            font=("Arial", 20, "bold"),
            text=page.title,
        )
        self.preview_canvas.create_text(
            24,
            height - 50,
            anchor="nw",
            fill="#c8d0ff",
            font=("Arial", 14),
            text=page.subtitle,
        )


def main():
    root = tk.Tk()
    app = RouletteApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
