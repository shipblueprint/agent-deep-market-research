import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import settings
from tools.save_report import SaveReportTool
from tools.visit_page import VisitPageTool


class SaveReportToolTest(unittest.TestCase):
    def test_writes_report_to_output_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "output"
            with patch.object(settings, "OUTPUT_DIR", output_dir):
                message = SaveReportTool()._run("report body", "Brand Inc")

            path = output_dir / "Brand_Inc_market_research.md"
            self.assertTrue(path.is_file())
            self.assertEqual(path.read_text(encoding="utf-8"), "report body")
            self.assertIn(str(path), message)


class VisitPageToolTest(unittest.TestCase):
    def test_skips_extraction_without_provider_key(self):
        env = {"LLM_PROVIDER": "ollama_cloud", "OLLAMA_API_KEY": ""}
        with patch.dict(os.environ, env, clear=True):
            result = VisitPageTool()._extract_info("page text", "goal", "https://example.com")

        self.assertIn("Extraction skipped", result)
        self.assertIn("https://example.com", result)


if __name__ == "__main__":
    unittest.main()
