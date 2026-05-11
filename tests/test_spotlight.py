import spotlight_tool_output as spl
from spotlight_tool_output import (
    SPOTLIGHT_MARKER,
    _load_env_list,
    _should_wrap,
    _source_label,
    _spotlight,
    spotlight_tool_result,
)


class TestLoadEnvList:
    def test_absent_key_returns_empty(self, monkeypatch):
        monkeypatch.delenv("SPOTLIGHT_TEST_KEY", raising=False)
        assert _load_env_list("SPOTLIGHT_TEST_KEY") == ()

    def test_single_value(self, monkeypatch):
        monkeypatch.setenv("SPOTLIGHT_TEST_KEY", "memory")
        assert _load_env_list("SPOTLIGHT_TEST_KEY") == ("memory",)

    def test_multiple_values(self, monkeypatch):
        monkeypatch.setenv("SPOTLIGHT_TEST_KEY", "memory,filesystem,brave_search")
        assert _load_env_list("SPOTLIGHT_TEST_KEY") == ("memory", "filesystem", "brave_search")

    def test_strips_whitespace(self, monkeypatch):
        monkeypatch.setenv("SPOTLIGHT_TEST_KEY", " memory , filesystem ")
        assert _load_env_list("SPOTLIGHT_TEST_KEY") == ("memory", "filesystem")


class TestSourceLabel:
    def test_web_search(self):
        assert _source_label("web_search") == "web-search"

    def test_web_wildcard(self):
        assert _source_label("web_browse") == "web"

    def test_browser_wildcard(self):
        assert _source_label("browser_click") == "browser"

    def test_mcp_includes_server_name(self):
        assert _source_label("mcp__brave_search__query") == "mcp:brave_search"

    def test_mcp_malformed_falls_back(self):
        assert _source_label("mcp__") == "mcp:unknown"

    def test_unknown_tool(self):
        assert _source_label("read_file") == "external"


class TestShouldWrap:
    def test_web_search_wrapped(self):
        assert _should_wrap("web_search")

    def test_web_fetch_wrapped(self):
        assert _should_wrap("web_fetch")

    def test_web_wildcard_wrapped(self):
        assert _should_wrap("web_browse")

    def test_browser_wildcard_wrapped(self):
        assert _should_wrap("browser_click")

    def test_internal_tools_not_wrapped(self):
        for name in ("read_file", "write_file", "execute_code", "bash"):
            assert not _should_wrap(name), f"expected {name!r} not wrapped"

    def test_mcp_not_wrapped_by_default(self):
        assert not _should_wrap("mcp__some_server__some_tool")

    def test_mcp_wrapped_when_in_untrusted_list(self, monkeypatch):
        monkeypatch.setenv("SPOTLIGHT_UNTRUSTED_MCP_SERVERS", "brave_search")
        assert _should_wrap("mcp__brave_search__search")

    def test_mcp_trusted_overrides_untrusted(self, monkeypatch):
        monkeypatch.setenv("SPOTLIGHT_UNTRUSTED_MCP_SERVERS", "brave_search")
        monkeypatch.setenv("SPOTLIGHT_TRUSTED_MCP_SERVERS", "brave_search")
        assert not _should_wrap("mcp__brave_search__search")

    def test_mcp_other_server_not_wrapped_when_only_one_listed(self, monkeypatch):
        monkeypatch.setenv("SPOTLIGHT_UNTRUSTED_MCP_SERVERS", "brave_search")
        assert not _should_wrap("mcp__filesystem__read")


class TestSpotlight:
    def test_spaces_replaced_with_marker(self):
        result = _spotlight("hello world", "web")
        assert f"hello{SPOTLIGHT_MARKER}world" in result

    def test_wrapped_in_untrusted_tags(self):
        result = _spotlight("content", "web")
        assert result.startswith('<UNTRUSTED source="web"')
        assert result.endswith("</UNTRUSTED>")

    def test_source_attribute_present(self):
        result = _spotlight("content", "mcp:brave_search")
        assert 'source="mcp:brave_search"' in result

    def test_marker_attribute_present(self):
        result = _spotlight("content", "web")
        assert f'marker="{SPOTLIGHT_MARKER}"' in result

    def test_escapes_closing_tag_in_content(self):
        result = _spotlight("</UNTRUSTED>", "web")
        assert "</UNTRUSTED_esc>" in result
        assert result.endswith("</UNTRUSTED>")  # only the real closing tag

    def test_escapes_opening_tag_in_content(self):
        result = _spotlight("<UNTRUSTED>", "web")
        assert "<UNTRUSTED_esc>" in result

    def test_strips_marker_collision_from_input(self):
        poisoned = f"before{SPOTLIGHT_MARKER}after"
        result = _spotlight(poisoned, "web")
        # Input marker removed, no spaces in "beforeafter", so inner is clean
        inner_start = result.index(">\n") + 2
        inner_end = result.rindex("\n<")
        inner = result[inner_start:inner_end]
        assert "beforeafter" in inner


class TestCallback:
    def test_wraps_web_search(self):
        result = spotlight_tool_result("web_search", {}, "some result", None, None, None, 0)
        assert result is not None
        assert "<UNTRUSTED" in result

    def test_passes_through_non_string_result(self):
        assert spotlight_tool_result("web_search", {}, 42, None, None, None, 0) is None

    def test_passes_through_empty_string(self):
        assert spotlight_tool_result("web_search", {}, "", None, None, None, 0) is None
        assert spotlight_tool_result("web_search", {}, "   ", None, None, None, 0) is None

    def test_passes_through_unwrapped_tool(self):
        assert spotlight_tool_result("read_file", {}, "content", None, None, None, 0) is None

    def test_passes_through_empty_tool_name(self):
        assert spotlight_tool_result("", {}, "content", None, None, None, 0) is None

    def test_accepts_unknown_future_kwargs(self):
        result = spotlight_tool_result(
            "web_search", {}, "text", None, None, None, 0, future_param="ignored"
        )
        assert result is not None

    def test_dry_run_returns_none(self, monkeypatch):
        monkeypatch.setenv("SPOTLIGHT_DRY_RUN", "true")
        assert spotlight_tool_result("web_search", {}, "text", None, None, None, 0) is None

    def test_dry_run_false_wraps_normally(self, monkeypatch):
        monkeypatch.setenv("SPOTLIGHT_DRY_RUN", "false")
        result = spotlight_tool_result("web_search", {}, "text", None, None, None, 0)
        assert result is not None

    def test_exception_in_spotlight_passes_through(self, monkeypatch):
        def boom(*_a, **_kw):
            raise RuntimeError("simulated failure")

        monkeypatch.setattr(spl, "_spotlight", boom)
        assert spotlight_tool_result("web_search", {}, "text", None, None, None, 0) is None
