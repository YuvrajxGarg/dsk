"""What can be cleared, what to look at first, and what to leave alone.

Each rule turns into a group for the UI:
  verdict "safe"    rebuildable or already-deleted data; ticked by default
  verdict "review"  probably fine to remove, but it's the user's call (old installers,
                    stale project dependencies, big files untouched for months)
  verdict "keep"    shown so the user knows what's taking space and why Dsk won't touch it

Rules only ever list paths; removing them goes through trash.remove(), which
checks every path again.
"""

import glob
import os
import time

from . import scan
from .scan import HOME, IS_MAC, IS_WIN, pretty

DAY = 86400
LARGE_MIN = 500 * 1024 * 1024   # "big files you haven't opened" starts here
INSTALLER_EXTS = (".dmg", ".pkg", ".iso", ".msi", ".exe", ".zip", ".xip", ".appimage")


def _j(*p):
    return os.path.join(*p)


def _env(name, default):
    return os.environ.get(name) or default


# ---------------------------------------------------------------------------
# rule tables
# ---------------------------------------------------------------------------

def _mac_rules():
    lib = _j(HOME, "Library")
    dev = _j(lib, "Developer")
    return [
        dict(id="app-caches", verdict="safe", cat="caches", kind="children", base=_j(lib, "Caches"),
             title="App caches",
             detail="Temporary files apps keep to load faster. They rebuild them when needed, so an app may open a little slower the first time."),
        dict(id="logs", verdict="safe", cat="caches", kind="children", base=_j(lib, "Logs"),
             title="Logs", detail="Diagnostic logs apps write as they run. Nothing reads them unless you're troubleshooting."),
        dict(id="xcode-derived", verdict="safe", cat="dev", kind="children", base=_j(dev, "Xcode", "DerivedData"),
             title="Xcode build files", detail="Intermediate build output. Xcode makes it again on the next build."),
        dict(id="sim-caches", verdict="safe", cat="dev", kind="paths",
             paths=[_j(dev, "CoreSimulator", "Caches")],
             title="Simulator caches", detail="Caches for iOS simulators. Rebuilt when a simulator boots."),
        dict(id="dev-caches", verdict="safe", cat="dev", kind="paths",
             paths=[_j(HOME, ".npm", "_cacache"), _j(HOME, ".cargo", "registry", "cache"), _j(HOME, ".gradle", "caches"),
                    _j(lib, "pnpm", "store"), _j(HOME, ".cache", "pip"), _j(HOME, ".cache", "huggingface", "xet"),
                    _j(HOME, ".bun", "install", "cache")],
             title="Package manager caches",
             detail="Downloaded copies of packages (npm, cargo, Gradle, pnpm, pip). They're fetched again when a project needs them."),
        dict(id="device-support", verdict="review", cat="dev", kind="children",
             base=_j(dev, "Xcode", "iOS DeviceSupport"),
             title="iPhone debug symbols",
             detail="Xcode copies these from each iPhone or iPad you plug in. Old iOS versions are dead weight; Xcode copies them again if needed."),
        dict(id="xcode-archives", verdict="review", cat="dev", kind="children", base=_j(dev, "Xcode", "Archives"),
             title="Xcode archives", detail="Builds you archived for the App Store. Keep the ones for versions you still support."),
        dict(id="simulators", verdict="review", cat="dev", kind="children", base=_j(dev, "CoreSimulator", "Devices"),
             title="iOS simulators", detail="Each simulator is a whole device with its own apps and data. Xcode can make new ones any time."),
        dict(id="stale-deps", verdict="review", cat="dev", kind="dev_folders", days=30,
             title="Project dependencies you haven't touched in a month",
             detail="node_modules, virtual environments and build folders in projects untouched for 30+ days. npm install (or similar) brings them back."),
        dict(id="ios-backups", verdict="review", cat="system", kind="children",
             base=_j(lib, "Application Support", "MobileSync", "Backup"),
             title="iPhone and iPad backups",
             detail="Local Finder backups. Remove one only if the device is backed up to iCloud or you no longer need it."),
        dict(id="mail-downloads", verdict="safe", cat="caches", kind="children",
             base=_j(lib, "Containers", "com.apple.mail", "Data", "Library", "Mail Downloads"),
             title="Mail attachment copies",
             detail="Copies Mail made when you opened attachments. The originals stay in your email."),
        dict(id="installers", verdict="review", cat="docs", kind="installers", base=_j(HOME, "Downloads"), days=7,
             title="Installers in Downloads",
             detail="Disk images, packages and zips more than a week old. Once an app is installed, its installer isn't needed."),
        dict(id="large-old", verdict="review", cat="docs", kind="large", days=90,
             title="Big files you haven't opened in 3 months",
             detail="Files over 500 MB in your own folders that haven't been opened for 90 days. Only you know if they matter."),
        dict(id="trash", verdict="safe", cat="trash", kind="trash", title="Trash",
             detail="Things you've already deleted. Emptying the Trash removes them for good."),
        # leave alone
        dict(id="keep-photos", verdict="keep", cat="photos", kind="info",
             paths=sorted(glob.glob(_j(HOME, "Pictures", "*.photoslibrary"))),
             title="Photos library",
             detail="Your photo library. Manage it in Photos: turn on Optimise Mac Storage in Photos settings to keep full-size originals only in iCloud."),
        dict(id="keep-icloud", verdict="keep", cat="docs", kind="info", paths=[_j(lib, "Mobile Documents")],
             title="iCloud Drive", detail="Files synced with iCloud. Deleting here deletes them everywhere."),
        dict(id="keep-support", verdict="keep", cat="system", kind="info",
             paths=[_j(lib, "Application Support"), _j(lib, "Containers"), _j(lib, "Group Containers")],
             title="App data", detail="Settings, libraries and documents apps keep for you. Remove an app's data by uninstalling the app instead."),
        dict(id="keep-docker", verdict="keep", cat="dev", kind="info",
             paths=[_j(lib, "Containers", "com.docker.docker")],
             title="Docker", detail="Docker's disk image. Free space from inside Docker (docker system prune) rather than deleting the file."),
        dict(id="keep-system", verdict="keep", cat="system", kind="info", paths=[],
             title="macOS and system data",
             detail="macOS itself, its snapshots, swap and other system files. macOS manages these; deleting them by hand can break things."),
    ]


