"""Dsk's window: an HTML/CSS interface (dsk/ui) in a native window via pywebview.

Uses WebKit on macOS and Edge WebView2 on Windows, so both platforms get the same UI.
"""

import json
import os
import subprocess
import sys
import threading
import time

import webview

from . import __version__, advisor, clean, scan, trash
from .settings import Settings
from .updater import Updater

UI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui")
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    UI_DIR = os.path.join(sys._MEIPASS, "dsk", "ui")

BG = "#0b0b0c"


class Api(object):
    def __init__(self):
        self._window = None
        self._settings = Settings()
        self._updater = Updater(self._settings, lambda st: self._emit("update", st))
        self._scanner = None
        self._result = None
        self._groups = []
        self._busy = False
        self._advice = {}
        self._lock = threading.Lock()

    # ---- helpers ---------------------------------------------------------
    def _emit(self, event, payload):
        if self._window:
            try:
                self._window.evaluate_js("window.App && App.on(%s, %s)" % (json.dumps(event), json.dumps(payload, default=str)))
            except Exception:
                pass

    def _scan_payload(self, r):
        d = r.public()
        d["current"] = scan.pretty(r.current) if r.current else ""
        return d

    def _groups_payload(self):
        return {"groups": self._groups, "summary": clean.summary(self._groups), "advice": self._advice}

    # ---- called from JS --------------------------------------------------
    def info(self):
        return {"version": __version__, "platform": sys.platform, "settings": self._settings.public(),
                "update": self._updater.state(), "home": scan.HOME, "claude": self.claude_state(),
                "categories": [{"key": k, "label": l, "color": c} for k, l, c in scan.CATEGORIES],
                "disk": scan.disk_usage(), "wiztree": self._wiztree_state()}

    def _wiztree_state(self):
        if os.name != "nt":
            return None
        from . import wiztree
        return {"found": wiztree.find(self._settings.get("wiztree_path"))}

    def claude_state(self):
        return {"has_key": advisor.has_key(), "hint": advisor.key_hint(),
                "env": bool(os.environ.get("ANTHROPIC_API_KEY"))}

    def set_claude_key(self, key):
        try:
            advisor.set_key(key)
        except Exception as e:
            return dict(self.claude_state(), error="Couldn't save the key: %s" % e)
        return self.claude_state()

    def set_setting(self, key, value):
        if key in ("use_trash", "wiztree", "wiztree_path", "wiztree_admin", "auto_check", "auto_install", "welcomed"):
            self._settings.set(key, value)
            if key == "auto_install" and value and self._updater.phase == "available":
                threading.Thread(target=self._updater.stage_newest, daemon=True).start()
        return self._settings.public()

    def pick_wiztree(self):
        res = self._window.create_file_dialog(webview.FileDialog.OPEN, allow_multiple=False,
                                              file_types=("WizTree (WizTree*.exe)", "Programs (*.exe)"))
        p = res[0] if isinstance(res, (list, tuple)) and res else res
        if p:
            self._settings.set("wiztree_path", p)
        return self._wiztree_state()

    # updates
    def check_updates(self):
        return self._updater.check(manual=True)

    def download_update(self):
        threading.Thread(target=self._updater.stage_newest, daemon=True).start()

    def install_update(self):
        def go():
            if self._updater.install() == "open_page":
                self.open_url(self._updater.state()["page"])
        threading.Thread(target=go, daemon=True).start()

    def open_url(self, url):
        if not url.startswith(("https://github.com/", "https://console.anthropic.com/", "https://diskanalyzer.com/",
                               "x-apple.systempreferences:", "ms-settings:")):
            return
        if url.startswith(("x-apple.systempreferences:", "ms-settings:")):
            try:
                if sys.platform == "darwin":
                    subprocess.Popen(["open", url])
                else:
                    os.startfile(url)  # type: ignore[attr-defined]
            except Exception:
                pass
            return
        import webbrowser
        webbrowser.open(url)

    # scanning
    def scan(self):
        if self._busy or (self._scanner and not (self._result and self._result.finished)):
            return False
        self._advice = {}
        threading.Thread(target=self._scan, daemon=True).start()
        return True

    def _scan(self):
        last = [0.0]

        def progress(r):
            now = time.time()
            if now - last[0] < 0.2 and not r.finished:
                return
            last[0] = now
            self._emit("scan", self._scan_payload(r))

        r = None
        if os.name == "nt" and self._settings.get("wiztree"):
            from . import wiztree
            exe = wiztree.find(self._settings.get("wiztree_path"))
            if exe:
                try:
                    self._emit("scan", {"current": "WizTree is reading the drive", "done": False, "engine": "wiztree",
                                        "disk": scan.disk_usage(), "sizes": {k: 0 for k in scan.KEYS}})
                    r = wiztree.run(exe, admin=bool(self._settings.get("wiztree_admin")), progress=progress)
                except Exception as e:
                    self._emit("toast", {"text": "WizTree didn't finish (%s). Using the built-in scan." % e, "err": True})
                    r = None
        if r is None:
            self._scanner = scan.Scanner(progress=progress)
            self._result = self._scanner.result
            r = self._scanner.run()
        self._result = r
        self._emit("scan", self._scan_payload(r))
        self._emit("looking", {})
        try:
            self._groups = clean.evaluate(r)
        except Exception as e:
            self._groups = []
            self._emit("toast", {"text": "Couldn't work out what to clear: %s" % e, "err": True})
        self._emit("groups", self._groups_payload())
        self._emit("large", self.large_files())

    def large_files(self):
        if not self._result:
            return []
        now = time.time()
        out = []
        for f in self._result.largest(300):
            # A file inside an app bundle or the system isn't something to remove on its own.
            if ".app/" in f["path"] or ".photoslibrary" in f["path"] or not os.path.exists(f["path"]):
                continue
            try:
                trash.check(f["path"])
            except trash.NotAllowed:
                continue
            out.append({"path": f["path"], "show": scan.pretty(f["path"]), "name": os.path.basename(f["path"]),
                        "size": f["size"], "mtime": f["mtime"], "cat": f["cat"],
                        "days": int((now - max(f["mtime"] or 0, f["atime"] or 0)) / 86400)})
        return out[:200]

    # cleaning
    def clean(self, paths, empty_trash=False):
        """Removes the given paths (each must come from the current groups or large files)."""
        if self._busy:
            return False
        known = {i["path"] for g in self._groups if g["action"] == "remove" for i in g["items"]}
        known |= {f["path"] for f in self.large_files()}
        paths = [p for p in (paths or []) if p in known]
        if not paths and not empty_trash:
            return False
        self._busy = True
        threading.Thread(target=self._clean, args=(paths, bool(empty_trash)), daemon=True).start()
        return True

    def _clean(self, paths, empty_trash):
        use_trash = bool(self._settings.get("use_trash"))
        sizes = {i["path"]: i["size"] for g in self._groups for i in g["items"]}
        sizes.update({f["path"]: f["size"] for f in (self._result.largest(300) if self._result else [])})
        self._emit("cleaning", {"total": len(paths), "trash": empty_trash})

        def prog(done, total, path):
            self._emit("clean-progress", {"done": done, "total": total, "current": scan.pretty(path)})

        done, failed = trash.remove(paths, use_trash=use_trash, progress=prog)
        freed = sum(sizes.get(p, 0) for p in done)
        moved = {}
        if self._result:
            for g in self._groups:
                for i in g["items"]:
                    if i["path"] in done:
                        moved[g["cat"]] = moved.get(g["cat"], 0) + i["size"]
            for f in self._result.largest(300):
                if f["path"] in done and not any(f["path"] == i["path"] for g in self._groups for i in g["items"]):
                    moved[f["cat"]] = moved.get(f["cat"], 0) + f["size"]
        emptied = 0
        trash_err = None
        if empty_trash:
            emptied = self._result.sizes.get("trash", 0) if self._result else 0
            try:
                trash.empty_trash()
            except Exception as e:
                trash_err = str(e)
                emptied = 0
        # Update the bar: removed bytes leave their category; with the Trash on they land in it.
        if self._result:
            r = self._result
            for cat, n in moved.items():
                r.sizes[cat] = max(0, r.sizes.get(cat, 0) - n)
                if use_trash:
                    r.sizes["trash"] = r.sizes.get("trash", 0) + n
            if empty_trash and not trash_err:
                r.sizes["trash"] = 0
            r.disk = scan.disk_usage()
        donepaths = set(done)
        for g in self._groups:
            g["items"] = [i for i in g["items"] if i["path"] not in donepaths]
            if g["action"] == "remove":
                g["size"] = sum(i["size"] for i in g["items"])
                g["count"] = len(g["items"])
            if g["action"] == "empty_trash":
                g["size"] = self._result.sizes.get("trash", 0) if self._result else 0
        self._groups = [g for g in self._groups if g["size"] > 0 or g["action"] == "none"]
        if use_trash and moved and not any(g["action"] == "empty_trash" for g in self._groups):
            self._groups = clean.evaluate(self._result)
        self._busy = False
        self._emit("cleaned", {"done": len(done), "failed": [[scan.pretty(p), why] for p, why in failed[:30]],
                               "failed_count": len(failed), "freed": freed, "moved": moved, "to_trash": use_trash,
                               "emptied": emptied, "trash_error": trash_err})
        if self._result:
            self._emit("scan", self._scan_payload(self._result))
        self._emit("groups", self._groups_payload())
        self._emit("large", self.large_files())

    # Claude
    def ask_claude(self):
        if not self._groups:
            return False

        def go():
            self._emit("claude", {"phase": "thinking"})
            try:
                ans = advisor.Advisor().review(self._groups)
                self._advice = ans["items"]
                self._emit("claude", {"phase": "done", "summary": ans["summary"], "count": len(ans["items"])})
                self._emit("groups", self._groups_payload())
            except Exception as e:
                self._emit("claude", {"phase": "failed", "error": str(e)})
        threading.Thread(target=go, daemon=True).start()
        return True

    def explain(self, path):
        def go():
            self._emit("explain", {"path": path, "phase": "thinking"})
            try:
                size = None
                if self._result:
                    size = self._result.folder_size(path)
                if size is None:
                    size = scan.measure(path)
                kids = advisor.children_of(path) if os.path.isdir(path) else []
                ans = advisor.Advisor().explain(path, size, kids)
                self._emit("explain", dict(ans, path=path, phase="done"))
            except Exception as e:
                self._emit("explain", {"path": path, "phase": "failed", "error": str(e)})
        threading.Thread(target=go, daemon=True).start()

    def reveal(self, path):
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", "-R", path])
            elif os.name == "nt":
                subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
            else:
                subprocess.Popen(["xdg-open", os.path.dirname(path)])
        except Exception:
            pass

    def open_privacy(self):
        if sys.platform == "darwin":
            self.open_url("x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles")


