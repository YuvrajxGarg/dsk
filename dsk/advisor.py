"""Optional "Ask Claude": a second opinion on what's safe to delete.

Only paths (with your home folder shortened to ~), sizes, ages and, for "What is
this?", the names of the biggest things inside a folder are sent. File contents
never leave the computer. Claude's answer only changes the advice shown; Dsk
still removes nothing until you press the button, and still sends it to the Trash.

The API key is the user's own, kept in the OS keychain (macOS Keychain, Windows
Credential Manager) or read from ANTHROPIC_API_KEY.
"""

import json
import os
import sys
import time

from .scan import pretty

MODEL = "claude-opus-5-5"
KEYRING_SERVICE = "Dsk"
KEYRING_USER = "anthropic-api-key"
MAX_ITEMS = 160


class AdvisorError(Exception):
    pass


# ---- API key -----------------------------------------------------------------

def get_key():
    env = os.environ.get("ANTHROPIC_API_KEY")
    if env:
        return env.strip()
    try:
        import keyring

        return keyring.get_password(KEYRING_SERVICE, KEYRING_USER)
    except Exception:
        return None


def set_key(key):
    import keyring

    key = (key or "").strip()
    if key:
        keyring.set_password(KEYRING_SERVICE, KEYRING_USER, key)
    else:
        try:
            keyring.delete_password(KEYRING_SERVICE, KEYRING_USER)
        except Exception:
            pass


def has_key():
    return bool(get_key())


def key_hint():
    k = get_key()
    return ("…" + k[-4:]) if k and len(k) > 8 else ""


# ---- helpers -----------------------------------------------------------------

def human(n):
    n = float(n or 0)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1000 or unit == "TB":
            return ("%d %s" % (n, unit)) if unit == "B" else ("%.1f %s" % (n, unit))
        n /= 1000.0


def _age(ts, now):
    if not ts:
        return "unknown"
    d = int((now - ts) / 86400)
    return "today" if d <= 0 else "%d days" % d


def _os_name():
    return "macOS" if sys.platform == "darwin" else "Windows" if os.name == "nt" else "Linux"


VERDICTS = ["safe", "review", "keep"]

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "verdict": {"type": "string", "enum": VERDICTS},
                    "reason": {"type": "string"},
                },
                "required": ["id", "verdict", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["summary", "items"],
    "additionalProperties": False,
}

EXPLAIN_SCHEMA = {
    "type": "object",
    "properties": {
        "what": {"type": "string"},
        "verdict": {"type": "string", "enum": VERDICTS},
        "reason": {"type": "string"},
        "how": {"type": "string"},
    },
    "required": ["what", "verdict", "reason", "how"],
    "additionalProperties": False,
}

SYSTEM = """You help someone free up disk space on their {os} computer with Dsk, a disk cleanup app.
You only see paths, sizes and ages, never file contents.

For each item give a verdict:
- "safe": rebuildable or disposable (caches, logs, build output, package caches, crash dumps,
  installers for apps that are clearly installed). Removing it loses nothing the person made.
- "review": probably fine, but only the person can know (old downloads, big media files,
  backups, old project dependencies, archives).
- "keep": removing it would lose personal work, break an app or the system, or there's a
  better way to free the space (say which in the reason).

Be conservative: when unsure, say "review". Anything that looks like personal photos,
video projects, documents, source code, password or key stores, app libraries (Photos,
Lightroom, Final Cut, Premiere, DaVinci Resolve, Logic, music libraries), virtual machines
or databases is never "safe".
Reasons are one plain sentence, at most 18 words, written for a creator, not an engineer.
Removing goes to the Trash first, so mention when something is quicker to clear from inside its app."""