def _win_rules():
    local = _env("LOCALAPPDATA", _j(HOME, "AppData", "Local"))
    roaming = _env("APPDATA", _j(HOME, "AppData", "Roaming"))
    windir = _env("SystemRoot", r"C:\Windows")
    browsers = []
    for prof in glob.glob(_j(local, "Google", "Chrome", "User Data", "*")) + \
            glob.glob(_j(local, "Microsoft", "Edge", "User Data", "*")) + \
            glob.glob(_j(local, "BraveSoftware", "Brave-Browser", "User Data", "*")):
        for sub in ("Cache", "Code Cache", "GPUCache", _j("Service Worker", "CacheStorage")):
            browsers.append(_j(prof, sub))
    browsers += glob.glob(_j(local, "Mozilla", "Firefox", "Profiles", "*", "cache2"))
    for app in ("discord", "Slack", "Code", "Microsoft\\Teams", "Spotify"):
        for sub in ("Cache", "Code Cache", "GPUCache"):
            browsers.append(_j(roaming, app, sub))
    return [
        dict(id="temp", verdict="safe", cat="caches", kind="children", base=_env("TEMP", _j(local, "Temp")),
             title="Temporary files",
             detail="Files apps and installers left in your Temp folder. Anything still in use is skipped."),
        dict(id="browser-caches", verdict="safe", cat="caches", kind="paths", paths=browsers,
             title="Browser and app caches",
             detail="Cached web pages and images from Chrome, Edge, Brave, Firefox, Discord, Slack and others. Close the browser first so nothing is in use."),
        dict(id="inet", verdict="safe", cat="caches", kind="children", base=_j(local, "Microsoft", "Windows", "INetCache"),
             title="Windows web cache", detail="Cached files from Windows' built-in web components."),
        dict(id="crash", verdict="safe", cat="caches", kind="paths",
             paths=[_j(local, "CrashDumps"), _j(local, "Microsoft", "Windows", "WER")],
             title="Crash reports", detail="Memory dumps and error reports from apps that crashed. Only useful for debugging."),
        dict(id="thumbs", verdict="safe", cat="caches", kind="glob",
             paths=[_j(local, "Microsoft", "Windows", "Explorer", "thumbcache_*.db")],
             title="Thumbnail cache", detail="Explorer's picture previews. Rebuilt as you browse folders."),
        dict(id="shader", verdict="safe", cat="caches", kind="paths",
             paths=[_j(local, "D3DSCache"), _j(local, "NVIDIA", "DXCache"), _j(local, "NVIDIA", "GLCache"),
                    _j(local, "AMD", "DxCache")],
             title="Graphics shader caches", detail="Compiled shaders. Games rebuild them, so the first launch after may stutter briefly."),
        dict(id="dev-caches", verdict="safe", cat="dev", kind="paths",
             paths=[_j(local, "npm-cache"), _j(roaming, "npm-cache"), _j(local, "pip", "Cache"), _j(local, "Yarn", "Cache"),
                    _j(local, "pnpm", "store"), _j(HOME, ".cargo", "registry", "cache"), _j(HOME, ".gradle", "caches")],
             title="Package manager caches",
             detail="Downloaded copies of packages (npm, pip, Yarn, pnpm, cargo, Gradle). Fetched again when needed."),
        dict(id="win-temp", verdict="review", cat="caches", kind="children", base=_j(windir, "Temp"),
             title="Windows temp folder", detail="System-wide temporary files. Some need admin rights; those are skipped."),
        dict(id="stale-deps", verdict="review", cat="dev", kind="dev_folders", days=30,
             title="Project dependencies you haven't touched in a month",
             detail="node_modules, virtual environments and build folders in projects untouched for 30+ days. npm install (or similar) brings them back."),
        dict(id="nuget", verdict="review", cat="dev", kind="paths", paths=[_j(HOME, ".nuget", "packages")],
             title="NuGet packages", detail="Downloaded .NET packages. Visual Studio restores them on the next build."),
        dict(id="installers", verdict="review", cat="docs", kind="installers", base=_j(HOME, "Downloads"), days=7,
             title="Installers in Downloads",
             detail="Setup files, disk images and zips more than a week old. Once a program is installed, its installer isn't needed."),
        dict(id="large-old", verdict="review", cat="docs", kind="large", days=90,
             title="Big files you haven't opened in 3 months",
             detail="Files over 500 MB in your own folders not opened for 90 days. Only you know if they matter."),
        dict(id="trash", verdict="safe", cat="trash", kind="trash", title="Recycle Bin",
             detail="Things you've already deleted. Emptying the Recycle Bin removes them for good."),
        dict(id="keep-system", verdict="keep", cat="system", kind="info",
             paths=[_j(windir, "WinSxS"), "C:\\pagefile.sys", "C:\\hiberfil.sys"],
             title="Windows, page file and hibernation",
             detail="Windows manages these. To shrink them use Settings > System > Storage > Cleanup recommendations, or turn hibernation off with powercfg /h off."),
        dict(id="keep-roaming", verdict="keep", cat="system", kind="info", paths=[roaming],
             title="App data (Roaming)", detail="Settings and saved data apps keep for you. Uninstall an app to remove its data."),
        dict(id="keep-onedrive", verdict="keep", cat="docs", kind="info", paths=[_j(HOME, "OneDrive")],
             title="OneDrive", detail="Synced files. Deleting here deletes them in the cloud too; use Free up space in OneDrive instead."),
    ]


