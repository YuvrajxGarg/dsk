import json
import unittest
from types import SimpleNamespace

from dsk import advisor


class FakeClient(object):
    def __init__(self, answer):
        self.answer = answer
        self.calls = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self.create))

    def create(self, **kw):
        self.calls.append(kw)
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=json.dumps(self.answer))])


GROUPS = [
    {"id": "app-caches", "title": "App caches", "verdict": "safe", "action": "remove", "items": [
        {"path": "/Users/me/Library/Caches/a", "show": "~/Library/Caches/a", "size": 5e9, "mtime": 0, "note": None},
        {"path": "/Users/me/Library/Caches/b", "show": "~/Library/Caches/b", "size": 1e9, "mtime": 0, "note": None}]},
    {"id": "keep-photos", "title": "Photos library", "verdict": "keep", "action": "none", "items": [
        {"path": "/Users/me/Pictures/Photos Library.photoslibrary", "show": "~/Pictures/Photos Library.photoslibrary", "size": 9e10, "mtime": 0}]},
]


class AdvisorTest(unittest.TestCase):
    def test_review_maps_ids_back_to_paths(self):
        fc = FakeClient({"summary": "Clear a.", "items": [
            {"id": "i0", "verdict": "safe", "reason": "Cache."}, {"id": "i1", "verdict": "keep", "reason": "Hmm."},
            {"id": "i9", "verdict": "safe", "reason": "unknown id"}]})
        out = advisor.Advisor(client=fc).review(GROUPS, now=1e9)
        self.assertEqual(out["summary"], "Clear a.")
        self.assertEqual(out["items"]["/Users/me/Library/Caches/a"]["verdict"], "safe")
        self.assertEqual(out["items"]["/Users/me/Library/Caches/b"]["verdict"], "keep")
        self.assertEqual(len(out["items"]), 2)
        sent = fc.calls[0]["messages"][0]["content"]
        # Only shortened paths go out, and things Dsk won't remove aren't sent at all.
        self.assertIn("~/Library/Caches/a", sent)
        self.assertNotIn("/Users/me", sent)
        self.assertNotIn("Photos Library", sent)
        self.assertEqual(fc.calls[0]["model"], advisor.MODEL)
        self.assertEqual(fc.calls[0]["output_config"]["format"]["schema"], advisor.REVIEW_SCHEMA)

    def test_refusal(self):
        fc = FakeClient({})
        fc.beta.messages.create = lambda **kw: SimpleNamespace(stop_reason="refusal", content=[])
        with self.assertRaises(advisor.AdvisorError):
            advisor.Advisor(client=fc).review(GROUPS)

    def test_no_key(self):
        a = advisor.Advisor(api_key=None)
        a._key = None
        import os
        old = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            advisor.get_key = lambda: None
            with self.assertRaises(advisor.AdvisorError):
                a.client()
        finally:
            if old:
                os.environ["ANTHROPIC_API_KEY"] = old


if __name__ == "__main__":
    unittest.main()
