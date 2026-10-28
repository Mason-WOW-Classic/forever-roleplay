"""Windows Unicode clipboard only. No hooks, process handles or simulated input."""
from __future__ import annotations

import ctypes
import os
from ctypes import wintypes


class ClipboardBusy(OSError):
    pass


class WindowsClipboard:
    MAX_CLIPBOARD_BYTES = 32768

    def __init__(self, hwnd: int):
        if os.name != "nt":
            raise OSError("此助手目前仅支持 Windows。")
        self.hwnd = hwnd
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        u, k = self.user32, self.kernel32
        u.OpenClipboard.argtypes = [wintypes.HWND]
        u.OpenClipboard.restype = wintypes.BOOL
        u.CloseClipboard.argtypes = []
        u.CloseClipboard.restype = wintypes.BOOL
        u.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
        u.IsClipboardFormatAvailable.restype = wintypes.BOOL
        u.GetClipboardData.argtypes = [wintypes.UINT]
        u.GetClipboardData.restype = wintypes.HANDLE
        u.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        u.SetClipboardData.restype = wintypes.HANDLE
        u.EmptyClipboard.argtypes = []
        u.EmptyClipboard.restype = wintypes.BOOL
        u.GetClipboardSequenceNumber.argtypes = []
        u.GetClipboardSequenceNumber.restype = wintypes.DWORD
        k.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        k.GlobalAlloc.restype = wintypes.HGLOBAL
        k.GlobalLock.argtypes = [wintypes.HGLOBAL]
        k.GlobalLock.restype = ctypes.c_void_p
        k.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        k.GlobalUnlock.restype = wintypes.BOOL
        k.GlobalSize.argtypes = [wintypes.HGLOBAL]
        k.GlobalSize.restype = ctypes.c_size_t
        k.GlobalFree.argtypes = [wintypes.HGLOBAL]
        k.GlobalFree.restype = wintypes.HGLOBAL

    def sequence(self) -> int:
        return self.user32.GetClipboardSequenceNumber()

    def _open(self):
        if not self.user32.OpenClipboard(self.hwnd):
            if ctypes.get_last_error() == 5:
                raise OSError("Windows 拒绝剪贴板访问。请在普通桌面环境启动助手后重试。")
            raise ClipboardBusy("剪贴板正在被其他程序占用。")

    def _read_open(self) -> str:
        if not self.user32.IsClipboardFormatAvailable(13):
            return ""
        handle = self.user32.GetClipboardData(13)
        size = self.kernel32.GlobalSize(handle) if handle else 0
        if not 0 < size <= self.MAX_CLIPBOARD_BYTES:
            return ""  # Don't ingest large or nontext clipboard data.
        pointer = self.kernel32.GlobalLock(handle)
        if not pointer:
            raise ClipboardBusy("暂时无法读取剪贴板。")
        try:
            return ctypes.wstring_at(pointer, size // 2).split("\0", 1)[0]
        finally:
            self.kernel32.GlobalUnlock(handle)

    def snapshot(self) -> tuple[int, str]:
        self._open()
        try:
            return self.sequence(), self._read_open()
        finally:
            self.user32.CloseClipboard()

    def replace_if_unchanged(self, sequence: int, expected: str, text: str) -> int | None:
        encoded = text.encode("utf-16-le") + b"\0\0"
        handle = self.kernel32.GlobalAlloc(0x0002, len(encoded))
        if not handle:
            raise OSError("无法分配剪贴板内存。")
        transferred = False
        try:
            pointer = self.kernel32.GlobalLock(handle)
            if not pointer:
                raise OSError("无法锁定剪贴板内存。")
            try:
                ctypes.memmove(pointer, encoded, len(encoded))
            finally:
                self.kernel32.GlobalUnlock(handle)
            self._open()
            try:
                # The clipboard lock makes the comparison and replacement atomic.
                if self.sequence() != sequence or self._read_open() != expected:
                    return None
                if not self.user32.EmptyClipboard():
                    raise ClipboardBusy("无法更新剪贴板。")
                if not self.user32.SetClipboardData(13, handle):
                    raise OSError("无法写入剪贴板，请从助手结果框手动复制。")
                transferred = True
                return self.sequence()
            finally:
                self.user32.CloseClipboard()
        finally:
            if not transferred:
                self.kernel32.GlobalFree(handle)
