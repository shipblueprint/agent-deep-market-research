import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import settings


class EnsurePromptsTest(unittest.TestCase):
    def test_copies_templates_on_first_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            templates = root / "prompts.example"
            templates.mkdir()
            (templates / "alpha.py").write_text("ALPHA = 1\n", encoding="utf-8")

            prompts = root / "prompts"
            copied = settings.ensure_prompts(prompts, templates)

            self.assertTrue(copied)
            self.assertEqual(
                (prompts / "alpha.py").read_text(encoding="utf-8"), "ALPHA = 1\n"
            )

    def test_keeps_existing_prompts_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            templates = root / "prompts.example"
            templates.mkdir()
            (templates / "alpha.py").write_text("ALPHA = 1\n", encoding="utf-8")

            prompts = root / "prompts"
            prompts.mkdir()
            (prompts / "alpha.py").write_text("CUSTOM = True\n", encoding="utf-8")

            copied = settings.ensure_prompts(prompts, templates)

            self.assertFalse(copied)
            self.assertIn(
                "CUSTOM", (prompts / "alpha.py").read_text(encoding="utf-8")
            )


class EnvironmentTest(unittest.TestCase):
    def test_reports_all_missing_keys(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit) as caught:
                settings.validate_environment()

        message = str(caught.exception)
        self.assertIn("EXA_API_KEY", message)
        self.assertIn("OLLAMA_API_KEY", message)

    def test_openai_requires_openai_key(self):
        env = {"LLM_PROVIDER": "openai", "EXA_API_KEY": "exa"}
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(SystemExit) as caught:
                settings.validate_environment()

        self.assertIn("OPENAI_API_KEY", str(caught.exception))

    def test_valid_ollama_environment_passes(self):
        env = {
            "LLM_PROVIDER": "ollama_cloud",
            "EXA_API_KEY": "exa",
            "OLLAMA_API_KEY": "ollama",
        }
        with patch.dict(os.environ, env, clear=True):
            settings.validate_environment()

    def test_unknown_provider_fails(self):
        env = {
            "LLM_PROVIDER": "something_else",
            "EXA_API_KEY": "exa",
            "OLLAMA_API_KEY": "ollama",
        }
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(SystemExit) as caught:
                settings.validate_environment()

        self.assertIn("Unsupported LLM_PROVIDER", str(caught.exception))


class ProviderConfigTest(unittest.TestCase):
    def test_ollama_extraction_uses_ollama_key(self):
        env = {
            "LLM_PROVIDER": "ollama_cloud",
            "OLLAMA_API_KEY": "ollama",
            "OLLAMA_MODEL": "gpt-oss:120b-cloud",
        }
        with patch.dict(os.environ, env, clear=True):
            config = settings.extraction_config()
            kwargs = settings.llm_kwargs()

        self.assertEqual(config["api_key"], "ollama")
        self.assertEqual(config["model"], settings.OLLAMA_DEFAULT_MODEL)
        self.assertEqual(kwargs["model"], "openai/gpt-oss:120b-cloud")

    def test_openai_extraction_uses_openai_key_and_model(self):
        env = {
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "openai",
            "OPENAI_MODEL": "gpt-4o",
        }
        with patch.dict(os.environ, env, clear=True):
            config = settings.extraction_config()
            kwargs = settings.llm_kwargs()

        self.assertEqual(config["api_key"], "openai")
        self.assertEqual(config["model"], settings.OPENAI_DEFAULT_MODEL)
        self.assertIsNone(config["base_url"])
        self.assertEqual(kwargs["model"], "gpt-4o")


if __name__ == "__main__":
    unittest.main()
