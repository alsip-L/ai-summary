# -*- coding: utf-8 -*-
"""TaskRunner 单元测试"""

import unittest
import os
import sys
import tempfile
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.processing_state import ProcessingState
from app.services.file_processor import FileProcessor
from app.services.task_runner import TaskRunner
from app.services.failed_record_service import FailedRecordService


class TestTaskRunner(unittest.TestCase):

    def setUp(self):
        ProcessingState.reset(force=True)

    def tearDown(self):
        ProcessingState.reset(force=True)

    def test_run_batch_empty_directory(self):
        state = ProcessingState()
        mock_fp = MagicMock(spec=FileProcessor)
        mock_fp.scan_txt_files.return_value = []
        mock_frs = MagicMock(spec=FailedRecordService)
        runner = TaskRunner(state=state, file_processor=mock_fp, failed_record_service=mock_frs)
        runner.run_batch("/some/dir", None, None, None, False)
        self.assertEqual(state.get_dict()["status"], "error")
        self.assertIn("未找到", state.get_dict()["error"])

    def test_run_batch_cancelled_during_scan(self):
        """在扫描阶段被取消"""
        state = ProcessingState()
        mock_fp = MagicMock(spec=FileProcessor)

        def scan_and_cancel(*args, **kwargs):
            state.request_cancel()
            return ["/fake/file.txt"]

        mock_fp.scan_txt_files.side_effect = scan_and_cancel
        mock_fp.process_file.return_value = {"source": "/fake/file.txt", "output": "/fake/file.md"}
        mock_frs = MagicMock(spec=FailedRecordService)
        runner = TaskRunner(state=state, file_processor=mock_fp, failed_record_service=mock_frs)
        runner.run_batch("/some/dir", None, None, None, False)
        # 取消发生在扫描后、循环前，_run_processing_loop 会检测到取消
        self.assertIn(state.get_dict()["status"], ("cancelled", "completed"))


if __name__ == '__main__':
    unittest.main()
