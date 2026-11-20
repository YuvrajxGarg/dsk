# PyInstaller build recipe for macOS (.app) and Windows (folder with .exe).
#   pyinstaller --noconfirm Dsk.spec
import os
import sys

from PyInstaller.utils.hooks import collect_all

root = SPECPATH
version = open(os.path.join(root, "VERSION")).read().strip()

datas, binaries, hiddenimports = [], [], []
datas += [
    (os.path.join(root, "dsk", "ui"), os.path.join("dsk", "ui")),
    (os.path.join(root, "VERSION"), "."),
]
hiddenimports += ["certifi"]
# Ask Claude: the Anthropic SDK, keyring with its macOS / Windows backends; send2trash for the Trash.
for pkg in ("anthropic", "keyring", "send2trash"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h
hiddenimports += ["keyring.backends.macOS", "keyring.backends.Windows"]
excludes = ["tkinter", "_tkinter", "matplotlib", "scipy", "numpy", "PIL"] if sys.platform == "darwin" else ["matplotlib", "scipy", "numpy", "PIL"]

a = Analysis(
    [os.path.join(root, "Dsk.py")],
    pathex=[root],
    datas=datas,
    binaries=binaries,
    hiddenimports=hiddenimports,
    excludes=excludes,
)
pyz = PYZ(a.pure)
icon = os.path.join(root, "assets", "AppIcon.icns" if sys.platform == "darwin" else "icon.ico")

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="Dsk",
    console=False,
    icon=icon,
)
coll = COLLECT(exe, a.binaries, a.datas, name="Dsk")

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Dsk.app",
        icon=icon,
        bundle_identifier="com.yuvrajgarg.dsk",
        version=version,
        info_plist={
            "CFBundleShortVersionString": version,
            "CFBundleVersion": version,
            "CFBundleDisplayName": "Dsk",
            "NSHighResodskionCapable": True,
            "LSMinimumSystemVersion": "11.0",
            "NSRequiresAquaSystemAppearance": False,
            # Measuring these folders makes macOS ask once; without the strings it silently refuses.
            "NSDesktopFolderUsageDescription": "Dsk measures your Desktop to show what's using space.",
            "NSDocumentsFolderUsageDescription": "Dsk measures your Documents to show what's using space.",
            "NSDownloadsFolderUsageDescription": "Dsk measures Downloads to find old installers you can clear.",
            "NSRemovableVolumesUsageDescription": "Dsk measures drives you choose to show what's using space.",
            "NSNetworkVolumesUsageDescription": "Dsk measures drives you choose to show what's using space.",
            "NSAppleEventsUsageDescription": "Dsk asks Finder to empty the Trash when you choose Empty Trash.",
        },
    )
