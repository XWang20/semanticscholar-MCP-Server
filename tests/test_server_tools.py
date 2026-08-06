import unittest

import semantic_scholar_server


OFFICIAL_TOOLS = {
    "batch_get_semantic_scholar_authors",
    "search_semantic_scholar_authors",
    "get_semantic_scholar_author_details",
    "get_semantic_scholar_author_papers",
    "autocomplete_semantic_scholar_papers",
    "batch_get_semantic_scholar_papers",
    "search_semantic_scholar_papers",
    "bulk_search_semantic_scholar_papers",
    "match_semantic_scholar_paper",
    "get_semantic_scholar_paper_details",
    "get_semantic_scholar_paper_authors",
    "get_semantic_scholar_paper_citations",
    "get_semantic_scholar_paper_references",
    "search_semantic_scholar_snippets",
    "recommend_semantic_scholar_papers_for_paper",
    "recommend_semantic_scholar_papers",
    "list_semantic_scholar_dataset_releases",
    "get_semantic_scholar_dataset_release",
    "get_semantic_scholar_dataset_download_links",
    "get_semantic_scholar_dataset_diffs",
}

LEGACY_TOOLS = {
    "search_semantic_scholar",
    "get_semantic_scholar_citations_and_references",
}


class ServerToolTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_official_and_legacy_tools_are_registered(self):
        tools = await semantic_scholar_server.mcp.list_tools()
        names = {tool.name for tool in tools}
        self.assertTrue(OFFICIAL_TOOLS <= names)
        self.assertTrue(LEGACY_TOOLS <= names)
        self.assertEqual(22, len(names))


if __name__ == "__main__":
    unittest.main()
