import logging
import os
from fnmatch import fnmatch

logger = logging.getLogger("hermes.plugins.spotlight_tool_output")

SPOTLIGHT_MARKER = "«⫶»"

# Built-in patterns always treated as untrusted. MCP is opt-in via env var.
WRAP_PATTERNS = ("web_*", "browser_*", "web_search", "web_fetch")


def _load_env_list(key: str) -> tuple[str, ...]:
    val = os.environ.get(key, "")
    return tuple(s.strip() for s in val.split(",") if s.strip())


def _dry_run() -> bool:
    return os.environ.get("SPOTLIGHT_DRY_RUN", "").lower() in ("1", "true", "yes")


def _source_label(tool_name: str) -> str:
    if tool_name.startswith("mcp__"):
        parts = tool_name.split("__", 2)
        return f"mcp:{parts[1]}" if len(parts) > 1 else "mcp:unknown"
    if tool_name == "web_search":
        return "web-search"
    if tool_name.startswith("web_"):
        return "web"
    if tool_name.startswith("browser_"):
        return "browser"
    return "external"


def _should_wrap(tool_name: str) -> bool:
    if tool_name.startswith("mcp__"):
        parts = tool_name.split("__", 2)
        server = parts[1] if len(parts) > 1 else None
        if server in _load_env_list("SPOTLIGHT_TRUSTED_MCP_SERVERS"):
            return False
        return server in _load_env_list("SPOTLIGHT_UNTRUSTED_MCP_SERVERS")
    return any(fnmatch(tool_name, pat) for pat in WRAP_PATTERNS)


def _spotlight(content: str, source: str) -> str:
    """Datamarking envelope per SpotLight (arXiv 2403.14720, §3.1)."""
    safe = (
        content
        .replace(SPOTLIGHT_MARKER, "")
        .replace("</UNTRUSTED>", "</UNTRUSTED_esc>")
        .replace("<UNTRUSTED", "<UNTRUSTED_esc")
    )
    marked = safe.replace(" ", SPOTLIGHT_MARKER)
    return (
        f'<UNTRUSTED source="{source}" marker="{SPOTLIGHT_MARKER}">\n'
        f"{marked}\n"
        f"</UNTRUSTED>"
    )


def spotlight_tool_result(
    tool_name, args, result, task_id, session_id, tool_call_id, duration_ms, **_extra
):
    try:
        if not isinstance(tool_name, str) or not tool_name:
            return None
        if not _should_wrap(tool_name):
            return None
        if not isinstance(result, str) or not result.strip():
            return None
        source = _source_label(tool_name)
        if _dry_run():
            logger.info(
                "spotlight[dry-run]: would wrap tool=%s source=%s len=%d",
                tool_name, source, len(result),
            )
            return None
        wrapped = _spotlight(result, source)
        logger.info(
            "spotlight: wrapped tool=%s source=%s len_in=%d len_out=%d",
            tool_name, source, len(result), len(wrapped),
        )
        return wrapped
    except Exception as e:
        logger.warning(
            "spotlight: callback error for tool=%s — passthrough: %s", tool_name, e
        )
        return None


def register(ctx):
    ctx.register_hook("transform_tool_result", spotlight_tool_result)
    untrusted_mcp = _load_env_list("SPOTLIGHT_UNTRUSTED_MCP_SERVERS")
    mode = "dry-run" if _dry_run() else "active"
    logger.warning(
        "spotlight: registered mode=%s wrap_patterns=%d untrusted_mcp=%d",
        mode, len(WRAP_PATTERNS), len(untrusted_mcp),
    )
