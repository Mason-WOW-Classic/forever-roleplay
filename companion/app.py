from __future__ import annotations

import json
import queue
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from tkinter import ttk

from .clipboard import ClipboardBusy, WindowsClipboard
from .core import (SOL_MODEL, OPENAI_BASE_URL, OPENAI_MODEL, ClipboardFlow, Config, RewriteError,
                   load_api_key, make_request, rewrite)

ROOT = Path(__file__).resolve().parent.parent


class App:
    def __init__(self, root: tk.Tk, clipboard=None):
        self.root = root
        root.title("WoW RP · Real DonaldTrump · v0.5")
        root.geometry("820x700")
        root.minsize(720, 650)
        self.flow = ClipboardFlow()
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="rp-llm")
        self.events = queue.Queue()
        self.future = None
        self.closed = False
        self.config = self.load_config()
        self.key = ""
        key_error = ""
        try:
            self.key = load_api_key(self.config, ROOT)
        except RewriteError as exc:
            key_error = str(exc)
        self.status = tk.StringVar(value="")
        self.demo = tk.BooleanVar(value=self.config.demo)
        self.url = tk.StringVar(value=self.config.base_url)
        self.model = tk.StringVar(value=self.config.model)
        self.language = tk.StringVar(value=self.config.output_language)
        self.tier = tk.StringVar(value=self.config.service_tier)
        self.secret = tk.StringVar()
        self.expressive = tk.BooleanVar(value=False)
        self._build()
        root.update_idletasks()
        self.clipboard = clipboard or WindowsClipboard(root.winfo_id())
        self.last_sequence = self.clipboard.sequence()
        self._set_mode_status()
        if key_error:
            self.status.set(key_error)
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(100, self.poll)

    def load_config(self):
        try:
            data = json.loads((ROOT / "settings.json").read_text(encoding="utf-8"))
            config = Config(**data)
            config.validate()
            return config
        except (OSError, ValueError, TypeError):
            return Config()

    def _build(self):
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Real DonaldTrump", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(outer, text="默认正常改写 · 手动勾选发挥才可加梗 · 复制触发 · 自己发送").pack(anchor="w", pady=(3, 12))
        ttk.Label(outer, textvariable=self.status, wraplength=750, foreground="#175a7a").pack(fill="x", pady=(0, 12))
        tabs = ttk.Notebook(outer)
        tabs.pack(fill="both", expand=True)
        settings = ttk.Frame(tabs, padding=12)
        tabs.add(settings, text="模型设置")
        settings.columnconfigure(1, weight=1)
        for row, (label, var, show) in enumerate([
            ("API 基础地址", self.url, ""), ("模型名", self.model, ""),
            ("API Key（仅本次会话）", self.secret, "•"),
        ]):
            ttk.Label(settings, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=3)
            ttk.Entry(settings, textvariable=var, show=show).grid(row=row, column=1, sticky="ew", pady=3)
        ttk.Label(settings, text="输出语言").grid(row=3, column=0, sticky="w")
        ttk.Combobox(settings, textvariable=self.language, values=("English", "跟随原文"), state="readonly", width=18).grid(row=3, column=1, sticky="w", pady=3)
        ttk.Label(settings, text="OpenAI 服务档位").grid(row=4, column=0, sticky="w")
        ttk.Combobox(settings, textvariable=self.tier, values=("default", "fast", "ultrafast"), state="readonly", width=18).grid(row=4, column=1, sticky="w", pady=3)
        ttk.Checkbutton(settings, text="离线模拟（不调用 LLM；只验证流程，不代表人格效果）", variable=self.demo).grid(row=5, column=0, columnspan=2, sticky="w", pady=5)
        controls = ttk.Frame(settings)
        controls.grid(row=6, column=0, columnspan=2, sticky="w")
        ttk.Button(controls, text="应用设置并开始监听", command=self.apply).pack(side="left")
        ttk.Button(controls, text="暂停", command=self.pause).pack(side="left", padx=8)
        ttk.Button(controls, text="OpenAI 小模型", command=self.openai_preset).pack(side="left")
        ttk.Button(controls, text="Sol Ultrafast", command=self.sol_preset).pack(side="left", padx=8)
        ttk.Label(settings, text="OpenAI 从本目录 key.txt 读取密钥。Ultrafast 费用高于标准档，延迟以实测为准。", wraplength=700).grid(row=7, column=0, columnspan=2, sticky="w", pady=10)
        panel = ttk.Frame(tabs, padding=12)
        tabs.add(panel, text="无游戏试用")
        background = ttk.Frame(tabs, padding=12)
        tabs.add(background, text="发挥背景")
        ttk.Label(background, text="仅发挥模式附带。可填写地点、队友名字和职业、当前情境；留空也能改写。", wraplength=730).pack(anchor="w")
        ttk.Label(background, text="这些内容会随发挥请求发送给所选模型。只在本次会话保留；正常模式不附带。", wraplength=730).pack(anchor="w", pady=6)
        self.context = tk.Text(background, height=10, wrap="word", undo=True, font=("Microsoft YaHei UI", 11))
        self.context.pack(fill="both", expand=True, pady=6)
        self.context.bind("<<Modified>>", self.context_changed)
        ttk.Button(background, text="填入死亡矿井示例（虚构队友）", command=self.context_example).pack(anchor="w")
        ttk.Label(background, text="背景只帮助选梗，不会自动更改招募需求，也不能证明玩家的专精或副本熟练度。", wraplength=730).pack(anchor="w", pady=8)
        tabs.select(panel)
        ttk.Label(panel, text="① 输入原句，点“准备复制”。② 在请求框按 Ctrl+C。③ 听到提示后，在结果框按 Ctrl+V。", wraplength=730).pack(anchor="w")
        ttk.Checkbutton(panel, text="发挥模式（可加贴合语境的梗；不勾选为正常模式）", variable=self.expressive, command=self.style_changed).pack(anchor="w", pady=(6, 0))
        ttk.Label(panel, text="可在“发挥背景”页补充地点和队友；切回此页准备复制。").pack(anchor="w")
        self.source = tk.Text(panel, height=2, wrap="word", undo=True, font=("Microsoft YaHei UI", 11))
        self.source.pack(fill="x", pady=6)
        self.source.insert("1.0", "找两个人打玛拉顿，一坦一奶")
        buttons = ttk.Frame(panel)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="准备复制", command=self.prepare).pack(side="left")
        ttk.Button(buttons, text="试试：先杀奶", command=lambda: self.example("先杀奶")).pack(side="left", padx=6)
        ttk.Button(buttons, text="试试：玛拉顿 LFM", command=lambda: self.example("找两个人打玛拉顿，一坦一奶")).pack(side="left")
        ttk.Button(buttons, text="试试：拍卖行", command=lambda: self.example("拍卖行这瓶药也太贵了")).pack(side="left", padx=6)
        ttk.Label(panel, text="请求框：已带人格标记，选中后手动 Ctrl+C（不要发到游戏频道）").pack(anchor="w", pady=(8, 0))
        self.request = tk.Text(panel, height=4, wrap="word", font=("Microsoft YaHei UI", 10))
        self.request.pack(fill="x", pady=4)
        ttk.Label(panel, text="结果框：点击此处后手动 Ctrl+V；回车只换行，不会发送任何消息").pack(anchor="w")
        self.pasted = tk.Text(panel, height=3, wrap="word", font=("Microsoft YaHei UI", 11))
        self.pasted.pack(fill="x", pady=4)
        ttk.Label(panel, text="最近返回（仅本次会话；可选中手动复制）：").pack(anchor="w")
        self.result = tk.Text(panel, height=3, wrap="word", state="disabled", font=("Microsoft YaHei UI", 10))
        self.result.pack(fill="both", expand=True, pady=4)
        ttk.Label(outer, text="WOWRP/3 支持发挥背景，兼容 WOWRP/2。只在手动复制时调用，自己发送。", wraplength=750).pack(anchor="w", pady=(10, 0))

    def _set_mode_status(self):
        self.status.set("监听中 · 离线模拟，不会联网。" if self.config.demo else f"监听中 · {self.config.model} / {self.config.service_tier} · 仅处理带标记请求。")

    def apply(self):
        try:
            config = Config(base_url=self.url.get().strip(), model=self.model.get().strip(),
                            output_language=self.language.get(), demo=self.demo.get(),
                            timeout_seconds=self.config.timeout_seconds,
                            api_key_env=self.config.api_key_env, service_tier=self.tier.get())
            config.validate()
            key = self.secret.get().strip() or load_api_key(config, ROOT)
            if not config.demo and config.base_url.rstrip("/") == OPENAI_BASE_URL and not key:
                raise RewriteError("请把 API Key 放到本目录 key.txt，或在设置中填写。")
            # No key or draft is saved. Key may instead come from the named env var.
            (ROOT / "settings.json").write_text(json.dumps(asdict(config), ensure_ascii=False, indent=2), encoding="utf-8")
            self.config = config
            self.key = key
            self.flow.invalidate()
            self.flow.enabled = True
            self.last_sequence = self.clipboard.sequence()
            self._set_mode_status()
        except (RewriteError, OSError) as exc:
            self.status.set(str(exc))

    def openai_preset(self):
        self.url.set(OPENAI_BASE_URL)
        self.model.set(OPENAI_MODEL)
        self.tier.set("default")
        self.demo.set(False)
        self.apply()

    def sol_preset(self):
        self.url.set(OPENAI_BASE_URL)
        self.model.set(SOL_MODEL)
        self.tier.set("ultrafast")
        self.demo.set(False)
        self.apply()

    def pause(self):
        self.flow.enabled = False
        self.flow.invalidate()
        self.status.set("已暂停；处理中结果不会写回剪贴板。")

    def example(self, text):
        self.source.delete("1.0", "end")
        self.source.insert("1.0", text)
        self.prepare()

    def style_changed(self):
        self.flow.invalidate()
        if self.future:
            self.future.cancel()
        self.request.delete("1.0", "end")
        self.pasted.delete("1.0", "end")
        label = "发挥" if self.expressive.get() else "正常"
        self.status.set(f"已选择{label}模式。旧请求已失效，请重新准备并 Ctrl+C。")

    def context_changed(self, _event=None):
        if not self.context.edit_modified():
            return
        self.context.edit_modified(False)
        if self.expressive.get():
            self.style_changed()
            self.status.set("背景已修改，旧请求已失效；请回试用页重新准备并 Ctrl+C。")

    def context_example(self):
        self.context.delete("1.0", "end")
        self.context.insert("1.0", "地点：死亡矿井，西部荒野\n队友：Player1 - 牧师；Player2 - 盗贼\n最近选中过的非玩家目标（仅作场景背景）：迪菲亚矿工；迪菲亚监工")

    def prepare(self):
        try:
            mode = "expressive" if self.expressive.get() else "normal"
            context = self.context.get("1.0", "end-1c") if mode == "expressive" else ""
            wire = make_request(self.source.get("1.0", "end-1c"), mode, context)
            self.pasted.delete("1.0", "end")
            self.request.delete("1.0", "end")
            self.request.insert("1.0", wire)
            self.request.focus_set()
            self.request.tag_add("sel", "1.0", "end-1c")
            self.status.set(
                f"{'发挥' if mode == 'expressive' else '正常'}请求已选中。请按 Ctrl+C；完成后在结果框 Ctrl+V。"
                if self.flow.enabled else
                "已暂停。请求已准备；请先在模型设置恢复监听，再 Ctrl+C。"
            )
        except RewriteError as exc:
            self.status.set(str(exc))

    def poll(self):
        if self.closed:
            return
        try:
            if self.clipboard.sequence() != self.last_sequence:
                sequence, wire = self.clipboard.snapshot()
                self.last_sequence = sequence
                request = self.flow.observe(wire)
                if request:
                    generation, draft = request
                    self.status.set("正在改写… 可以继续游戏；再次复制其他内容会使本次结果失效。")
                    if self.future:
                        self.future.cancel()  # Keep at most one queued request.
                    self.future = self.pool.submit(rewrite, draft.text, self.config, self.key, draft.mode, draft.context)
                    self.future.add_done_callback(lambda future, g=generation, s=sequence, w=wire:
                                                  self.events.put((g, s, w, future)))
                elif self.flow.enabled and self.future and not self.future.done():
                    self.status.set("你已复制其他内容；之前的请求已失效，不会覆盖新剪贴板。")
        except ClipboardBusy:
            pass  # Retry next tick without advancing the observed sequence.
        except RewriteError as exc:
            self.status.set(str(exc))
        except OSError:
            self.flow.invalidate()
            self.status.set("剪贴板暂时不可用，请重新复制。")
        while True:
            try:
                generation, sequence, wire, future = self.events.get_nowait()
            except queue.Empty:
                break
            if not self.flow.is_current(generation) or future.cancelled():
                continue
            try:
                result = future.result()
                self.result.configure(state="normal")
                self.result.delete("1.0", "end")
                self.result.insert("1.0", result.text)
                self.result.configure(state="disabled")
                new_sequence = self.clipboard.replace_if_unchanged(sequence, wire, result.text)
                if new_sequence is None:
                    self.status.set("你已复制其他内容；旧结果已丢弃，剪贴板未覆盖。")
                    continue
                self.last_sequence = new_sequence
                label = "正常" if result.mode == "normal" else "发挥"
                demo = "离线模拟 · " if result.demo else ""
                self.status.set(f"完成 · {demo}{label} · {len(result.text.encode('utf-8'))} 字节。请 Ctrl+V 预览并自行发送。")
                self.root.bell()
            except (RewriteError, OSError) as exc:
                self.status.set(str(exc))
                self.root.bell()
            except Exception:
                # Do not show raw HTTP bodies, keys or source text in diagnostics.
                self.status.set("处理失败；原文已保留，请检查配置后重新复制。")
        self.root.after(100, self.poll)

    def close(self):
        self.closed = True
        self.flow.enabled = False
        self.flow.invalidate()
        self.pool.shutdown(wait=False, cancel_futures=True)
        self.root.destroy()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
