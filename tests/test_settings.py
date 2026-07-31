from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


agent_settings = load_module(
    "agent_settings_under_test",
    ROOT / "apps" / "agent" / "settings.py",
)
ingestion_settings = load_module(
    "ingestion_settings_under_test",
    ROOT / "apps" / "ingestion" / "settings.py",
)
web_settings = load_module(
    "web_settings_under_test",
    ROOT / "apps" / "web" / "app" / "settings.py",
)


class SettingsTests(unittest.TestCase):
    def test_agent_settings_support_model_alias_and_trim_endpoints(self) -> None:
        environment = {
            "FOUNDRY_PROJECT_ENDPOINT": "https://foundry.invalid/",
            "FOUNDRY_MODEL_NAME": "model",
            "EMBEDDING_DEPLOYMENT_NAME": "embedding",
            "SEARCH_ENDPOINT": "https://search.invalid/",
        }
        with patch.dict(os.environ, environment, clear=True):
            settings = agent_settings.AgentSettings.from_environment()

        self.assertEqual(settings.model_deployment_name, "model")
        self.assertEqual(settings.foundry_project_endpoint, "https://foundry.invalid")
        self.assertEqual(settings.search_endpoint, "https://search.invalid")

    def test_agent_settings_reject_small_passage_limit(self) -> None:
        environment = {
            "FOUNDRY_PROJECT_ENDPOINT": "https://foundry.invalid",
            "FOUNDRY_MODEL_NAME": "model",
            "EMBEDDING_DEPLOYMENT_NAME": "embedding",
            "SEARCH_ENDPOINT": "https://search.invalid",
            "MAX_PASSAGE_CHARACTERS": "100",
        }
        with patch.dict(os.environ, environment, clear=True):
            with self.assertRaises(RuntimeError):
                agent_settings.AgentSettings.from_environment()

    def test_ingestion_settings_validate_chunk_overlap(self) -> None:
        environment = {
            "FOUNDRY_PROJECT_ENDPOINT": "https://foundry.invalid",
            "EMBEDDING_DEPLOYMENT_NAME": "embedding",
            "SEARCH_ENDPOINT": "https://search.invalid",
            "STORAGE_BLOB_ENDPOINT": "https://storage.invalid",
            "CHUNK_SIZE": "300",
            "CHUNK_OVERLAP": "300",
        }
        with patch.dict(os.environ, environment, clear=True):
            with self.assertRaises(RuntimeError):
                ingestion_settings.IngestionSettings.from_environment()

    def test_web_settings_require_positive_timeout(self) -> None:
        environment = {
            "AGENT_ENDPOINT": "https://foundry.invalid/responses",
            "COSMOS_ENDPOINT": "https://cosmos.invalid",
            "REQUEST_TIMEOUT_SECONDS": "0",
        }
        with patch.dict(os.environ, environment, clear=True):
            with self.assertRaises(RuntimeError):
                web_settings.WebSettings.from_environment()

    def test_required_environment_variable_is_enforced(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "AGENT_ENDPOINT"):
                web_settings.WebSettings.from_environment()


if __name__ == "__main__":
    unittest.main()
