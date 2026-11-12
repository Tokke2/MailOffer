"""Append-only diagnostics handler with cooperative native-crash capture."""
import faulthandler
import logging


class DiagnosticFileHandler(logging.FileHandler):
    def __init__(self, *args, **kwargs):
        self.native_capture = False
        super().__init__(*args, **kwargs)

    def pause_fault(self):
        if self.native_capture:
            faulthandler.disable()

    def resume_fault(self):
        if self.native_capture:
            if self.stream is None:
                self.stream = self._open()
            faulthandler.enable(file=self.stream, all_threads=True)

    def close(self):
        self.pause_fault()
        self.native_capture = False
        super().close()
