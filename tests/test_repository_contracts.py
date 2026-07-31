from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class _HTMLValidator(HTMLParser):
    pass


class RepositoryContractTests(unittest.TestCase):
    def test_required_public_repository_files_exist(self) -> None:
        required = {
            "README.md",
            "LICENSE",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "SUPPORT.md",
            "CHANGELOG.md",
            "requirements-dev.txt",
            ".github/dependabot.yml",
            ".github/pull_request_template.md",
            ".github/workflows/ci.yml",
            ".github/workflows/deploy.yml",
            "docs/testing.md",
            "docs/github-setup.md",
        }
        missing = sorted(path for path in required if not (ROOT / path).is_file())
        self.assertEqual(missing, [])

    def test_yaml_files_parse(self) -> None:
        paths = [
            ROOT / "azure.yaml",
            *sorted((ROOT / ".github").rglob("*.yml")),
            *sorted((ROOT / ".github").rglob("*.yaml")),
        ]
        self.assertGreater(len(paths), 3)
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIsNotNone(yaml.safe_load(path.read_text(encoding="utf-8")))

    def test_html_parses(self) -> None:
        parser = _HTMLValidator()
        parser.feed((ROOT / "apps/web/static/index.html").read_text(encoding="utf-8"))
        parser.close()

    def test_local_markdown_links_resolve(self) -> None:
        failures: list[str] = []
        for path in [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]:
            text = path.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                if target.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                local_target = target.split("#", 1)[0]
                if local_target and not (path.parent / local_target).resolve().exists():
                    failures.append(f"{path.relative_to(ROOT)} -> {target}")
        self.assertEqual(failures, [])

    def test_no_obvious_secret_material(self) -> None:
        patterns = [
            re.compile(r"-----BEGIN (?:RSA|OPENSSH|EC|DSA) PRIVATE KEY-----", re.I),
            re.compile(r"AccountKey=[A-Za-z0-9+/=]{20,}", re.I),
            re.compile(r"client_secret\s*[=:]\s*[\"'][^\"']+", re.I),
        ]
        findings: list[str] = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or any(
                part in {".git", ".venv", ".terraform", "__pycache__"} for part in path.parts
            ):
                continue
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".zip", ".pyc"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if any(pattern.search(text) for pattern in patterns):
                findings.append(str(path.relative_to(ROOT)))
        self.assertEqual(findings, [])

    def test_container_images_run_as_non_root(self) -> None:
        for path in sorted((ROOT / "apps").glob("*/Dockerfile")):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIn("USER app", text)
                self.assertNotIn("USER root", text)

    def test_hosted_agent_protocol_is_current(self) -> None:
        config = yaml.safe_load((ROOT / "azure.yaml").read_text(encoding="utf-8"))
        protocols = config["services"]["enterprise-knowledge-agent"]["protocols"]
        self.assertIn({"protocol": "responses", "version": "2.0.0"}, protocols)

    def test_makefile_does_not_override_process_path(self) -> None:
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertNotRegex(makefile, r"(?m)^PATH\s*[?:+]?=")
        self.assertIn("SOURCE ?= sample-data", makefile)


if __name__ == "__main__":
    unittest.main()
