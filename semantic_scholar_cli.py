"""Schema-driven command-line interface for the Semantic Scholar MCP tools."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from semantic_scholar_server import __version__, api, mcp


class CLIUsageError(ValueError):
    """Raised when CLI input cannot be mapped to an MCP tool call."""


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


def _load_params(inline: Optional[str], filename: Optional[str]) -> Dict[str, Any]:
    source = inline
    if filename is not None:
        source = sys.stdin.read() if filename == "-" else Path(filename).read_text()
    elif inline == "-":
        source = sys.stdin.read()

    if source is None or not source.strip():
        return {}

    try:
        value = json.loads(source)
    except json.JSONDecodeError as exc:
        raise CLIUsageError(f"parameters are not valid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise CLIUsageError("parameters must be a JSON object")
    return value


def _model_to_data(value: Any) -> Any:
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json", by_alias=True, exclude_none=True)
    return value


def _normalize_tool_result(result: Any) -> Any:
    if isinstance(result, (list, tuple)):
        text_values: List[Any] = []
        for block in result:
            text = getattr(block, "text", None)
            if not isinstance(text, str):
                break
            try:
                text_values.append(json.loads(text))
            except json.JSONDecodeError:
                text_values.append(text)
        else:
            return text_values[0] if len(text_values) == 1 else text_values
        return [_model_to_data(block) for block in result]
    return _model_to_data(result)


async def _list_tool_records() -> List[Dict[str, Any]]:
    tools = await mcp.list_tools()
    return [
        {
            "name": tool.name,
            "description": tool.description or "",
            "inputSchema": tool.inputSchema,
        }
        for tool in sorted(tools, key=lambda item: item.name)
    ]


async def _run_tools(args: argparse.Namespace) -> int:
    records = await _list_tool_records()
    if args.json:
        _dump_json(records, compact=args.compact)
    else:
        for record in records:
            print(f"{record['name']}\t{record['description']}")
    return 0


async def _run_schema(args: argparse.Namespace) -> int:
    records = await _list_tool_records()
    record = next((item for item in records if item["name"] == args.tool), None)
    if record is None:
        _dump_json(
            {"error": f"unknown tool: {args.tool}", "available_tools": len(records)},
            compact=args.compact,
        )
        return 2
    _dump_json(record, compact=args.compact)
    return 0


async def _run_call(args: argparse.Namespace) -> int:
    try:
        params = _load_params(args.params, args.params_file)
    except (CLIUsageError, OSError) as exc:
        _dump_json({"error": str(exc)}, compact=args.compact)
        return 2

    records = await _list_tool_records()
    if not any(item["name"] == args.tool for item in records):
        _dump_json(
            {"error": f"unknown tool: {args.tool}", "available_tools": len(records)},
            compact=args.compact,
        )
        return 2

    try:
        result = await mcp.call_tool(args.tool, params)
        normalized = _normalize_tool_result(result)
        _dump_json(normalized, compact=args.compact)
        return 1 if isinstance(normalized, dict) and "error" in normalized else 0
    except Exception as exc:
        _dump_json(
            {"error": str(exc), "tool": args.tool},
            compact=args.compact,
        )
        return 2
    finally:
        await api.aclose()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="semanticscholar-cli",
        description=(
            "Inspect and call the same typed Semantic Scholar operations exposed "
            "by the MCP server."
        ),
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command")

    tools_parser = subparsers.add_parser("tools", help="list available operations")
    tools_parser.add_argument("--json", action="store_true", help="include JSON schemas")
    tools_parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    tools_parser.set_defaults(handler=_run_tools)

    schema_parser = subparsers.add_parser("schema", help="show one operation schema")
    schema_parser.add_argument("tool", help="exact MCP tool name")
    schema_parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    schema_parser.set_defaults(handler=_run_schema)

    call_parser = subparsers.add_parser("call", help="invoke one operation")
    call_parser.add_argument("tool", help="exact MCP tool name")
    params_group = call_parser.add_mutually_exclusive_group()
    params_group.add_argument(
        "--params",
        help="JSON object with tool arguments; use '-' to read stdin",
    )
    params_group.add_argument(
        "--params-file",
        help="path to a JSON object; use '-' to read stdin",
    )
    call_parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    call_parser.set_defaults(handler=_run_call)
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
