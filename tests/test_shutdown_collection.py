from pathlib import Path
import tempfile
import unittest
from core.error_log import ErrorLogCollector


class ShutdownCollectionTests(unittest.TestCase):
    def test_stop_joins_collector_before_finalization_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as folder:
            collector = ErrorLogCollector(Path(folder), canonical_layout=True)
            collector.start()
            collector.stop()
            self.assertFalse(collector._thread.is_alive())
            collector.stop()
