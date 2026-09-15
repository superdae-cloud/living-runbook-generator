from types import SimpleNamespace

import pytest

from lrg import llm


@pytest.fixture(autouse=True)
def clear_anthropic_env(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)


def test_has_credentials_false_with_nothing_configured(monkeypatch, tmp_path):
    monkeypatch.setattr(llm.Path, "home", lambda: tmp_path)
    assert llm.has_credentials() is False


def test_has_credentials_true_with_api_key_env_var(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    assert llm.has_credentials() is True


def test_has_credentials_true_with_auth_token_env_var(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "token")
    assert llm.has_credentials() is True


def test_has_credentials_true_with_profile_dir(monkeypatch, tmp_path):
    profile_dir = tmp_path / ".config" / "anthropic"
    profile_dir.mkdir(parents=True)
    (profile_dir / "profile.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(llm.Path, "home", lambda: tmp_path)
    assert llm.has_credentials() is True


def test_synthesize_skips_single_ticket_cluster(monkeypatch, make_ticket):
    monkeypatch.setattr(llm, "has_credentials", lambda: True)
    result = llm.synthesize_root_cause([make_ticket(id="INC-1")])
    assert result is None


def test_synthesize_returns_none_without_credentials(monkeypatch, make_ticket):
    monkeypatch.setattr(llm, "has_credentials", lambda: False)
    tickets = [make_ticket(id="INC-1"), make_ticket(id="INC-2")]
    assert llm.synthesize_root_cause(tickets) is None


def test_synthesize_fails_soft_on_sdk_exception(monkeypatch, make_ticket):
    monkeypatch.setattr(llm, "has_credentials", lambda: True)

    class ExplodingClient:
        class messages:
            @staticmethod
            def create(**kwargs):
                raise RuntimeError("network exploded")

    anthropic_stub = SimpleNamespace(Anthropic=lambda: ExplodingClient())
    monkeypatch.setitem(__import__("sys").modules, "anthropic", anthropic_stub)

    tickets = [make_ticket(id="INC-1"), make_ticket(id="INC-2")]
    assert llm.synthesize_root_cause(tickets) is None


def test_synthesize_returns_text_on_success(monkeypatch, make_ticket):
    monkeypatch.setattr(llm, "has_credentials", lambda: True)

    fake_response = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="A malformed route-map, seen twice.")]
    )

    class FakeClient:
        class messages:
            @staticmethod
            def create(**kwargs):
                return fake_response

    anthropic_stub = SimpleNamespace(Anthropic=lambda: FakeClient())
    monkeypatch.setitem(__import__("sys").modules, "anthropic", anthropic_stub)

    tickets = [make_ticket(id="INC-1"), make_ticket(id="INC-2")]
    result = llm.synthesize_root_cause(tickets)
    assert result == "A malformed route-map, seen twice."