class Advisor(object):
    def __init__(self, api_key=None, model=MODEL, client=None):
        self.model = model
        self._client = client
        self._key = api_key

    def client(self):
        if self._client is None:
            key = self._key or get_key()
            if not key:
                raise AdvisorError("Add your Claude API key in Settings to ask Claude.")
            try:
                import anthropic
            except ImportError:
                raise AdvisorError("This build of Dsk doesn't include the Claude SDK.")
            self._client = anthropic.Anthropic(api_key=key, timeout=180.0, max_retries=2)
        return self._client

    def _ask(self, text, schema, max_tokens=16000):
        try:
            import anthropic
        except ImportError:
            anthropic = None
        try:
            resp = self.client().beta.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                system=SYSTEM.format(os=_os_name()),
                output_config={"effort": "medium", "format": {"type": "json_schema", "schema": schema}},
                messages=[{"role": "user", "content": text}],
            )
        except AdvisorError:
            raise
        except Exception as e:
            raise AdvisorError(_api_error(e, anthropic, self.model))
        if resp.stop_reason == "refusal":
            raise AdvisorError("Claude declined to review this list.")
        out = next((b.text for b in resp.content if b.type == "text"), "")
        try:
            return json.loads(out)
        except ValueError:
            raise AdvisorError("Claude's answer wasn't readable. Try again.")

    def review(self, groups, now=None):
        """Second opinion on every removable item. Returns {"summary", "items": {path: {verdict, reason}}}."""
        now = now or time.time()
        rows, ids = [], {}
        pool = []
        for g in groups:
            if g["action"] != "remove":
                continue
            for it in g["items"]:
                pool.append((it["size"], g, it))
        pool.sort(key=lambda t: -t[0])
        for n, (size, g, it) in enumerate(pool[:MAX_ITEMS]):
            key = "i%d" % n
            ids[key] = it["path"]
            rows.append("%s | %s | %s | untouched %s | group: %s (we said %s)%s" % (
                key, it["show"], human(size), _age(it["mtime"], now), g["title"], g["verdict"],
                (" | " + it["note"]) if it.get("note") else ""))
        if not rows:
            return {"summary": "Nothing to review.", "items": {}}
        text = ("Here are the biggest things Dsk could remove. Columns: id | path | size | time since last change | "
                "the group Dsk put it in and Dsk's own verdict.\n\n" + "\n".join(rows) +
                "\n\nGive a verdict and reason for every id, and a two-sentence summary of what to clear first.")
        ans = self._ask(text, REVIEW_SCHEMA)
        out = {}
        for r in ans.get("items") or []:
            p = ids.get(r.get("id"))
            if p and r.get("verdict") in VERDICTS:
                out[p] = {"verdict": r["verdict"], "reason": (r.get("reason") or "").strip()}
        return {"summary": (ans.get("summary") or "").strip(), "items": out}

    def explain(self, path, size, children, now=None):
        """What is this file or folder, and can it go? children: [(name, size, is_dir)]."""
        now = now or time.time()
        try:
            mtime = os.lstat(path).st_mtime
        except OSError:
            mtime = 0
        lines = ["Path: %s" % pretty(path), "Size: %s" % human(size), "Last changed: %s ago" % _age(mtime, now)]
        if children:
            lines.append("Biggest things inside:")
            for name, s, is_dir in children[:30]:
                lines.append("  %s%s  %s" % (name, "/" if is_dir else "", human(s)))
        text = "\n".join(lines) + ("\n\nWhat is this, should it be removed, and if the space should be freed some "
                                   "other way, how? Put the 'what' in one sentence and 'how' in one sentence "
                                   "(empty string if just moving it to the Trash is fine).")
        return self._ask(text, EXPLAIN_SCHEMA, max_tokens=4000)


def _api_error(e, anthropic, model):
    if anthropic is not None:
        if isinstance(e, anthropic.AuthenticationError):
            return "Claude didn't accept the API key. Check it in Settings."
        if isinstance(e, anthropic.PermissionDeniedError):
            return "This API key can't use %s." % model
        if isinstance(e, anthropic.RateLimitError):
            return "Claude is rate-limiting this key. Try again in a minute."
        if isinstance(e, anthropic.APIConnectionError):
            return "Couldn't reach Claude. Check the internet connection."
        if isinstance(e, anthropic.APIStatusError):
            return "Claude API error %s: %s" % (e.status_code, getattr(e, "message", e))
    return str(e) or e.__class__.__name__


def children_of(path, limit=30):
    """[(name, size, is_dir)] biggest first, for explain()."""
    from .scan import measure

    out = []
    try:
        with os.scandir(path) as it:
            entries = list(it)[:400]
    except OSError:
        return out
    for e in entries:
        try:
            is_dir = e.is_dir(follow_symlinks=False)
            out.append((e.name, measure(e.path), is_dir))
        except OSError:
            pass
    out.sort(key=lambda t: -t[1])
    return out[:limit]
