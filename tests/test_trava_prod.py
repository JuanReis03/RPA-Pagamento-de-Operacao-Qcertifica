import pytest

from src.infrastructure.teams import graph_teams
from src.infrastructure.teams.graph_teams import EnvioBloqueado, TeamsGraph


@pytest.fixture
def env(monkeypatch, tmp_path):
    monkeypatch.setattr(graph_teams, "CACHE_TOKEN", tmp_path / "cache.bin")
    monkeypatch.setattr(graph_teams.msal, "PublicClientApplication", lambda *a, **k: object())
    for k, v in {
        "MS_CLIENT_ID": "x", "MS_TENANT_ID": "y",
        "TEAMS_CHAT_ID_TESTE": "19:teste@thread.v2", "TEAMS_CHAT_ID_PROD": "19:prod@thread.v2",
    }.items():
        monkeypatch.setenv(k, v)


def test_teste_igual_prod_e_recusado(env, monkeypatch):
    monkeypatch.setenv("TEAMS_CHAT_ID_TESTE", "19:prod@thread.v2")
    with pytest.raises(EnvioBloqueado):
        TeamsGraph()


def test_envio_vai_sempre_para_o_chat_de_teste(env, monkeypatch):
    monkeypatch.setenv("TEAMS_AMBIENTE", "prod")  # mesmo assim não pode ir para prod
    t = TeamsGraph()
    chamadas = []
    monkeypatch.setattr(t, "_req", lambda metodo, caminho, **kw: chamadas.append(caminho) or {"id": "1"})
    t.enviar_no_chat_teste("oi")
    assert chamadas == ["/chats/19:teste@thread.v2/messages"]


def test_envio_bloqueado_se_chat_teste_virar_prod(env):
    t = TeamsGraph()
    t.chat_teste = t.chat_prod
    with pytest.raises(EnvioBloqueado):
        t.enviar_no_chat_teste("oi")
