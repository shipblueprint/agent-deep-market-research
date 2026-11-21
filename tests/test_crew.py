import tempfile
import unittest
from pathlib import Path

from market_research_crew import parse_input_file


class ParseInputFileTest(unittest.TestCase):
    def test_reads_website_and_product(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.txt"
            path.write_text(
                "website: https://example.com\nproduct: A test product.\n",
                encoding="utf-8",
            )

            website, product = parse_input_file(str(path))

        self.assertEqual(website, "https://example.com")
        self.assertEqual(product, "A test product.")

    def test_missing_file_exits_cleanly(self):
        with self.assertRaises(SystemExit) as caught:
            parse_input_file("/nonexistent/input.txt")

        self.assertIn("Input file not found", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
