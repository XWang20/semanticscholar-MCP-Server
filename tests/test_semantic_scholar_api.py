import json
import unittest
from urllib.parse import parse_qs

import httpx

from semantic_scholar_api import SemanticScholarAPI, SemanticScholarAPIError


class SemanticScholarAPITests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.requests = []

        async def handler(request: httpx.Request) -> httpx.Response:
            self.requests.append(request)
            return httpx.Response(200, json={"ok": True}, request=request)

        self.api = SemanticScholarAPI(
            api_key="test-key",
            api_url="https://example.test",
            max_retries=0,
            transport=httpx.MockTransport(handler),
        )

    async def asyncTearDown(self):
        await self.api.aclose()

    async def test_every_official_endpoint_has_a_client_method(self):
        calls = [
            ("POST", "/graph/v1/author/batch", self.api.batch_authors(["1"])),
            ("GET", "/graph/v1/author/search", self.api.search_authors("Ada")),
            ("GET", "/graph/v1/author/1", self.api.get_author("1")),
            ("GET", "/graph/v1/author/1/papers", self.api.get_author_papers("1")),
            (
                "GET",
                "/graph/v1/paper/autocomplete",
                self.api.autocomplete_papers("att"),
            ),
            ("POST", "/graph/v1/paper/batch", self.api.batch_papers(["p1"])),
            ("GET", "/graph/v1/paper/search", self.api.search_papers("attention")),
            (
                "GET",
                "/graph/v1/paper/search/bulk",
                self.api.bulk_search_papers("attention"),
            ),
            (
                "GET",
                "/graph/v1/paper/search/match",
                self.api.match_paper("Attention is All You Need"),
            ),
            ("GET", "/graph/v1/paper/p1", self.api.get_paper("p1")),
            ("GET", "/graph/v1/paper/p1/authors", self.api.get_paper_authors("p1")),
            ("GET", "/graph/v1/paper/p1/citations", self.api.get_paper_citations("p1")),
            (
                "GET",
                "/graph/v1/paper/p1/references",
                self.api.get_paper_references("p1"),
            ),
            (
                "GET",
                "/graph/v1/snippet/search",
                self.api.search_snippets("transformer"),
            ),
            (
                "GET",
                "/recommendations/v1/papers/forpaper/p1",
                self.api.recommend_papers_for_paper("p1"),
            ),
            ("POST", "/recommendations/v1/papers/", self.api.recommend_papers(["p1"])),
            ("GET", "/datasets/v1/release/", self.api.list_dataset_releases()),
            (
                "GET",
                "/datasets/v1/release/latest",
                self.api.get_dataset_release("latest"),
            ),
            (
                "GET",
                "/datasets/v1/release/latest/dataset/papers",
                self.api.get_dataset_download_links("latest", "papers"),
            ),
            (
                "GET",
                "/datasets/v1/diffs/2025-01-01/to/latest/papers",
                self.api.get_dataset_diffs("2025-01-01", "latest", "papers"),
            ),
        ]

        for expected_method, expected_path, call in calls:
            with self.subTest(path=expected_path):
                await call
                request = self.requests[-1]
                self.assertEqual(expected_method, request.method)
                self.assertEqual(expected_path, request.url.path)
                self.assertEqual("test-key", request.headers["x-api-key"])

    async def test_search_serializes_all_filters(self):
        await self.api.search_papers(
            "graph neural network",
            fields=["title", "authors"],
            publication_types=["JournalArticle", "Conference"],
            open_access_pdf=True,
            min_citation_count=10,
            publication_date_or_year="2020:2025",
            year="2020-2025",
            venue=["NeurIPS", "ICML"],
            fields_of_study=["Computer Science"],
            offset=20,
            limit=25,
        )

        query = parse_qs(self.requests[-1].url.query.decode(), keep_blank_values=True)
        self.assertEqual(["graph neural network"], query["query"])
        self.assertEqual(["title,authors"], query["fields"])
        self.assertEqual(["JournalArticle,Conference"], query["publicationTypes"])
        self.assertEqual([""], query["openAccessPdf"])
        self.assertEqual(["10"], query["minCitationCount"])
        self.assertEqual(["2020:2025"], query["publicationDateOrYear"])
        self.assertEqual(["2020-2025"], query["year"])
        self.assertEqual(["NeurIPS,ICML"], query["venue"])
        self.assertEqual(["Computer Science"], query["fieldsOfStudy"])
        self.assertEqual(["20"], query["offset"])
        self.assertEqual(["25"], query["limit"])

    async def test_batch_and_recommendation_payloads(self):
        await self.api.batch_papers(["p1", "DOI:10.1/example"])
        self.assertEqual(
            {"ids": ["p1", "DOI:10.1/example"]},
            json.loads(self.requests[-1].content),
        )

        await self.api.recommend_papers(["p1"], ["p2"], limit=12)
        self.assertEqual(
            {"positivePaperIds": ["p1"], "negativePaperIds": ["p2"]},
            json.loads(self.requests[-1].content),
        )
        self.assertEqual("12", self.requests[-1].url.params["limit"])

    async def test_validation_rejects_invalid_limits_and_empty_ids(self):
        with self.assertRaises(ValueError):
            await self.api.search_papers("query", limit=101)
        with self.assertRaises(ValueError):
            await self.api.search_authors("name", limit=1001)
        with self.assertRaises(ValueError):
            await self.api.batch_papers([])
        with self.assertRaises(ValueError):
            await self.api.recommend_papers([])

    async def test_api_errors_include_status_and_message(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                400,
                json={"error": "bad query"},
                request=request,
            )

        api = SemanticScholarAPI(
            api_url="https://example.test",
            max_retries=0,
            transport=httpx.MockTransport(handler),
        )
        self.addAsyncCleanup(api.aclose)

        with self.assertRaises(SemanticScholarAPIError) as raised:
            await api.search_papers("bad")
        self.assertEqual(400, raised.exception.status_code)
        self.assertIn("bad query", str(raised.exception))

    async def test_throttled_requests_are_retried(self):
        attempts = 0

        async def handler(request: httpx.Request) -> httpx.Response:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                return httpx.Response(
                    429,
                    headers={"Retry-After": "0"},
                    json={"message": "slow down"},
                    request=request,
                )
            return httpx.Response(200, json={"data": []}, request=request)

        api = SemanticScholarAPI(
            api_url="https://example.test",
            max_retries=1,
            transport=httpx.MockTransport(handler),
        )
        self.addAsyncCleanup(api.aclose)

        result = await api.search_papers("retry me")
        self.assertEqual({"data": []}, result)
        self.assertEqual(2, attempts)


if __name__ == "__main__":
    unittest.main()
