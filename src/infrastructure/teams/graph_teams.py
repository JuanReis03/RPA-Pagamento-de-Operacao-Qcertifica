"""Leitura e envio no Teams via Microsoft Graph (permissões delegadas).

TRAVA DE SEGURANÇA: enviar mensagem só é permitido no chat de TESTE
(TEAMS_CHAT_ID_TESTE). Qualquer tentativa de enviar para o chat de PROD
(TEAMS_CHAT_ID_PROD) levanta EnvioBloqueado, seja qual for o TEAMS_AMBIENTE.
Liberar prod exige mudar este código de propósito.
"""

from __future__ import annotations

import html
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path

import msal
import requests

log = logging.getLogger(__name__)

RAIZ = Path(__file__).resolve().parents[3]
CACHE_TOKEN = RAIZ / "data" / "msal_cache.bin"
ESCOPOS = ["Chat.Read", "ChatMessage.Send", "User.Read"]


class ErroTeams(Exception):
    pass


class EnvioBloqueado(ErroTeams):
    pass


@dataclass(frozen=True)
class MensagemTeams:
    id: str
    criada_em: str
    autor: str
    texto: str


def _html_para_texto(conteudo: str) -> str:
    conteudo = re.sub(r"<br\s*/?>|</p>|</div>", "\n", conteudo, flags=re.I)
    conteudo = re.sub(r"<[^>]+>", "", conteudo)
    linhas = [html.unescape(l).replace("\xa0", " ").strip() for l in conteudo.splitlines()]
    return "\n".join(l for l in linhas if l)


class TeamsGraph:
    def __init__(self) -> None:
        self.base = os.environ.get("MS_GRAPH_BASE_URL", "https://graph.microsoft.com").rstrip("/") + "/v1.0"
        self.chat_teste = os.environ["TEAMS_CHAT_ID_TESTE"].strip()
        self.chat_prod = os.environ.get("TEAMS_CHAT_ID_PROD", "").strip()
        if self.chat_prod and self.chat_teste == self.chat_prod:
            raise EnvioBloqueado("TEAMS_CHAT_ID_TESTE é igual ao de PROD: corrija o .env.")
        self._cache = msal.SerializableTokenCache()
        if CACHE_TOKEN.exists():
            self._cache.deserialize(CACHE_TOKEN.read_text(encoding="utf-8"))
        self._app = msal.PublicClientApplication(
            os.environ["MS_CLIENT_ID"],
            authority=f"https://login.microsoftonline.com/{os.environ['MS_TENANT_ID']}",
            token_cache=self._cache,
        )
        self._token: str | None = None

    # ---------- autenticação ----------
    def _salvar_cache(self) -> None:
        if self._cache.has_state_changed:
            CACHE_TOKEN.parent.mkdir(exist_ok=True)
            CACHE_TOKEN.write_text(self._cache.serialize(), encoding="utf-8")

    def autenticar(self) -> None:
        """Usa o login guardado em cache. A conta tem MFA: login com senha não funciona."""
        usuario = os.environ["MS_USERNAME"]
        contas = self._app.get_accounts(username=usuario)
        r = self._app.acquire_token_silent(ESCOPOS, account=contas[0]) if contas else None
        if not r or "access_token" not in r:
            raise ErroTeams("Sem login guardado (ou expirou). Rode: uv run python scripts/teste_teams.py login")
        log.info("Login no Microsoft Graph reaproveitado do cache.")
        self._token = r["access_token"]
        self._salvar_cache()

    def login_por_codigo(self, mostrar) -> None:
        """Login interativo (uma vez): a pessoa abre o link, digita o código e aprova o MFA."""
        fluxo = self._app.initiate_device_flow(scopes=ESCOPOS)
        if "user_code" not in fluxo:
            raise ErroTeams(f"Não consegui iniciar o login por código: {fluxo.get('error_description')}")
        mostrar(fluxo["message"])
        r = self._app.acquire_token_by_device_flow(fluxo)  # espera a aprovação (até ~15 min)
        if "access_token" not in r:
            codigos = r.get("error_codes")
            raise ErroTeams(f"Login no Graph falhou: {r.get('error')} {codigos} - "
                            f"{(r.get('error_description') or '').splitlines()[0]}")
        self._token = r["access_token"]
        self._salvar_cache()

    # ---------- HTTP ----------
    def _req(self, metodo: str, caminho: str, **kw) -> dict:
        if not self._token:
            self.autenticar()
        resp = requests.request(metodo, self.base + caminho, headers={"Authorization": f"Bearer {self._token}"},
                                timeout=30, **kw)
        if resp.status_code >= 400:
            raise ErroTeams(f"Graph {metodo} {caminho.split('?')[0]} -> HTTP {resp.status_code}: {resp.text[:300]}")
        return resp.json() if resp.content else {}

    # ---------- leitura ----------
    def eu(self) -> str:
        return self._req("GET", "/me?$select=displayName")["displayName"]

    def nome_chat(self, chat_id: str) -> str:
        c = self._req("GET", f"/chats/{chat_id}")
        return c.get("topic") or f"(chat sem nome, tipo {c.get('chatType')})"

    def ultimas_mensagens(self, chat_id: str, quantidade: int = 20) -> list[MensagemTeams]:
        dados = self._req("GET", f"/chats/{chat_id}/messages?$top={quantidade}")
        saida = []
        for m in dados.get("value", []):
            if m.get("messageType") != "message":
                continue
            autor = ((m.get("from") or {}).get("user") or {}).get("displayName") or "?"
            corpo = m.get("body") or {}
            texto = corpo.get("content") or ""
            if corpo.get("contentType") == "html":
                texto = _html_para_texto(texto)
            saida.append(MensagemTeams(m["id"], m.get("createdDateTime", ""), autor, texto))
        return saida

    # ---------- envio (SÓ chat de teste) ----------
    def enviar_no_chat_teste(self, texto: str) -> str:
        chat = self.chat_teste
        if chat == self.chat_prod:
            raise EnvioBloqueado("Envio para o chat de PROD bloqueado.")
        log.info("Enviando mensagem no chat de TESTE.")
        r = self._req("POST", f"/chats/{chat}/messages", json={"body": {"contentType": "text", "content": texto}})
        return r.get("id", "")
