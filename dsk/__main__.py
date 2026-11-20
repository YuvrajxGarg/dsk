import os
import sys


def run():
    # A windowed build (no console) has no stdout/stderr; give the CLI somewhere to write.
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-psn"):
        from .cli import main

        sys.exit(main())
    try:
        from .webapp import main
    except ImportError:
        print("The window needs pywebview: pip install -r requirements.txt")
        print("Or use the command line: python Dsk.py scan")
        sys.exit(1)
    main()


if __name__ == "__main__":
    run()