# ---- native window chrome -------------------------------------------------

def _style_mac(window):
    """Dark, transparent title bar with content running underneath (like Dwn)."""
    try:
        import AppKit
        from PyObjCTools import AppHelper

        def apply():
            w = window.native
            w.setStyleMask_(w.styleMask() | AppKit.NSWindowStyleMaskFullSizeContentView)
            w.setTitlebarAppearsTransparent_(True)
            w.setTitleVisibility_(AppKit.NSWindowTitleHidden)
            w.setAppearance_(AppKit.NSAppearance.appearanceNamed_(AppKit.NSAppearanceNameDarkAqua))
            w.setBackgroundColor_(AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.043, 0.043, 0.047, 1.0))
            w.setMovableByWindowBackground_(False)
            try:
                w.contentView().superview().subviews().lastObject().setBackgroundColor_(AppKit.NSColor.clearColor())
            except Exception:
                pass
            if hasattr(w, "setToolbarStyle_"):
                w.setToolbarStyle_(AppKit.NSWindowToolbarStyleUnifiedCompact)

        AppHelper.callAfter(apply)
    except Exception:
        pass


def _style_windows(window):
    """Dark title bar on Windows 10/11; caption colour matches the app on Windows 11."""
    try:
        import ctypes

        hwnd = window.native.Handle.ToInt32()
        dwm = ctypes.windll.dwmapi
        on = ctypes.c_int(1)
        for attr in (20, 19):
            if dwm.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(on), 4) == 0:
                break
        caption = ctypes.c_int(0x000C0B0B)
        dwm.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(caption), 4)
    except Exception:
        pass


def main():
    api = Api()
    webview.settings["DRAG_REGION_DIRECT_TARGET_ONLY"] = True
    window = webview.create_window(
        "Dsk", url=os.path.join(UI_DIR, "index.html"), js_api=api,
        width=1040, height=820, min_size=(820, 640), background_color=BG, easy_drag=False,
    )
    api._window = window

    def quit_for_install():
        try:
            window.destroy()
        finally:
            t = threading.Timer(3.0, lambda: os._exit(0))
            t.daemon = True
            t.start()

    api._updater.on_quit_for_install = quit_for_install
    window.events.closing += lambda: api._updater.install_on_quit()
    window.events.loaded += lambda: api._updater.start()

    if sys.platform == "darwin":
        window.events.before_show += lambda: _style_mac(window)
    elif os.name == "nt":
        window.events.shown += lambda: _style_windows(window)
    webview.start(debug=bool(os.environ.get("DSK_DEBUG")))
    if os.name == "nt":
        # Leave without Python's normal shutdown: tearing down pythonnet and WinForms can crash, and a
        # crash report keeps the process alive, which stalls the update swap (see the updater).
        os._exit(0)


if __name__ == "__main__":
    main()
