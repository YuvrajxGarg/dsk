"""Measures what's filling the disk, by category, without changing anything.

The walk uses os.scandir over a few threads, counts allocated blocks (so sparse
and cloned files aren't over-counted on macOS), skips symlinks, and counts each
hard-linked file once. Along the way it keeps:

  * the size of every category (Apps, Developer, Photos, ...),
  * the size of shallow folders and of every developer folder (node_modules,
    .venv, ...) so the cleanup rules can price themselves without walking again,
  * the largest files it saw.

"System data" is what's used on the disk minus everything measured, the same
way macOS reports it.
"""

import heapq
import os
import shutil
import stat
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

IS_MAC = sys.platform == "darwin"
IS_WIN = os.name == "nt"
HOME = os.path.expanduser("~")

# key, label, colour (matches the bar in the UI)
CATEGORIES = [
    ("apps", "Apps", "#3d8bff"),
    ("dev", "Developer", "#2fd36b"),
    ("photos", "Photos", "#ff4fa3"),
    ("movies", "Movies", "#a46bff"),
    ("docs", "Documents", "#22d3ee"),
    ("music", "Music", "#facc15"),
    ("system", "System data", "#a1a1aa"),
    ("caches", "Caches", "#ff8a3d"),
    ("trash", "Trash" if not IS_WIN else "Recycle Bin", "#ff5b5b"),
]
KEYS = [c[0] for c in CATEGORIES]

# Folders that hold rebuildable project dependencies or build output. Wherever they
# turn up (usually inside Documents), their size counts as Developer.
DEV_DIRS = {"node_modules", ".venv", "venv", "Pods", ".gradle", "DerivedData", ".next", ".turbo",
            ".parcel-cache", ".svelte-kit", ".nuxt", "__pycache__", ".pytest_cache", ".mypy_cache",
            ".tox", "bower_components", ".dart_tool"}
# These are only Developer when a project file sits beside them (a "target" or "build" folder on its own could be anything).
DEV_BUILD_DIRS = {"target": ("Cargo.toml", "pom.xml"), "build": ("build.gradle", "build.gradle.kts", "CMakeLists.txt", "package.json")}

TOP_FILES = 300
SHALLOW_DEPTH = 3


def _env(name, default=""):
    return os.environ.get(name) or default


def _j(*parts):
    return os.path.join(*parts)


def roots():
    """Category -> list of folders to walk. Order matters: an earlier root owns its tree."""
    h = HOME
    if IS_MAC:
        lib = _j(h, "Library")
        return {
            "caches": [_j(lib, "Caches"), _j(lib, "Logs")],
            "dev": [_j(lib, "Developer"), _j(h, ".npm"), _j(h, ".cargo"), _j(h, ".rustup"), _j(h, ".gradle"),
                    _j(h, ".m2"), _j(h, ".pyenv"), _j(h, ".conda"), _j(h, "miniconda3"), _j(h, "anaconda3"),
                    _j(h, ".nvm"), _j(h, ".bun"), _j(h, "go"), _j(h, ".docker"), _j(h, ".cache"),
                    _j(lib, "pnpm"), _j(lib, "Containers", "com.docker.docker"), _j(h, "Developer"),
                    _j(h, ".android"), _j(lib, "Android")],
            "trash": [_j(h, ".Trash")],
            "apps": ["/Applications", _j(h, "Applications")],
            "photos": [_j(h, "Pictures")],
            "movies": [_j(h, "Movies")],
            "music": [_j(h, "Music")],
            "docs": [_j(h, "Documents"), _j(h, "Desktop"), _j(h, "Downloads"),
                     _j(lib, "Mobile Documents")],
        }
    if IS_WIN:
        local = _env("LOCALAPPDATA", _j(h, "AppData", "Local"))
        roaming = _env("APPDATA", _j(h, "AppData", "Roaming"))
        pf = _env("ProgramFiles", r"C:\Program Files")
        pf86 = _env("ProgramFiles(x86)", r"C:\Program Files (x86)")
        return {
            "caches": [_env("TEMP", _j(local, "Temp")), _j(local, "Microsoft", "Windows", "INetCache"),
                       _j(local, "CrashDumps"), _j(local, "Microsoft", "Windows", "WER"),
                       _j(local, "Google", "Chrome", "User Data"), _j(local, "Microsoft", "Edge", "User Data"),
                       _j(local, "Mozilla", "Firefox", "Profiles"), _j(local, "D3DSCache"),
                       _j(local, "NVIDIA", "DXCache"), _j(local, "NVIDIA", "GLCache")],
            "dev": [_j(local, "npm-cache"), _j(roaming, "npm-cache"), _j(local, "pip"), _j(local, "Yarn"),
                    _j(local, "pnpm"), _j(h, ".nuget"), _j(h, ".gradle"), _j(h, ".cargo"), _j(h, ".rustup"),
                    _j(h, ".m2"), _j(h, ".conda"), _j(h, "miniconda3"), _j(h, "anaconda3"), _j(h, ".android"),
                    _j(local, "Android"), _j(h, "go"), _j(h, ".vscode"), _j(local, "Docker"), _j(h, "source")],
            "trash": [],  # measured with SHQueryRecycleBin, not walked
            "apps": [pf, pf86, _j(local, "Programs")],
            "photos": [_j(h, "Pictures")],
            "movies": [_j(h, "Videos")],
            "music": [_j(h, "Music")],
            "docs": [_j(h, "Documents"), _j(h, "Desktop"), _j(h, "Downloads"), _j(h, "OneDrive")],
        }
    return {
        "caches": [_j(h, ".cache")],
        "dev": [_j(h, ".npm"), _j(h, ".cargo"), _j(h, ".rustup"), _j(h, ".gradle")],
        "trash": [_j(h, ".local", "share", "Trash")],
        "apps": [],
        "photos": [_j(h, "Pictures")],
        "movies": [_j(h, "Videos")],
        "music": [_j(h, "Music")],
        "docs": [_j(h, "Documents"), _j(h, "Desktop"), _j(h, "Downloads")],
    }


