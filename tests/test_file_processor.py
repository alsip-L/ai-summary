# -*- coding: utf-8 -*-
"""FileProcessor 单元测试"""

import unittest
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.file_processor import FileProcessor


class TestFileProcessor(unittest.TestCase):

    def test_scan_txt_files_finds_txt_files(self):
        tmp_dir = tempfile.mkdtemp()
        try:
            txt_path = os.path.join(tmp_dir, "test.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("hello")
            result = FileProcessor.scan_txt_files(tmp_dir)
            self.assertIn(txt_path, result)
        finally:
            os.unlink(txt_path)
            os.rmdir(tmp_dir)

    def test_scan_txt_files_skips_existing_md(self):
        tmp_dir = tempfile.mkdtemp()
        try:
            txt_path = os.path.join(tmp_dir, "test.txt")
            md_path = os.path.join(tmp_dir, "test.md")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("hello")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write("summary")
            result = FileProcessor.scan_txt_files(tmp_dir, skip_existing=True)
            self.assertNotIn(txt_path, result)
        finally:
            os.unlink(txt_path)
            os.unlink(md_path)
            os.rmdir(tmp_dir)

    def test_scan_txt_files_nonexistent_directory(self):
        with self.assertRaises(ValueError):
            FileProcessor.scan_txt_files("/nonexistent_dir_xyz_12345")

    def test_save_response_creates_md_file(self):
        tmp_dir = tempfile.mkdtemp()
        try:
            txt_path = os.path.join(tmp_dir, "test.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("hello")
            md_path = FileProcessor.save_response(txt_path, "AI summary content")
            self.assertTrue(os.path.exists(md_path))
            with open(md_path, "r", encoding="utf-8") as f:
                self.assertEqual(f.read(), "AI summary content")
        finally:
            os.unlink(txt_path)
            os.unlink(md_path)
            os.rmdir(tmp_dir)


if __name__ == '__main__':
    unittest.main()
