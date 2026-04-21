# -*- coding: utf-8 -*-
"""ProcessingState 单元测试"""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.processing_state import ProcessingState


class TestProcessingState(unittest.TestCase):

    def setUp(self):
        ProcessingState.reset()

    def tearDown(self):
        ProcessingState.reset()

    def test_initial_state_is_idle(self):
        state = ProcessingState()
        self.assertEqual(state.get_dict()["status"], "idle")

    def test_start_transitions_to_scanning(self):
        state = ProcessingState()
        state.start()
        self.assertEqual(state.get_dict()["status"], "scanning")

    def test_start_processing_transitions_to_processing(self):
        state = ProcessingState()
        state.start()
        state.start_processing(5)
        self.assertEqual(state.get_dict()["status"], "processing")
        self.assertEqual(state.get_dict()["total_files"], 5)

    def test_update_progress(self):
        state = ProcessingState()
        state.start()
        state.start_processing(10)
        state.update_progress(3, "file.txt", 30)
        d = state.get_dict()
        self.assertEqual(d["processed_files_count"], 3)
        self.assertEqual(d["current_file"], "file.txt")
        self.assertEqual(d["progress"], 30)

    def test_add_result(self):
        state = ProcessingState()
        state.start()
        state.add_result("source.txt", "output.md", None, False)
        d = state.get_dict()
        self.assertEqual(len(d["results"]), 1)
        self.assertEqual(d["results"][0]["source"], "source.txt")

    def test_complete_when_not_cancelled(self):
        state = ProcessingState()
        state.start()
        state.start_processing(1)
        state.complete()
        self.assertEqual(state.get_dict()["status"], "completed")

    def test_complete_when_cancelled(self):
        state = ProcessingState()
        state.start()
        state.start_processing(1)
        state.set_cancelled()
        state.complete()
        self.assertEqual(state.get_dict()["status"], "cancelled")

    def test_request_cancel_when_running(self):
        state = ProcessingState()
        state.start()
        state.start_processing(1)
        result = state.request_cancel()
        self.assertTrue(result)

    def test_request_cancel_when_idle(self):
        state = ProcessingState()
        result = state.request_cancel()
        self.assertFalse(result)

    def test_reset_creates_fresh_instance(self):
        state1 = ProcessingState()
        state1.start(total_files=5)
        self.assertEqual(state1.get_dict()["status"], "scanning")

        ProcessingState.reset()
        state2 = ProcessingState()
        self.assertEqual(state2.get_dict()["status"], "idle")


if __name__ == '__main__':
    unittest.main()
