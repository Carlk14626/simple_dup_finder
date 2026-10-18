import os
import shutil
import tempfile
import unittest

import simple_dup_finder


class TestDuplicateFinder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, path, content):
        full = os.path.join(self.tmp, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as f:
            f.write(content)
        return full

    def test_no_duplicates_single_size(self):
        a = self._write("a.txt", b"hello")
        b = self._write("b.txt", b"world")
        result = simple_dup_finder.find_duplicates([self.tmp])
        self.assertEqual(result, [])

    def test_no_duplicates_same_size_different_content(self):
        a = self._write("a.txt", b"aaa")
        b = self._write("b.txt", b"bbb")
        result = simple_dup_finder.find_duplicates([self.tmp])
        self.assertEqual(result, [])

    def test_finds_duplicates_by_content(self):
        a = self._write("a.txt", b"duplicate")
        b = self._write("b.txt", b"duplicate")
        result = simple_dup_finder.find_duplicates([self.tmp])
        self.assertEqual(len(result), 1)
        self.assertEqual(set(result[0]), {a, b})

    def test_multiple_distinct_groups(self):
        a1 = self._write("a1.txt", b"group-a")
        a2 = self._write("a2.txt", b"group-a")
        b1 = self._write("b1.txt", b"group-b")
        b2 = self._write("b2.txt", b"group-b")
        result = simple_dup_finder.find_duplicates([self.tmp])
        self.assertEqual(len(result), 2)
        found = {frozenset(g) for g in result}
        self.assertIn(frozenset({a1, a2}), found)
        self.assertIn(frozenset({b1, b2}), found)

    def test_empty_file_grouping(self):
        a = self._write("a.txt", b"")
        b = self._write("b.txt", b"")
        result = simple_dup_finder.find_duplicates([self.tmp])
        self.assertEqual(len(result), 1)
        self.assertEqual(set(result[0]), {a, b})

    def test_nested_directories(self):
        a = self._write("dir1/a.txt", b"content")
        b = self._write("dir2/sub/b.txt", b"content")
        result = simple_dup_finder.find_duplicates([self.tmp])
        self.assertEqual(len(result), 1)
        self.assertEqual(set(result[0]), {a, b})

    def test_direct_file_paths(self):
        a = self._write("a.txt", b"same")
        b = self._write("b.txt", b"same")
        result = simple_dup_finder.find_duplicates([a, b])
        self.assertEqual(len(result), 1)
        self.assertEqual(set(result[0]), {a, b})

    def test_size_only_stage(self):
        a = self._write("a.txt", b"abc")
        b = self._write("b.txt", b"xyz")
        result = simple_dup_finder.find_duplicates_by_size([self.tmp])
        self.assertEqual(len(result), 1)
        self.assertEqual(set(result[0]), {a, b})

    def test_hash_only_stage(self):
        a = self._write("a.txt", b"abc")
        b = self._write("b.txt", b"abc")
        result = simple_dup_finder.find_duplicates_by_hash([self.tmp])
        self.assertEqual(len(result), 1)
        self.assertEqual(set(result[0]), {a, b})

    def test_hash_stage_rejects_same_size_different_content(self):
        a = self._write("a.txt", b"abc")
        b = self._write("b.txt", b"xyz")
        result = simple_dup_finder.find_duplicates_by_hash([self.tmp])
        self.assertEqual(result, [])

    def test_mixed_files_and_dirs(self):
        a = self._write("a.txt", b"content")
        b = self._write("sub/b.txt", b"content")
        result = simple_dup_finder.find_duplicates([a, os.path.join(self.tmp, "sub")])
        self.assertEqual(len(result), 1)
        self.assertEqual(set(result[0]), {a, b})

    def test_nonexistent_path_skipped(self):
        a = self._write("a.txt", b"content")
        b = self._write("b.txt", b"content")
        result = simple_dup_finder.find_duplicates([a, b, os.path.join(self.tmp, "nonexistent")])
        self.assertEqual(len(result), 1)
        self.assertEqual(set(result[0]), {a, b})

    def test_empty_paths_list(self):
        result = simple_dup_finder.find_duplicates([])
        self.assertEqual(result, [])

    def test_empty_directory(self):
        result = simple_dup_finder.find_duplicates([self.tmp])
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
