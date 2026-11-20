"""Windows Recycle Bin: size and emptying, through shell32 (no admin needed)."""

import ctypes
from ctypes import wintypes


class _SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("i64Size", ctypes.c_longlong), ("i64NumItems", ctypes.c_longlong)]


def recycle_bin_size(drive=None):
    """(bytes, items) across all drives, or one drive like 'C:\\'."""
    info = _SHQUERYRBINFO()
    info.cbSize = ctypes.sizeof(info)
    hr = ctypes.windll.shell32.SHQueryRecycleBinW(drive, ctypes.byref(info))
    if hr != 0:
        raise OSError("SHQueryRecycleBin failed (0x%08x)" % (hr & 0xFFFFFFFF))
    return int(info.i64Size), int(info.i64NumItems)


def empty_recycle_bin():
    SHERB_NOCONFIRMATION, SHERB_NOPROGRESSUI, SHERB_NOSOUND = 0x1, 0x2, 0x4
    hr = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND)
    # S_OK, or E_UNEXPECTED when it's already empty.
    if hr not in (0, -2147418113):
        raise OSError("Couldn't empty the Recycle Bin (0x%08x)" % (hr & 0xFFFFFFFF))