def disk_root():
    if IS_WIN:
        return os.path.splitdrive(HOME)[0] + "\\"
    if IS_MAC and os.path.isdir("/System/Volumes/Data"):
        return "/System/Volumes/Data"
    return "/"


def disk_usage(path=None):
    u = shutil.disk_usage(path or disk_root())
    return {"total": u.total, "used": u.total - u.free, "free": u.free}


def norm(p):
    p = os.path.normpath(p)
    return os.path.normcase(p) if IS_WIN else p


def pretty(path):
    """~/... for the UI and for anything sent to Claude."""
    if path == HOME:
        return "~"
    if path.startswith(HOME + os.sep):
        return "~" + path[len(HOME):].replace("\\", "/")
    return path


def _alloc(st):
    blocks = getattr(st, "st_blocks", None)
    if blocks is not None:
        return blocks * 512
    return st.st_size


class ScanResult(object):
    def __init__(self):
        self.disk = disk_usage()
        self.sizes = {k: 0 for k in KEYS}
        self.counts = {k: 0 for k in KEYS}
        self.folders = {}          # norm(path) -> bytes, shallow folders and dev folders
        self.dev_folders = []      # [{path, size, mtime, kind}]
        self.top = []              # heap of (size, path, mtime, atime, cat)
        self.denied = []           # folders we weren't allowed to read
        self.started = time.time()
        self.finished = None
        self.engine = "walk"
        self.current = ""

    def largest(self, n=TOP_FILES):
        return [{"size": s, "path": p, "mtime": m, "atime": a, "cat": c}
                for s, p, m, a, c in sorted(self.top, reverse=True)[:n]]

    def folder_size(self, path):
        return self.folders.get(norm(path))

    def finish(self):
        measured = sum(v for k, v in self.sizes.items() if k != "system")
        self.disk = disk_usage()
        self.sizes["system"] = max(0, self.disk["used"] - measured)
        self.finished = time.time()

    def public(self):
        return {"disk": self.disk, "sizes": dict(self.sizes), "denied": [pretty(d) for d in self.denied[:20]],
                "denied_count": len(self.denied), "engine": self.engine,
                "seconds": round((self.finished or time.time()) - self.started, 1), "done": self.finished is not None}


