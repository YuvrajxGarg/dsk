"""A fake home folder laid out like a Mac's, and a context that points Dsk at it."""

import contextlib
import os
import tempfile
import time

from dsk import clean, scan, trash

MB = 1024 * 1024


def write(path, size, age_days=0):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(os.urandom(min(size, 4096)) + b"\0" * max(0, size - 4096))
    if age_days:
        t = time.time() - age_days * 86400
        os.utime(path, (t, t))
    return path


def age(path, days):
    t = time.time() - days * 86400
    os.utime(path, (t, t))


def mac_home():
    h = tempfile.mkdtemp(prefix="dsk-home-")
    L = os.path.join(h, "Library")
    write(os.path.join(L, "Caches", "com.example.app", "blob.bin"), 3 * MB)
    write(os.path.join(L, "Caches", "Homebrew", "pkg.tar"), 2 * MB)
    write(os.path.join(L, "Logs", "app.log"), 1 * MB)
    write(os.path.join(L, "Developer", "Xcode", "DerivedData", "Proj-abc", "Build.o"), 4 * MB)
    write(os.path.join(h, ".npm", "_cacache", "x"), 2 * MB)
    write(os.path.join(h, "Documents", "report.pdf"), 1 * MB)
    write(os.path.join(h, "Documents", "old-site", "package.json"), 100, age_days=120)
    write(os.path.join(h, "Documents", "old-site", "node_modules", "lib", "index.js"), 2 * MB, age_days=120)
    write(os.path.join(h, "Documents", "fresh-site", "node_modules", "lib", "index.js"), 2 * MB)
    write(os.path.join(h, "Downloads", "Setup.dmg"), 3 * MB, age_days=30)
    write(os.path.join(h, "Downloads", "new.dmg"), 1 * MB)
    write(os.path.join(h, "Movies", "big.mov"), 60 * MB, age_days=200)
    write(os.path.join(h, "Pictures", "a.jpg"), 1 * MB)
    write(os.path.join(h, "Music", "song.m4a"), 1 * MB)
    write(os.path.join(h, ".Trash", "gone.txt"), 1 * MB)
    for d in ("old-site", "old-site/node_modules"):
        age(os.path.join(h, "Documents", d), 120)
    return h


@contextlib.contextmanager
def fake_mac(home):
    saved = [(m, m.HOME) for m in (scan, clean, trash)] + [(scan, "IS_MAC"), (clean, "IS_MAC"), (scan, "IS_WIN"), (clean, "IS_WIN"), (trash, "IS_WIN"), (trash, "IS_MAC")]
    old = {(id(m), k): getattr(m, k) for m, k in saved[3:]}
    for m in (scan, clean, trash):
        m.HOME = home
    for m in (scan, clean, trash):
        m.IS_MAC, m.IS_WIN = True, False
    try:
        yield home
    finally:
        for m, h in saved[:3]:
            m.HOME = h
        for m, k in saved[3:]:
            setattr(m, k, old[(id(m), k)])
