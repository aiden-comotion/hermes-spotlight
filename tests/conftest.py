import pytest

_SPOTLIGHT_ENVS = (
    "SPOTLIGHT_DRY_RUN",
    "SPOTLIGHT_UNTRUSTED_MCP_SERVERS",
    "SPOTLIGHT_TRUSTED_MCP_SERVERS",
)


@pytest.fixture(autouse=True)
def clear_spotlight_env(monkeypatch):
    for key in _SPOTLIGHT_ENVS:
        monkeypatch.delenv(key, raising=False)