class Scanner(object):
    """Walks the category roots on a few threads. progress(result) is called a few times a second."""

    def __init__(self, progress=None, threads=6, only=None):
        self._progress = progress
        self._only = set(only) if only else None
        self._threads = threads
        self._lock = threading.Lock()
        self._seen = set()
        self._cancel = False
        self.result = ScanResult()

    def cancel(self):
        self._cancel = True

    def run(self):
        r = self.result
        plan = roots()
        owned = {}
        for cat in ("caches", "dev", "trash", "apps", "photos", "movies", "music", "docs"):
            for p in plan.get(cat, []):
                n = norm(p)
                if n not in owned and os.path.isdir(p):
                    owned[n] = (cat, p)
        self._owned = set(owned)
        if self._only:
            owned = {n: cp for n, cp in owned.items() if cp[0] in self._only}
        ticker = threading.Thread(target=self._tick, daemon=True)
        ticker.start()
        # Biggest trees first so the threads finish together.
        jobs = sorted(owned.values(), key=lambda cp: 0 if cp[0] in ("apps", "docs", "photos", "dev") else 1)
        with ThreadPoolExecutor(max_workers=self._threads) as ex:
            list(ex.map(lambda cp: self._walk_root(cp[1], cp[0]), jobs))
        if IS_WIN:
            try:
                from . import winshell
                size, count = winshell.recycle_bin_size()
                r.sizes["trash"] += size
                r.counts["trash"] += count
            except Exception:
                pass
        r.finish()
        self._cancel = True
        self._emit()
        return r

    def _tick(self):
        while not self._cancel:
            time.sleep(0.25)
            self._emit()

    def _emit(self):
        if self._progress:
            try:
                self._progress(self.result)
            except Exception:
                pass

    def _add_file(self, cat, path, st):
        size = _alloc(st)
        if not IS_WIN and st.st_nlink > 1:
            key = (st.st_dev, st.st_ino)
            with self._lock:
                if key in self._seen:
                    return 0
                self._seen.add(key)
        r = self.result
        if size > 50 * 1024 * 1024:
            item = (size, path, st.st_mtime, st.st_atime, cat)
            with self._lock:
                if len(r.top) < TOP_FILES:
                    heapq.heappush(r.top, item)
                elif size > r.top[0][0]:
                    heapq.heapreplace(r.top, item)
        return size

    def _walk_root(self, root, cat):
        self._walk(root, cat, 0, None)

    def _walk(self, path, cat, depth, dev_kind):
        """Returns the bytes under path. Counts into cat (or Developer inside a dev folder)."""
        if self._cancel and self.result.finished:
            return 0
        r = self.result
        total = 0
        files = 0
        r.current = path
        try:
            it = os.scandir(path)
        except PermissionError:
            r.denied.append(path)
            return 0
        except OSError:
            return 0
        subdirs = []
        names = None
        with it:
            for e in it:
                try:
                    if e.is_symlink():
                        continue
                    if e.is_dir(follow_symlinks=False):
                        subdirs.append(e)
                    else:
                        st = e.stat(follow_symlinks=False)
                        if IS_WIN and (getattr(st, "st_file_attributes", 0) & 0x400):  # reparse point
                            continue
                        total += self._add_file("dev" if dev_kind else cat, e.path, st)
                        files += 1
                except OSError:
                    continue
        counted_cat = "dev" if dev_kind else cat
        with self._lock:
            r.sizes[counted_cat] += total
            r.counts[counted_cat] += files
        for e in subdirs:
            child = e.path
            n = norm(child)
            if n in self._owned:
                continue  # another category walks it
            kind = dev_kind
            if not kind:
                if e.name in DEV_DIRS:
                    kind = e.name
                elif e.name in DEV_BUILD_DIRS:
                    if names is None:
                        try:
                            names = set(os.listdir(path))
                        except OSError:
                            names = set()
                    if names & set(DEV_BUILD_DIRS[e.name]):
                        kind = e.name
            sub = self._walk(child, cat, depth + 1, kind)
            total += sub
            if kind and not dev_kind:
                # The outermost dev folder: its bytes were counted as Developer inside the walk.
                # Remember it for cleanup.
                try:
                    mtime = _project_mtime(child)
                except OSError:
                    mtime = 0
                with self._lock:
                    r.dev_folders.append({"path": child, "size": sub, "mtime": mtime, "kind": kind})
                    r.folders[n] = sub
            elif depth < SHALLOW_DEPTH:
                with self._lock:
                    r.folders[n] = sub
        if depth == 0:
            with self._lock:
                r.folders[norm(path)] = total
        return total


def _project_mtime(dev_dir):
    """When the project that owns a dev folder was last touched: the newest of the folder and its siblings."""
    parent = os.path.dirname(dev_dir)
    newest = os.stat(dev_dir).st_mtime
    try:
        with os.scandir(parent) as it:
            for e in it:
                try:
                    newest = max(newest, e.stat(follow_symlinks=False).st_mtime)
                except OSError:
                    pass
    except OSError:
        pass
    return newest


def measure(path):
    """Size of one path, walked on the spot (for rule paths the scan didn't record)."""
    try:
        st = os.lstat(path)
    except OSError:
        return 0
    if not stat.S_ISDIR(st.st_mode):
        return _alloc(st)
    total = 0
    stack = [path]
    while stack:
        p = stack.pop()
        try:
            with os.scandir(p) as it:
                for e in it:
                    try:
                        if e.is_symlink():
                            continue
                        if e.is_dir(follow_symlinks=False):
                            stack.append(e.path)
                        else:
                            total += _alloc(e.stat(follow_symlinks=False))
                    except OSError:
                        pass
        except OSError:
            pass
    return total
