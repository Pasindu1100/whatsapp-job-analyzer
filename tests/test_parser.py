import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from parser import parse_whatsapp_chat


class ParserTests(unittest.TestCase):
    def test_parses_current_whatsapp_export_format(self):
        chat_text = """1/9/26, 7:46 PM - Messages and calls are end-to-end encrypted. Only people in this chat can read, listen to, or share them. *Learn more*
1/9/26, 11:29 PM - +94 71 522 6008: 🚀 We’re Hiring! Econsulate

This is a test job post.
"""

        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            handle.write(chat_text)
            temp_path = Path(handle.name)

        try:
            df = parse_whatsapp_chat(temp_path)
            self.assertEqual(len(df), 1)
            self.assertEqual(df.iloc[0]["sender"], "+94 71 522 6008")
            self.assertIn("This is a test job post.", df.iloc[0]["raw_text"])
        finally:
            temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
