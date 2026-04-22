import itertools
import sys
import threading
import time
from types import TracebackType
from typing import Optional, TextIO, Type


class Status:
    def __init__(self, message: str, enabled: bool = True, stream: TextIO = sys.stderr) -> None:
        self.message = message
        self.visible = enabled
        self.enabled = enabled and hasattr(stream, "isatty") and stream.isatty()
        self.stream = stream
        self._done = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def __enter__(self) -> "Status":
        if not self.visible:
            return self
        if not self.enabled:
            if self.message:
                print(self.message, file=self.stream)
            return self

        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        if self.enabled:
            self._done.set()
            if self._thread:
                self._thread.join()
            self._clear_line()

    def _spin(self) -> None:
        for frame in itertools.cycle(("-", "\\", "|", "/")):
            if self._done.is_set():
                return
            self.stream.write(f"\r{frame} {self.message}")
            self.stream.flush()
            time.sleep(0.12)

    def _clear_line(self) -> None:
        self.stream.write("\r\033[K")
        self.stream.flush()


def status(message: str, quiet: bool = False, stream: TextIO = sys.stderr) -> Status:
    return Status(message, enabled=not quiet, stream=stream)
