import importlib.resources
import os
from pathlib import Path


def main() -> None:
    hermes_home = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
    dest = hermes_home / "plugins" / "spotlight-tool-output"
    dest.mkdir(parents=True, exist_ok=True)

    pkg = importlib.resources.files("spotlight_tool_output")
    yaml_bytes = (pkg / "plugin.yaml").read_bytes()
    (dest / "plugin.yaml").write_bytes(yaml_bytes)

    print(f"Installed plugin.yaml → {dest}")
    print()
    print("Add to your config.yaml:")
    print("  plugins:")
    print("    enabled:")
    print("      - spotlight-tool-output")
    print()
    print("Then restart your hermes gateway to activate.")
    print()
    print("Optional env vars:")
    print("  SPOTLIGHT_UNTRUSTED_MCP_SERVERS=server1,server2  (opt-in MCP wrapping)")
    print("  SPOTLIGHT_TRUSTED_MCP_SERVERS=memory,filesystem  (exempt MCP servers)")
    print("  SPOTLIGHT_DRY_RUN=true                           (log without wrapping)")
