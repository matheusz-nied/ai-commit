import io
import unittest

from ai_commit.status import status


class StatusTests(unittest.TestCase):
    def test_prints_static_message_for_non_tty_stream(self):
        stream = io.StringIO()

        with status("Generating commit message...", stream=stream):
            pass

        self.assertEqual(stream.getvalue(), "Generating commit message...\n")

    def test_quiet_suppresses_message(self):
        stream = io.StringIO()

        with status("Generating commit message...", quiet=True, stream=stream):
            pass

        self.assertEqual(stream.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
