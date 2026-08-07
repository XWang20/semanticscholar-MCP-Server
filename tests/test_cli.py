import asyncio
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import AsyncMock, patch

import semantic_scholar_cli
import semantic_scholar_server


class SemanticScholarCLITests(unittest.TestCase):
    def run_cli(self, *args):
        output = io.StringIO()
        with redirect_stdout(output):
            status = semantic_scholar_cli.main(list(args))
        return status, output.getvalue()

    def test_tool_catalog_matches_mcp_server(self):
        records = asyncio.run(semantic_scholar_cli._list_tool_records())
        self.assertEqual(22, len(records))
        self.assertEqual(22, len({record["name"] for record in records}))

    def test_tools_json_and_schema_are_machine_readable(self):
        status, output = self.run_cli("tools", "--json", "--compact")
        self.assertEqual(0, status)
        self.assertEqual(22, len(json.loads(output)))

        status, output = self.run_cli(
            "schema", "search_semantic_scholar_papers", "--compact"
        )
        self.assertEqual(0, status)
        schema = json.loads(output)
        self.assertIn("query", schema["inputSchema"]["properties"])

    def test_call_dispatches_through_the_mcp_tool(self):
        response = {"data": [{"paperId": "p1", "title": "Example"}]}
        with patch.object(
            semantic_scholar_server.api,
            "search_papers",
            new=AsyncMock(return_value=response),
        ):
            status, output = self.run_cli(
                "call",
                "search_semantic_scholar_papers",
                "--params",
                '{"query":"example","limit":1}',
                "--compact",
            )
        self.assertEqual(0, status)
        self.assertEqual(response, json.loads(output))

    def test_batch_call_normalizes_multiple_mcp_content_blocks(self):
        response = [
            {"paperId": "p1", "title": "First"},
            {"paperId": "p2", "title": "Second"},
        ]
        with patch.object(
            semantic_scholar_server.api,
            "batch_papers",
            new=AsyncMock(return_value=response),
        ):
            status, output = self.run_cli(
                "call",
                "batch_get_semantic_scholar_papers",
                "--params",
                '{"paper_ids":["p1","p2"]}',
                "--compact",
            )
        self.assertEqual(0, status)
        self.assertEqual(response, json.loads(output))

    def test_call_rejects_non_object_json(self):
        status, output = self.run_cli(
            "call",
            "search_semantic_scholar_papers",
            "--params",
            "[]",
        )
        self.assertEqual(2, status)
        self.assertIn("JSON object", json.loads(output)["error"])

    def test_call_reads_params_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "params.json"
            path.write_text('{"query":"example","limit":1}')
            response = {"data": []}
            with patch.object(
                semantic_scholar_server.api,
                "search_papers",
                new=AsyncMock(return_value=response),
            ):
                status, output = self.run_cli(
                    "call",
                    "search_semantic_scholar_papers",
                    "--params-file",
                    str(path),
                )
        self.assertEqual(0, status)
        self.assertEqual(response, json.loads(output))

    def test_unknown_tool_returns_usage_error(self):
        status, output = self.run_cli("schema", "not_a_real_tool")
        self.assertEqual(2, status)
        self.assertIn("unknown tool", json.loads(output)["error"])


if __name__ == "__main__":
    unittest.main()