def rules():
    return _mac_rules() if IS_MAC else _win_rules() if IS_WIN else []


# ---------------------------------------------------------------------------
# evaluation
# ---------------------------------------------------------------------------

def _size(result, path):
    s = result.folder_size(path) if result else None
    return s if s is not None else scan.measure(path)


def _mtime(path):
    try:
        st = os.lstat(path)
        return st.st_mtime
    except OSError:
        return 0


def _item(result, path, size=None, mtime=None, note=None):
    if size is None:
        size = _size(result, path)
    return {"path": path, "show": pretty(path), "name": os.path.basename(path.rstrip("\\/")) or path,
            "size": size, "mtime": _mtime(path) if mtime is None else mtime, "note": note}


def _children(result, base):
    out = []
    try:
        with os.scandir(base) as it:
            for e in it:
                if e.name in (".DS_Store", ".localized"):
                    continue
                out.append(_item(result, e.path))
    except OSError:
        pass
    return out


def _user_path(path):
    """Somewhere the user keeps their own files (not app internals or the system)."""
    n = scan.norm(path)
    lib = scan.norm(_j(HOME, "Library"))
    appdata = scan.norm(_j(HOME, "AppData"))
    if not n.startswith(scan.norm(HOME) + os.sep):
        return False
    return not (n.startswith(lib + os.sep) or n.startswith(appdata + os.sep) or "/." in path.replace("\\", "/")[len(HOME):])


