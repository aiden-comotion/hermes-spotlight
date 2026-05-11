import importlib.resources
import sys
from pathlib import Path


def main() -> None:
    dest = Path.home() / ".hermes" / "plugins" / "spotlight-tool-output"
    dest.mkdir(parents=True, exist_ok=True)

    pkg = importlib.resources.files("spotlight_tool_output")
    yaml_bytes = (pkg / "plugin.yaml").read_bytes()
    (dest / "plugin.yaml").write_bytes(yaml_bytes)

    print(f"Installed plugin.yaml → {dest}")
    print("Restart your hermes gateway to activate.")
    print()
    print("Optional env vars:")
    print("  SPOTLIGHT_UNTRUSTED_MCP_SERVERS=server1,server2  (opt-in MCP wrapping)")
    print("  SPOTLIGHT_TRUSTED_MCP_SERVERS=memory,filesystem  (exempt MCP servers)")
    print("  SPOTLIGHT_DRY_RUN=true                           (log without wrapping)")
    sys.exit(0)
