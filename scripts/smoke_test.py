"""Test de fumée : démarre le serveur MCP en stdio et interroge ses outils.

Usage : python scripts/smoke_test.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

ROOT = Path(__file__).resolve().parents[1]


async def main() -> int:
    python = ROOT / ".venv" / "Scripts" / "python.exe"
    params = StdioServerParameters(
        command=str(python),
        args=["-m", "copilot_rag.server"],
        cwd=str(ROOT),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            print("Outils exposés :", ", ".join(names))
            assert "search_code" in names, "search_code manquant"

            result = await session.call_tool(
                "search_code", {"query": "comment logger une erreur proprement", "top_k": 2}
            )
            text = result.content[0].text if result.content else ""
            print("\n--- search_code ---")
            print(text[:800])
            assert text, "Réponse vide"

            projects = await session.call_tool("list_projects", {})
            print("\n--- list_projects ---")
            print(projects.content[0].text if projects.content else "(vide)")

    print("\nSMOKE TEST OK")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
