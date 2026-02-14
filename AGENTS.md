# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**ff1ctl** — CLI and agent toolkit for Feral File FF1 art computers. Three layers, one codebase: async Python client library, Click CLI with JSON output, and FastMCP server for AI agents.

## Commands

```bash
# Install for development
pip install -e ".[mcp]"

# Run all tests
pytest

# Run a single test
pytest tests/test_client.py::test_send_command_envelope

# Run tests matching a pattern
pytest -k "test_validate" -v
```

No linter or formatter is configured in the project.

## Architecture

```
Humans / Scripts ──► ff1ctl CLI ──┐
AI Agents (Skill) ──► ff1ctl CLI ──┤──► FF1Client ──► HTTP :1111 ──► feral-controld
AI Agents (MCP)   ──► MCP Server ──┘
```

**`ff1.client`** — `FF1Client` is a fully async HTTP/WS client using `httpx` and `websockets`. Commands are sent as `CommandEnvelope(command, request)` via POST to `/api/cast`. Player status uses WebSocket at `/api/notification`. Supports optional API key (header) and topic ID (param).

**`ff1.types`** — Pydantic v2 models for API types. All models use `alias` for camelCase API fields with `populate_by_name=True`. Serialize with `model_dump(by_alias=True, exclude_none=True)`.

**`ff1.discovery`** — Finds devices by: (1) config file (`ff1.json` or `~/.config/ff1/config.json`), (2) ARP table scan for `FF1-*` hostnames, (3) probe port 1111 to verify. The CLI's `_resolve_device()` helper centralizes device selection logic across all commands.

**`ff1.playlist`** — Builds valid DP1 playlist JSON with UUIDs, timestamps, display config, and slug generation.

**`ff1.server`** — FastMCP server exposing all client operations as MCP tools. Uses `_get_client()` for device resolution.

**`ff1.url_policy`** — Feature-flagged URL validation (off by default). Controlled by `FF1_ENABLE_URL_VALIDATION` and `FF1_UNSAFE_ALLOW_LOCAL_URLS` env vars.

## Key Patterns

- **Async everywhere**: `FF1Client` is async, CLI wraps with `asyncio.run()`, MCP tools are async
- **Pydantic alias mapping**: API uses camelCase, Python uses snake_case — always use `by_alias=True` when serializing for the API
- **JSON I/O**: Every CLI command outputs JSON; `--pretty` flag for formatting; supports piping (`ff1ctl build ... | ff1ctl playlist -`)
- **CLI commands** follow a consistent pattern: resolve device via `_resolve_device()`, call async client method, output JSON

## Testing

- pytest with `pytest-asyncio` for async tests (`@pytest.mark.asyncio`)
- HTTP calls mocked with `unittest.mock.AsyncMock`
- Tests are in `tests/` mirroring `src/ff1/` module names
