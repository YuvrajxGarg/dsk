"""Command line: python Dsk.py scan | clean [--yes] [--delete] | version"""

import argparse
import sys

from . import __version__, clean, scan, trash
from .advisor import human


def _scan(args):
    if args.wiztree and scan.IS_WIN:
        from . import wiztree
        exe = wiztree.find()
        if exe:
            return wiztree.run(exe, admin=not args.no_admin)
        print("WizTree isn't installed; using the built-in scan.", file=sys.stderr)
    only = [c.strip() for c in (getattr(args, "only", None) or "").split(",") if c.strip()]
    return scan.Scanner(only=only or None).run()


def _selftest(out):
    """For CI: writes which optional parts this build can load."""
    import importlib
    import json

    res = {"version": __version__}
    for mod in ("anthropic", "keyring", "send2trash", "webview"):
        try:
            importlib.import_module(mod)
            res[mod] = True
        except Exception as e:
            res[mod] = False
            res[mod + "_error"] = str(e)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="dsk", description="See what's filling your disk and clear what's safe.")
    p.add_argument("--version", action="version", version="Dsk " + __version__)
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("scan", help="show disk usage by category and what can be cleared")
    s.add_argument("--wiztree", action="store_true", help="Windows: scan with WizTree if it's installed")
    s.add_argument("--no-admin", action="store_true")
    s.add_argument("--json", action="store_true", help="print the result as JSON")
    s.add_argument("--report", metavar="FILE", help="write the JSON result to FILE")
    s.add_argument("--only", metavar="CATS", help="measure only these categories, e.g. caches,trash")
    c = sub.add_parser("clean", help="clear everything marked safe (to the Trash unless --delete)")
    c.add_argument("--yes", action="store_true", help="don't ask first")
    c.add_argument("--delete", action="store_true", help="delete straight away instead of using the Trash")
    c.add_argument("--wiztree", action="store_true")
    c.add_argument("--no-admin", action="store_true")
    sub.add_parser("version")
    st = sub.add_parser("selftest", help=argparse.SUPPRESS)
    st.add_argument("out")
    args = p.parse_args(argv)
    if args.cmd in (None, "version"):
        print("Dsk " + __version__)
        return 0
    if args.cmd == "selftest":
        return _selftest(args.out)

    r = _scan(args)
    groups = clean.evaluate(r)
    if args.cmd == "scan":
        if args.json or args.report:
            import json
            out = json.dumps({"version": __version__, "scan": r.public(),
                              "groups": [dict(g, items=[dict(i) for i in g["items"][:50]]) for g in groups]},
                             indent=1, default=str)
            if args.report:
                with open(args.report, "w", encoding="utf-8") as f:
                    f.write(out)
            else:
                print(out)
            return 0
        d = r.disk
        print("%s of %s used (%s free), scanned in %.1fs" % (human(d["used"]), human(d["total"]), human(d["free"]),
                                                            r.finished - r.started))
        for key, label, _ in scan.CATEGORIES:
            print("  %-12s %10s" % (label, human(r.sizes[key])))
        if r.denied:
            print("  (%d folders couldn't be read)" % len(r.denied))
        print()
        for g in groups:
            print("[%s] %-48s %10s" % (g["verdict"], g["title"], human(g["size"])))
        return 0

    safe = [g for g in groups if g["verdict"] == "safe"]
    total = sum(g["size"] for g in safe)
    print("Safe to clear: %s" % human(total))
    for g in safe:
        print("  %-48s %10s" % (g["title"], human(g["size"])))
    if not safe:
        return 0
    if not args.yes:
        if input("Clear these%s? [y/N] " % ("" if args.delete else " (to the Trash)")).strip().lower() not in ("y", "yes"):
            return 1
    failed = 0
    for g in safe:
        if g["action"] == "empty_trash":
            try:
                trash.empty_trash()
            except Exception as e:
                print("  Trash: %s" % e)
            continue
        _, bad = trash.remove([i["path"] for i in g["items"]], use_trash=not args.delete)
        failed += len(bad)
    print("Done%s." % (", %d skipped (in use or not allowed)" % failed if failed else ""))
    return 0
