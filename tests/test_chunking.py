from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "ingestion"))

from chunking import chunk_text, normalize_text  # noqa: E402


class ChunkingTests(unittest.TestCase):
    def test_normalizes_whitespace(self) -> None:
        self.assertEqual(normalize_text("alpha   beta\n\n\n\ngamma"), "alpha beta\n\ngamma")

    def test_normalizes_null_bytes_and_tabs(self) -> None:
        self.assertEqual(normalize_text(" alpha\x00\tbeta "), "alpha beta")

    def test_empty_input_returns_no_chunks(self) -> None:
        self.assertEqual(chunk_text(" \n\t "), [])

    def test_chunks_are_bounded_and_overlap(self) -> None:
        text = " ".join(f"word-{index}" for index in range(300))
        chunks = chunk_text(text, size=300, overlap=50)
        self.assertGreater(len(chunks), 2)
        self.assertTrue(all(len(chunk) <= 301 for chunk in chunks))

    def test_short_text_is_one_chunk(self) -> None:
        self.assertEqual(
            chunk_text("A short paragraph.", size=200, overlap=20), ["A short paragraph."]
        )

    def test_rejects_too_small_chunk_size(self) -> None:
        with self.assertRaises(ValueError):
            chunk_text("hello world", size=199, overlap=10)

    def test_rejects_invalid_overlap(self) -> None:
        with self.assertRaises(ValueError):
            chunk_text("hello world", size=200, overlap=200)

    def test_rejects_negative_overlap(self) -> None:
        with self.assertRaises(ValueError):
            chunk_text("hello world", size=200, overlap=-1)


if __name__ == "__main__":
    unittest.main()
