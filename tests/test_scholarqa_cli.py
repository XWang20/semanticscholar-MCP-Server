import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import AsyncMock, patch

import scholarqa_cli
from semantic_scholar_api import SemanticScholarAPIError


class ScholarQACLITests(unittest.TestCase):
    def run_cli(self, *args):
        output = io.StringIO()
        with redirect_stdout(output):
            status = scholarqa_cli.main(list(args))
        return status, output.getvalue()

    def test_collect_builds_deduplicated_evidence_bundle(self):
        snippet_response = {"data": [{"paperId": "p1", "text": "Supporting passage"}]}
        paper_response = {
            "data": [
                {"paperId": "p1", "title": "First"},
                {"paperId": "p2", "title": "Second"},
            ]
        }
        with (
            patch.object(
                scholarqa_cli.api,
                "search_snippets",
                new=AsyncMock(return_value=snippet_response),
            ) as search_snippets,
            patch.object(
                scholarqa_cli.api,
                "search_papers",
                new=AsyncMock(return_value=paper_response),
            ) as search_papers,
            patch.object(scholarqa_cli.api, "aclose", new=AsyncMock()),
        ):
            status, output = self.run_cli(
                "collect",
                "How do agents synthesize literature?",
                "--query",
                "agent literature synthesis",
                "--query",
                "scholarly question answering",
                "--paper-limit",
                "2",
                "--snippet-limit",
                "3",
                "--field-of-study",
                "Computer Science",
                "--compact",
            )

        self.assertEqual(0, status)
        bundle = json.loads(output)
        self.assertEqual("scholarqa-evidence-bundle", bundle["kind"])
        self.assertEqual(["p1", "p2"], bundle["candidate_paper_ids"])
        self.assertEqual(2, len(bundle["query_runs"]))
        self.assertEqual([], bundle["operation_errors"])
        self.assertIn("final_citations", bundle["evidence_policy"])
        self.assertEqual(2, search_snippets.await_count)
        self.assertEqual(2, search_papers.await_count)
        self.assertEqual(
            ["Computer Science"],
            search_papers.await_args.kwargs["fields_of_study"],
        )

    def test_collect_preserves_partial_results_and_reports_api_errors(self):
        error = SemanticScholarAPIError(429, "slow down")
        with (
            patch.object(
                scholarqa_cli.api,
                "search_snippets",
                new=AsyncMock(side_effect=error),
            ),
            patch.object(
                scholarqa_cli.api,
                "search_papers",
                new=AsyncMock(return_value={"data": [{"paperId": "p1"}]}),
            ),
            patch.object(scholarqa_cli.api, "aclose", new=AsyncMock()),
        ):
            status, output = self.run_cli("collect", "A question", "--compact")

        self.assertEqual(1, status)
        bundle = json.loads(output)
        self.assertEqual(["p1"], bundle["candidate_paper_ids"])
        self.assertEqual(1, len(bundle["operation_errors"]))
        self.assertEqual(
            "search_semantic_scholar_snippets",
            bundle["operation_errors"][0]["operation"],
        )

    def test_collect_rejects_disabling_both_searches(self):
        status, output = self.run_cli(
            "collect", "A question", "--no-snippets", "--no-papers"
        )
        self.assertEqual(2, status)
        self.assertIn("cannot disable both", json.loads(output)["error"])

    def test_verify_resolves_records_and_preserves_missing_ids(self):
        response = [
            {
                "paperId": "p1",
                "title": "A verified paper",
                "externalIds": {"DOI": "10.1/example"},
            },
            None,
        ]
        with (
            patch.object(
                scholarqa_cli.api,
                "batch_papers",
                new=AsyncMock(return_value=response),
            ) as batch_papers,
            patch.object(scholarqa_cli.api, "aclose", new=AsyncMock()),
        ):
            status, output = self.run_cli("verify", "p1", "missing", "p1", "--compact")

        self.assertEqual(1, status)
        result = json.loads(output)
        self.assertEqual("scholarqa-citation-verification", result["kind"])
        self.assertEqual(2, result["requested_count"])
        self.assertEqual(1, result["resolved_count"])
        self.assertEqual(["missing"], result["unresolved_ids"])
        self.assertIn("Bibliographic identity", result["verification_scope"])
        batch_papers.assert_awaited_once_with(
            ["p1", "missing"], fields=scholarqa_cli.VERIFICATION_FIELDS
        )

    def test_verify_reads_json_ids_file_and_custom_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ids.json"
            path.write_text('["DOI:10.1/a", "ARXIV:2504.10861"]')
            response = [
                {"paperId": "p1", "title": "First"},
                {"paperId": "p2", "title": "Second"},
            ]
            with (
                patch.object(
                    scholarqa_cli.api,
                    "batch_papers",
                    new=AsyncMock(return_value=response),
                ) as batch_papers,
                patch.object(scholarqa_cli.api, "aclose", new=AsyncMock()),
            ):
                status, output = self.run_cli(
                    "verify",
                    "--ids-file",
                    str(path),
                    "--field",
                    "paperId",
                    "--field",
                    "title",
                    "--compact",
                )

        self.assertEqual(0, status)
        self.assertEqual(2, json.loads(output)["resolved_count"])
        batch_papers.assert_awaited_once_with(
            ["DOI:10.1/a", "ARXIV:2504.10861"],
            fields=["paperId", "title"],
        )

    def test_provenance_attributes_paper_and_official_repository(self):
        status, output = self.run_cli("provenance", "--compact")
        self.assertEqual(0, status)
        provenance = json.loads(output)
        scholarqa = provenance["sources"][0]
        self.assertEqual(
            "https://doi.org/10.18653/v1/2025.acl-demo.49", scholarqa["doi"]
        )
        self.assertEqual(
            "https://github.com/allenai/ai2-scholarqa-lib",
            scholarqa["repository"],
        )


if __name__ == "__main__":
    unittest.main()