def evaluate(result, now=None):
    """Groups for the UI, biggest first within each verdict."""
    now = now or time.time()
    groups = []
    taken = set()
    for rule in rules():
        kind = rule["kind"]
        items = []
        size = 0
        if kind == "children":
            items = _children(result, rule["base"])
        elif kind == "paths":
            items = [_item(result, p) for p in rule["paths"] if os.path.isdir(p) or os.path.isfile(p)]
        elif kind == "glob":
            for pat in rule["paths"]:
                items += [_item(result, p) for p in glob.glob(pat)]
        elif kind == "dev_folders":
            cutoff = now - rule["days"] * DAY
            for d in (result.dev_folders if result else []):
                if d["mtime"] and d["mtime"] < cutoff and d["size"] > 1024 * 1024:
                    age = int((now - d["mtime"]) / DAY)
                    items.append(_item(result, d["path"], d["size"], d["mtime"],
                                       "%s · project untouched for %d days" % (d["kind"], age)))
        elif kind == "installers":
            cutoff = now - rule["days"] * DAY
            try:
                with os.scandir(rule["base"]) as it:
                    for e in it:
                        if e.name.lower().endswith(INSTALLER_EXTS) or (IS_MAC and e.name.endswith(".app.zip")):
                            st = e.stat(follow_symlinks=False)
                            if st.st_mtime < cutoff:
                                items.append(_item(result, e.path, scan._alloc(st), st.st_mtime))
            except OSError:
                pass
        elif kind == "large":
            cutoff = now - rule["days"] * DAY
            for f in (result.largest() if result else []):
                used = max(f["mtime"] or 0, f["atime"] or 0)
                if f["size"] >= LARGE_MIN and used < cutoff and _user_path(f["path"]):
                    items.append(_item(result, f["path"], f["size"], f["mtime"],
                                       "Last opened %d days ago" % int((now - used) / DAY)))
        elif kind == "trash":
            size = result.sizes.get("trash", 0) if result else 0
        elif kind == "info":
            for p in rule["paths"]:
                if os.path.exists(p):
                    items.append(_item(result, p))
            if rule["id"] == "keep-system" and result:
                size = result.sizes.get("system", 0)
        # A path belongs to the first group that lists it (e.g. Mail Downloads vs. Containers).
        fresh = []
        for it in items:
            n = scan.norm(it["path"])
            if rule["verdict"] != "keep" and n in taken:
                continue
            taken.add(n)
            fresh.append(it)
        items = sorted(fresh, key=lambda i: -i["size"])
        if kind not in ("trash",) and not (rule["id"] == "keep-system" and size):
            size = sum(i["size"] for i in items)
        if size <= 0 and rule["verdict"] != "keep":
            continue
        if rule["verdict"] == "keep" and size <= 0:
            continue
        groups.append({
            "id": rule["id"], "title": rule["title"], "detail": rule["detail"], "verdict": rule["verdict"],
            "cat": rule["cat"], "size": size, "count": len(items) if kind != "trash" else (result.counts.get("trash", 0) if result else 0),
            "action": "empty_trash" if kind == "trash" else ("none" if rule["verdict"] == "keep" else "remove"),
            "items": items[:400], "more": max(0, len(items) - 400),
        })
    order = {"safe": 0, "review": 1, "keep": 2}
    groups.sort(key=lambda g: (order[g["verdict"]], -g["size"]))
    return groups


def summary(groups):
    safe = sum(g["size"] for g in groups if g["verdict"] == "safe")
    review = sum(g["size"] for g in groups if g["verdict"] == "review")
    return {"safe": safe, "review": review}
