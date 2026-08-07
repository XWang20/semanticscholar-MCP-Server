"""Evidence collection and citation verification CLI for ScholarQA workflows."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from semantic_scholar_api import SemanticScholarAPI, SemanticScholarAPIError
from semantic_scholar_server import __version__

DISCOVERY_FIELDS = [
    "paperId",
    "title",
    "authors",
    "year",
    "abstract",
    "venue",
    "externalIds",
    "url",
    "openAccessPdf",
    "citationCount",
    "publicationDate",
    "publicationTypes",
    "fieldsOfStudy",
]

VERIFICATION_FIELDS = [
    "paperId",
    "title",
    "authors",
    "year",
    "externalIds",
    "url",
]

PROVENANCE = {
    "kind": "scholarqa-provenance",
    "adaptation": (
        "Independent Semantic Scholar MCP/CLI adaptation; not an official Ai2 "
        "Scholar QA distribution and not a wrapper around ai2-scholarqa-lib."
    ),
    "sources": [
        {
            "role": "evidence_qa",
            "title": "Ai2 Scholar QA: Organized Literature Synthesis with Attribution",
            "authors": "Singh et al.",
            "year": 2025,
            "doi": "https://doi.org/10.18653/v1/2025.acl-demo.49",
            "arxiv": "https://arxiv.org/abs/2504.10861",
            "repository": "https://github.com/allenai/ai2-scholarqa-lib",
            "repository_snapshot": (
                "https://github.com/allenai/ai2-scholarqa-lib/tree/"
                "a96232870bdb0bd763f0131320e8377c6deb575e"
            ),
            "paper_license": "CC BY 4.0",
            "repository_license": "Apache-2.0",
        },
        {
            "role": "facet_ideation_and_novelty",
            "title": (
                "Scideator: Human-LLM Compound System for Scientific Ideation "
                "through Facet Recombination and Novelty Evaluation"
            ),
            "authors": "Radensky, Shahid et al.",
            "year": 2026,
            "doi": "https://doi.org/10.1145/3786335.3813161",
            "arxiv": "https://arxiv.org/abs/2409.14634v7",
            "paper_license": "CC BY 4.0",
        },
    ],
    "boundaries": [
        "No ai2-scholarqa-lib source code or runtime dependency is bundled.",
        (
            "Evidence collection is model-free and auditable; an agent or skill "
            "performs synthesis."
        ),
        "Novelty assessments must remain bounded to the retrieved literature.",
    ],
}


class CLIUsageError(ValueError):
    """Raised when ScholarQA CLI input is invalid."""


api = SemanticScholarAPI()


def _dump_json(value: Any, compact: bool = False) -> None:
    options: Dict[str, Any] = {
        "ensure_ascii": False,
        "default": str,
        "sort_keys": compact,
    }
    if compact:
        options["separators"] = (",", ":")
    else:
        options["indent"] = 2
    print(json.dumps(value, **options))


def _unique(values: Iterable[str]) -> List[str]:
    result: List[str] = []
    seen = set()
    for value in values:
        normalized = value.strip() if isinstance(value, str) else ""
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def _paper_ids(value: Any) -> List[str]:
    found: List[str] = []

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            paper_id = item.get("paperId")
            if isinstance(paper_id, str) and paper_id.strip():
                found.append(paper_id)
            for nested in item.values():
                visit(nested)
        elif isinstance(item, list):
            for nested in item:
                visit(nested)

    visit(value)
    return _unique(found)


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _collect_queries(args: argparse.Namespace) -> List[str]:
    question = args.question.strip()
    if not question:
        raise CLIUsageError("question must be a non-empty string")
    queries = _unique(args.queries or [question])
    if not queries:
        raise CLIUsageError("at least one non-empty search query is required")
    if args.no_snippets and args.no_papers:
        raise CLIUsageError("cannot disable both snippet and paper search")
    if not 1 <= args.paper_limit <= 100:
        raise CLIUsageError("paper-limit must be between 1 and 100")
    if not 1 <= args.snippet_limit <= 1000:
        raise CLIUsageError("snippet-limit must be between 1 and 1000")
    if args.min_citation_count is not None and args.min_citation_count < 0:
        raise CLIUsageError("min-citation-count must be non-negative")
    return queries


def _filter_record(args: argparse.Namespace) -> Dict[str, Any]:
    values = {
        "publication_types": args.publication_types,
        "open_access_pdf": args.open_access_pdf,
        "min_citation_count": args.min_citation_count,
        "publication_date_or_year": args.publication_date_or_year,
        "year": args.year,
        "venue": args.venues,
        "fields_of_study": args.fields_of_study,
    }
    return {
        key: value
        for key, value in values.items()
        if value not in (None, False, [], "")
    }


async def _run_collect(args: argparse.Namespace) -> int:
    try:
        queries = _collect_queries(args)
        filters = _filter_record(args)
    except CLIUsageError as exc:
        _dump_json({"error": str(exc), "command": "collect"}, args.compact)
        return 2

    query_runs: List[Dict[str, Any]] = []
    operation_errors: List[Dict[str, str]] = []

    try:
        for query in queries:
            run: Dict[str, Any] = {"query": query}

            if not args.no_snippets:
                try:
                    run["snippet_search"] = await api.search_snippets(
                        query,
                        min_citation_count=args.min_citation_count,
                        publication_date_or_year=args.publication_date_or_year,
                        year=args.year,
                        venue=args.venues,
                        fields_of_study=args.fields_of_study,
                        limit=args.snippet_limit,
                    )
                except SemanticScholarAPIError as exc:
                    run["snippet_search"] = {"error": str(exc)}
                    operation_errors.append(
                        {
                            "query": query,
                            "operation": "search_semantic_scholar_snippets",
                            "error": str(exc),
                        }
                    )

            if not args.no_papers:
                try:
                    run["paper_search"] = await api.search_papers(
                        query,
                        fields=DISCOVERY_FIELDS,
                        publication_types=args.publication_types,
                        open_access_pdf=args.open_access_pdf,
                        min_citation_count=args.min_citation_count,
                        publication_date_or_year=args.publication_date_or_year,
                        year=args.year,
                        venue=args.venues,
                        fields_of_study=args.fields_of_study,
                        limit=args.paper_limit,
                    )
                except SemanticScholarAPIError as exc:
                    run["paper_search"] = {"error": str(exc)}
                    operation_errors.append(
                        {
                            "query": query,
                            "operation": "search_semantic_scholar_papers",
                            "error": str(exc),
                        }
                    )

            query_runs.append(run)

        candidate_ids = _paper_ids(query_runs)
        bundle = {
            "schema_version": 1,
            "kind": "scholarqa-evidence-bundle",
            "created_at": _timestamp(),
            "question": args.question.strip(),
            "search_queries": queries,
            "filters": filters,
            "query_runs": query_runs,
            "candidate_paper_ids": candidate_ids,
            "operation_errors": operation_errors,
            "evidence_policy": {
                "snippet_search": (
                    "Candidate passage evidence; inspect its source before assigning "
                    "full-text Tier A or abstract Tier B."
                ),
                "paper_search": (
                    "An abstract may support Tier B; metadata alone is Tier C and "
                    "does not establish a finding."
                ),
                "final_citations": (
                    "Select papers by relevance and evidence, then run "
                    "scholarqa-cli verify before citation."
                ),
            },
        }
        _dump_json(bundle, args.compact)
        return 1 if operation_errors else 0
    except (CLIUsageError, ValueError) as exc:
        _dump_json({"error": str(exc), "command": "collect"}, args.compact)
        return 2
    except Exception as exc:
        _dump_json({"error": str(exc), "command": "collect"}, args.compact)
        return 2
    finally:
        await api.aclose()


def _load_ids(positional: Sequence[str], filename: Optional[str]) -> List[str]:
    if filename is not None and positional:
        raise CLIUsageError("provide paper IDs or --ids-file, not both")
    if filename is None:
        values = list(positional)
    else:
        text = sys.stdin.read() if filename == "-" else Path(filename).read_text()
        stripped = text.strip()
        if not stripped:
            values = []
        elif stripped.startswith("["):
            try:
                decoded = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise CLIUsageError(f"IDs file is not valid JSON: {exc.msg}") from exc
            if not isinstance(decoded, list) or any(
                not isinstance(value, str) for value in decoded
            ):
                raise CLIUsageError("JSON IDs input must be an array of strings")
            values = decoded
        else:
            values = [line for line in stripped.splitlines() if line.strip()]
    result = _unique(values)
    if not result:
        raise CLIUsageError("at least one non-empty paper ID is required")
    return result


def _chunks(values: Sequence[str], size: int) -> Iterable[Sequence[str]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


async def _run_verify(args: argparse.Namespace) -> int:
    try:
        paper_ids = _load_ids(args.paper_ids, args.ids_file)
        fields = _unique(args.fields or VERIFICATION_FIELDS)
        if not fields:
            raise CLIUsageError("at least one verification field is required")
    except (CLIUsageError, OSError) as exc:
        _dump_json({"error": str(exc), "command": "verify"}, args.compact)
        return 2

    items: List[Dict[str, Any]] = []
    unresolved: List[str] = []
    try:
        for chunk in _chunks(paper_ids, 500):
            response = await api.batch_papers(chunk, fields=fields)
            if not isinstance(response, list) or len(response) != len(chunk):
                raise SemanticScholarAPIError(
                    None, "batch verification returned an unexpected response shape"
                )
            for requested_id, record in zip(chunk, response):
                resolved = isinstance(record, dict)
                items.append(
                    {
                        "requested_id": requested_id,
                        "resolved": resolved,
                        "record": record,
                    }
                )
                if not resolved:
                    unresolved.append(requested_id)

        result = {
            "schema_version": 1,
            "kind": "scholarqa-citation-verification",
            "created_at": _timestamp(),
            "fields": fields,
            "requested_count": len(paper_ids),
            "resolved_count": len(paper_ids) - len(unresolved),
            "unresolved_ids": unresolved,
            "verification_scope": (
                "Bibliographic identity only; claim support must be checked against "
                "the retrieved evidence."
            ),
            "items": items,
        }
        _dump_json(result, args.compact)
        return 1 if unresolved else 0
    except SemanticScholarAPIError as exc:
        _dump_json({"error": str(exc), "command": "verify"}, args.compact)
        return 1
    except (CLIUsageError, ValueError, OSError) as exc:
        _dump_json({"error": str(exc), "command": "verify"}, args.compact)
        return 2
    except Exception as exc:
        _dump_json({"error": str(exc), "command": "verify"}, args.compact)
        return 2
    finally:
        await api.aclose()


async def _run_provenance(args: argparse.Namespace) -> int:
    _dump_json(PROVENANCE, args.compact)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scholarqa-cli",
        description=(
            "Collect auditable scholarly evidence and verify citations for an "
            "agent-driven ScholarQA workflow. This CLI does not generate prose."
        ),
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command")

    collect = subparsers.add_parser(
        "collect", help="collect snippet and paper evidence for one question"
    )
    collect.add_argument("question", help="research question to preserve in the bundle")
    collect.add_argument(
        "--query",
        dest="queries",
        action="append",
        help="search formulation; repeat for complementary queries",
    )
    collect.add_argument("--paper-limit", type=int, default=10)
    collect.add_argument("--snippet-limit", type=int, default=10)
    collect.add_argument(
        "--publication-type", dest="publication_types", action="append"
    )
    collect.add_argument("--open-access-pdf", action="store_true")
    collect.add_argument("--min-citation-count", type=int)
    collect.add_argument("--publication-date-or-year")
    collect.add_argument("--year")
    collect.add_argument("--venue", dest="venues", action="append")
    collect.add_argument("--field-of-study", dest="fields_of_study", action="append")
    collect.add_argument("--no-snippets", action="store_true")
    collect.add_argument("--no-papers", action="store_true")
    collect.add_argument("--compact", action="store_true")
    collect.set_defaults(handler=_run_collect)

    verify = subparsers.add_parser(
        "verify", help="batch-resolve and verify final citation records"
    )
    verify.add_argument("paper_ids", nargs="*", help="paper IDs to verify")
    verify.add_argument(
        "--ids-file", help="JSON array or newline-delimited IDs; use '-' for stdin"
    )
    verify.add_argument(
        "--field", dest="fields", action="append", help="field to return; repeatable"
    )
    verify.add_argument("--compact", action="store_true")
    verify.set_defaults(handler=_run_verify)

    provenance = subparsers.add_parser(
        "provenance", help="show the attributed research and repository sources"
    )
    provenance.add_argument("--compact", action="store_true")
    provenance.set_defaults(handler=_run_provenance)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 2
    try:
        return asyncio.run(handler(args))
    except KeyboardInterrupt:
        return 130
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
