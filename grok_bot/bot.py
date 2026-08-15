"""Interactive Grok chat loop with Aigarth Garden tools."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from grok_bot.garden_tools import execute_tool, lab_status, tool_schemas
from grok_bot.prompt import SYSTEM_PROMPT

DEFAULT_MODEL = os.getenv("GROK_MODEL", "grok-4.6")


def _require_api_key() -> str:
    key = os.getenv("XAI_API_KEY")
    if not key:
        print(
            "Missing XAI_API_KEY.\n"
            "Create a key at https://console.x.ai/ and export it:\n"
            "  export XAI_API_KEY=xai-...\n",
            file=sys.stderr,
        )
        sys.exit(1)
    return key


def _build_xai_tools() -> list[Any]:
    from xai_sdk.chat import tool

    return [
        tool(name=spec["name"], description=spec["description"], parameters=spec["parameters"])
        for spec in tool_schemas()
    ]


def _handle_tool_calls(chat: Any, response: Any) -> Any:
    from xai_sdk.chat import tool_result

    while getattr(response, "tool_calls", None):
        chat.append(response)
        for tc in response.tool_calls:
            name = tc.function.name
            args = tc.function.arguments
            print(f"  ⚙ {name}({args})", flush=True)
            out = execute_tool(name, args)
            chat.append(tool_result(out))
        response = chat.sample()
    return response


def chat_once(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Single-turn (tool-looping) chat; returns assistant text."""
    from xai_sdk import Client
    from xai_sdk.chat import system, user

    client = Client(api_key=_require_api_key())
    chat = client.chat.create(model=model, tools=_build_xai_tools())
    chat.append(system(SYSTEM_PROMPT))
    chat.append(user(prompt))
    response = chat.sample()
    response = _handle_tool_calls(chat, response)
    return response.content or ""


def interactive_chat(model: str = DEFAULT_MODEL) -> None:
    """Multi-turn REPL."""
    from xai_sdk import Client
    from xai_sdk.chat import system, user

    client = Client(api_key=_require_api_key())
    chat = client.chat.create(model=model, tools=_build_xai_tools())
    chat.append(system(SYSTEM_PROMPT))

    print(f"Grok Bot — Aigarth Garden Labs  [{model}]")
    print("Commands: /status  /quit")
    print("Ask about fitness runs, mining logs, or request a short evolution.\n")

    while True:
        try:
            line = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye.")
            return
        if not line:
            continue
        if line in {"/quit", "/exit", ":q"}:
            print("bye.")
            return
        if line == "/status":
            print(json.dumps(lab_status(), indent=2, default=str))
            continue

        chat.append(user(line))
        response = chat.sample()
        response = _handle_tool_calls(chat, response)
        print(f"grok> {response.content or ''}\n")


def offline_status() -> None:
    """Print lab snapshot without calling xAI."""
    print(json.dumps(lab_status(), indent=2, default=str))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="grok_bot",
        description="Grok research bot for Aigarth Garden Labs (xAI API + local garden tools).",
    )
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"xAI model (default: {DEFAULT_MODEL})")
    p.add_argument("-q", "--query", help="Single prompt then exit")
    p.add_argument(
        "--status",
        action="store_true",
        help="Print local lab status JSON (no API key required)",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.status:
        offline_status()
        return
    if args.query:
        print(chat_once(args.query, model=args.model))
        return
    interactive_chat(model=args.model)


if __name__ == "__main__":
    main()
