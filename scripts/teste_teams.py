"""Teste do Teams via Graph.

    uv run python scripts/teste_teams.py login          # uma vez: login com código + MFA (conta tem MFA)
    uv run python scripts/teste_teams.py ler            # SÓ LEITURA: chats de teste e prod
    uv run python scripts/teste_teams.py enviar-teste   # envia 1 mensagem no chat de TESTE

Envio para o chat de prod é bloqueado no código (graph_teams.enviar_no_chat_teste).
"""

import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src.domain.mensagem_op import ler_mensagem_op  # noqa: E402
from src.infrastructure.log import configurar_log  # noqa: E402
from src.infrastructure.teams.graph_teams import TeamsGraph  # noqa: E402


def mostrar_chat(t: TeamsGraph, rotulo: str, chat_id: str, log) -> None:
    log.info("=== Chat %s: %s ===", rotulo, t.nome_chat(chat_id))
    for m in t.ultimas_mensagens(chat_id, 15):
        op = ler_mensagem_op(m.texto)
        marca = f"[OP {op.numero} | {op.sigla} | {op.situacao or '-'}]" if op else "[não é OP]"
        log.info("%s | %s | %s | %r", m.criada_em[:19], m.autor, marca, m.texto[:120])


def main() -> int:
    modo = sys.argv[1] if len(sys.argv) > 1 else "ler"
    load_dotenv(RAIZ / ".env")
    log = configurar_log("teste_teams")
    try:
        t = TeamsGraph()
        if modo == "login":
            t.login_por_codigo(lambda msg: log.info("AÇÃO NECESSÁRIA: %s", msg))
        else:
            t.autenticar()
        log.info("Conectado como: %s", t.eu())
        if modo == "login":
            log.info("Login guardado. Próximas execuções não pedem código.")
        elif modo == "ler":
            mostrar_chat(t, "TESTE", t.chat_teste, log)
            if t.chat_prod:
                mostrar_chat(t, "PROD (só leitura)", t.chat_prod, log)
        elif modo == "enviar-teste":
            texto = f"[TESTE RPA] Mensagem de teste do RPA Pagamento Operação ({datetime.now():%d/%m/%Y %H:%M}). Pode ignorar."
            log.info("Mensagem enviada no chat de TESTE, id=%s", t.enviar_no_chat_teste(texto))
        else:
            log.error("Modo desconhecido: %s", modo)
            return 2
    except Exception:
        log.exception("Teste do Teams falhou")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
