import os
import shutil
import unittest

from dsk import clean, scan, trash
from helpers import MB, fake_mac, mac_home, write


class ScanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = mac_home()
        clean.LARGE_MIN = 50 * MB
        with fake_mac(cls.home):
            cls.r = scan.Scanner().run()
            cls.groups = clean.evaluate(cls.r)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.home, ignore_errors=True)

    def near(self, got, want, slack=1 * MB):
        self.assertTrue(abs(got - want) <= slack, "%d vs %d" % (got, want))

    def test_categories(self):
        s = self.r.sizes
        self.near(s["caches"], 6 * MB)
        # Xcode + npm cache + two node_modules found inside Documents
        self.near(s["dev"], 10 * MB)
        self.near(s["docs"], 5 * MB, 2 * MB)
        self.near(s["movies"], 60 * MB)
        self.near(s["trash"], 1 * MB)
        self.assertGreaterEqual(s["system"], 0)
        self.assertTrue(self.r.finished)

    def test_dev_folders_found_with_project_age(self):
        found = {os.path.basename(os.path.dirname(d["path"])): d for d in self.r.dev_folders}
        self.assertIn("old-site", found)
        self.assertIn("fresh-site", found)
        self.assertLess(found["old-site"]["mtime"], found["fresh-site"]["mtime"])

    def test_largest_files(self):
        top = self.r.largest()
        self.assertEqual(os.path.basename(top[0]["path"]), "big.mov")

    def g(self, gid):
        return next((g for g in self.groups if g["id"] == gid), None)

    def test_groups(self):
        caches = self.g("app-caches")
        self.assertEqual(caches["verdict"], "safe")
        self.assertEqual({i["name"] for i in caches["items"]}, {"com.example.app", "Homebrew"})
        self.assertEqual(self.g("xcode-derived")["items"][0]["name"], "Proj-abc")
        stale = self.g("stale-deps")
        self.assertEqual(len(stale["items"]), 1)
        self.assertIn("old-site", stale["items"][0]["path"])
        inst = self.g("installers")
        self.assertEqual([i["name"] for i in inst["items"]], ["Setup.dmg"])
        big = self.g("large-old")
        self.assertEqual(big["verdict"], "review")
        self.assertEqual(big["items"][0]["name"], "big.mov")
        self.assertEqual(self.g("trash")["action"], "empty_trash")
        order = [g["verdict"] for g in self.groups]
        self.assertEqual(order, sorted(order, key=["safe", "review", "keep"].index))

    def test_summary(self):
        s = clean.summary(self.groups)
        self.assertGreater(s["safe"], 10 * MB)
        self.assertGreater(s["review"], 60 * MB)


class TrashGuardTest(unittest.TestCase):
    def setUp(self):
        self.home = mac_home()

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def test_refuses_dangerous_paths(self):
        with fake_mac(self.home) as h:
            for p in [h, os.path.join(h, "Library"), os.path.join(h, "Library", "Caches"), os.path.join(h, "Documents"),
                      "/", "/System", "/usr/bin", "relative/path", os.path.join(h, "nope")]:
                with self.assertRaises(trash.NotAllowed, msg=p):
                    trash.check(p)

    def test_delete_now_removes_only_the_child(self):
        with fake_mac(self.home) as h:
            target = os.path.join(h, "Library", "Caches", "Homebrew")
            trash.check(target)
            done, failed = trash.remove([target, os.path.join(h, "Documents")], use_trash=False)
            self.assertEqual(done, [target])
            self.assertEqual(len(failed), 1)
            self.assertFalse(os.path.exists(target))
            self.assertTrue(os.path.exists(os.path.join(h, "Library", "Caches", "com.example.app")))
            self.assertTrue(os.path.exists(os.path.join(h, "Documents", "report.pdf")))

    @unittest.skipIf(os.name == "nt", "DirEntry.stat() has no inode numbers on Windows")
    def test_hard_links_counted_once(self):
        with fake_mac(self.home) as h:
            a = write(os.path.join(h, "Documents", "linked.bin"), 8 * MB)
            os.link(a, os.path.join(h, "Documents", "linked-again.bin"))
            r = scan.Scanner().run()
            self.assertLess(r.sizes["docs"], 15 * MB)


if __name__ == "__main__":
    unittest.main()
