from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
INGESTION_DIR = ROOT / "apps" / "ingestion"
for module_name in ("settings", "ingest"):
    sys.modules.pop(module_name, None)
sys.path.insert(0, str(INGESTION_DIR))
import ingest as ingestion  # noqa: E402
from extractors import ExtractedPage, extract_pages  # noqa: E402

sys.path.pop(0)
sys.modules.pop("settings", None)


class IngestionHelperTests(unittest.TestCase):
    def test_batches_preserve_order(self) -> None:
        self.assertEqual(
            list(ingestion.batches([1, 2, 3, 4, 5], 2)),
            [[1, 2], [3, 4], [5]],
        )

    def test_batches_reject_invalid_size(self) -> None:
        with self.assertRaises(ValueError):
            list(ingestion.batches([1], 0))

    def test_stable_id_is_deterministic_and_content_sensitive(self) -> None:
        first = ingestion.stable_id("source", 1, 1, "alpha")
        second = ingestion.stable_id("source", 1, 1, "alpha")
        changed = ingestion.stable_id("source", 1, 1, "beta")
        self.assertEqual(first, second)
        self.assertNotEqual(first, changed)
        self.assertEqual(len(first), 64)

    def test_escapes_odata_literal(self) -> None:
        self.assertEqual(ingestion.escape_odata("Director's guide"), "Director''s guide")

    def test_collects_only_supported_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "nested").mkdir()
            (root / "b.txt").write_text("b")
            (root / "nested" / "a.md").write_text("a")
            (root / "ignored.csv").write_text("ignored")

            result = ingestion.collect_files(root)

            self.assertEqual(
                [path.relative_to(root).as_posix() for path in result],
                ["b.txt", "nested/a.md"],
            )

    def test_extracts_plain_text_page(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "note.txt"
            path.write_text("Approved text", encoding="utf-8")
            self.assertEqual(
                extract_pages(path),
                [ExtractedPage(page_number=None, text="Approved text")],
            )

    def test_rejects_unsupported_document(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.csv"
            path.write_text("a,b", encoding="utf-8")
            with self.assertRaises(ValueError):
                extract_pages(path)

    def test_embeddings_are_restored_to_response_order(self) -> None:
        class _Embeddings:
            @staticmethod
            def create(**kwargs):
                self.assertEqual(kwargs["model"], "embedding-model")
                return SimpleNamespace(
                    data=[
                        SimpleNamespace(index=1, embedding=[2.0]),
                        SimpleNamespace(index=0, embedding=[1.0]),
                    ]
                )

        ingestor = object.__new__(ingestion.DocumentIngestor)
        ingestor.settings = SimpleNamespace(
            embedding_batch_size=2,
            embedding_deployment_name="embedding-model",
        )
        ingestor.openai_client = SimpleNamespace(embeddings=_Embeddings())

        self.assertEqual(ingestor.embed(["one", "two"]), [[1.0], [2.0]])

    def test_ingest_file_uploads_vectorized_records(self) -> None:
        class _SearchClient:
            def __init__(self) -> None:
                self.uploaded: list[dict[str, object]] = []

            def search(self, **_kwargs):
                return []

            def delete_documents(self, **_kwargs):
                self.fail("No old documents should be deleted")

            def upload_documents(self, documents):
                self.uploaded.extend(documents)
                return [SimpleNamespace(succeeded=True) for _ in documents]

        ingestor = object.__new__(ingestion.DocumentIngestor)
        ingestor.settings = SimpleNamespace(chunk_size=200, chunk_overlap=20)
        ingestor.search_client = _SearchClient()
        ingestor.upload_source = lambda _path, _name: "https://example.invalid/doc.txt"
        ingestor.embed = lambda texts: [[0.1, 0.2] for _ in texts]

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "doc.txt"
            path.write_text("Approved source content.", encoding="utf-8")
            with patch.object(
                ingestion,
                "extract_pages",
                return_value=[ExtractedPage(page_number=None, text=path.read_text())],
            ):
                count = ingestor.ingest_file(path, root)

        self.assertEqual(count, 1)
        self.assertEqual(ingestor.search_client.uploaded[0]["content_vector"], [0.1, 0.2])
        self.assertEqual(ingestor.search_client.uploaded[0]["title"], "doc.txt")


if __name__ == "__main__":
    unittest.main()
