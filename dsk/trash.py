"""Removing things. Everything goes to the Trash / Recycle Bin unless the user turned that off,
and nothing outside the user's own folders (plus a few known system temp folders) can be touched."""

import os
import shutil
import stat
import subprocess

from .scan import HOME, IS_MAC, IS_WIN, norm, roots


def _never():
    """Never removed, whatever a rule or a click asks for."""
    return {norm(p) for p in [
        "/", "/System", "/Library", "/Applications", "/Users", "/private", "/usr", "/bin", "/sbin", "/etc", "/var",
        "/Volumes", HOME, os.path.join(HOME, "Library"), os.path.join(HOME, "Documents"), os.path.join(HOME, "Desktop"),
        os.path.join(HOME, "Downloads"), os.path.join(HOME, "Pictures"), os.path.join(HOME, "Movies"),
        os.path.join(HOME, "Music"), os.path.join(HOME, "Videos"), os.path.join(HOME, "Library", "Caches"),
        os.path.join(HOME, ".Trash"), os.path.join(HOME, "AppData"), os.path.join(HOME, "AppData", "Local"),
        os.path.join(HOME, "AppData", "Roaming"), os.path.join(HOME, "OneDrive"),
        os.environ.get("TEMP", "/nonexistent-temp"), os.environ.get("SystemRoot", r"C:\Windows"),
        os.environ.get("ProgramFiles", r"C:\Program Files"), os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
    ]}


class NotAllowed(Exception):
    pass


def _allowed_bases():
    bases = [HOME]
    if IS_WIN:
        bases.append(os.environ.get("TEMP", ""))
        bases.append(os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "Temp"))
    if IS_MAC:
        bases.append("/Applications")  # apps the user drags to the Trash themselves, from Large files
    return [norm(b) for b in bases if b]


def check(path):
    """Raises NotAllowed unless path is something Dsk may remove."""
    if not path or not os.path.isabs(path):
        raise NotAllowed("Not a full path: %r" % path)
    n = norm(os.path.abspath(path))
    if n in _never():
        raise NotAllowed("%s is a folder Dsk never removes" % path)
    for cat_roots in roots().values():
        if n in {norm(r) for r in cat_roots}:
            raise NotAllowed("%s is a whole category folder; Dsk only removes what's inside it" % path)
    if not any(n.startswith(b + os.sep) for b in _allowed_bases()):
        raise NotAllowed("%s is outside your own folders" % path)
    if not os.path.lexists(path):
        raise NotAllowed("%s is already gone" % path)


def to_trash(path):
    from send2trash import send2trash

    check(path)
    send2trash(path)


def delete_now(path):
    check(path)

    def onerror(func, p, exc):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except OSError:
            pass

    if os.path.isdir(path) and not os.path.islink(path):
        shutil.rmtree(path, onerror=onerror)
    else:
        os.remove(path)


def remove(paths, use_trash=True, progress=None):
    """Removes each path. Returns (done, failed) where failed is [(path, reason)]."""
    done, failed = [], []
    for i, p in enumerate(paths):
        try:
            (to_trash if use_trash else delete_now)(p)
            done.append(p)
        except NotAllowed as e:
            failed.append((p, str(e)))
        except Exception as e:  # in use, permission, ...
            failed.append((p, _reason(e)))
        if progress:
            progress(i + 1, len(paths), p)
    return done, failed


def _reason(e):
    s = str(e) or e.__class__.__name__
    if isinstance(e, PermissionError) or "ermission" in s or "Access is denied" in s:
        return "In use or not allowed"
    return s


def empty_trash():
    """Empties the Trash / Recycle Bin. Permanent."""
    if IS_WIN:
        from . import winshell

        winshell.empty_recycle_bin()
        return
    if IS_MAC:
        t = os.path.join(HOME, ".Trash")
        try:
            names = os.listdir(t)
        except PermissionError:
            names = None
        if names is None:
            # No Full Disk Access: ask Finder, which owns the Trash.
            r = subprocess.run(["osascript", "-e", 'tell application "Finder" to empty trash'],
                               capture_output=True, text=True, timeout=600)
            if r.returncode != 0:
                raise OSError(r.stderr.strip() or "Finder couldn't empty the Trash")
            return
        for name in names:
            p = os.path.join(t, name)
            try:
                if os.path.isdir(p) and not os.path.islink(p):
                    shutil.rmtree(p, ignore_errors=True)
                else:
                    os.remove(p)
            except OSError:
                pass
        return
    t = os.path.join(HOME, ".local", "share", "Trash")
    for sub in ("files", "info"):
        shutil.rmtree(os.path.join(t, sub), ignore_errors=True)
