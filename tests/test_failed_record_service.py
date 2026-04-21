# -*- coding: utf-8 -*-
"""FailedRecordService 单元测试"""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.failed_record_service import FailedRecordService


class TestFailedRecordService(unittest.TestCase):

    def test_get_failed_records_empty(self):
        result = FailedRecordService.get_failed_records()
        self.assertTrue(result["success"])
        self.assertIsInstance(result["failed"], list)

    def test_clear_failed_records(self):
        result = FailedRecordService.clear_failed_records()
        self.assertTrue(result["success"])

    def test_get_sources_for_retry_empty(self):
        records, sources = FailedRecordService.get_sources_for_retry()
        self.assertIsInstance(records, list)
        self.assertIsInstance(sources, list)


if __name__ == '__main__':
    unittest.main()
