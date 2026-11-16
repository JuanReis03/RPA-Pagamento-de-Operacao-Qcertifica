"""Log por execução: arquivo em logs/ + console, sem segredos.

Uso:
    from src.infrastructure.log import configurar_log
    log = configurar_log("qcertifica")
    log.info("Abrindo portal")

Cada execução gera logs/AAAAMMDD_HHMMSS_<nome>.log. Qualquer valor de variável
do .env cujo nome termine em SENHA, TOKEN, CPF, USUARIO ou PASSWORD é trocado
por *** antes de ir para o arquivo ou para a tela.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PASTA_LOGS = RAIZ / "logs"
SUFIXOS_SECRETOS = ("SENHA", "TOKEN", "CPF", "USUARIO", "PASSWORD", "USERNAME")
IGNORAR = {"USERNAME"}  # variável do Windows (usuário logado), não é segredo
FORMATO ="%(asctime)s [%(levelname)s] %(name)s: %(message)s"


class MascaraSegredos(logging.Filter):
    """Troca valores secretos do ambiente por *** em toda mensagem."""

    def __init__(self) -> None:
        super().__init__()
        self.segredos = sorted(
            {
                v
                for k, v in os.environ.items()
                if k.upper().endswith(SUFIXOS_SECRETOS) and k.upper() not in IGNORAR and len(v) >= 3
            },
            key=len,
            reverse=True,
        )

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        for s in self.segredos:
            msg = msg.replace(s, "***")
        record.msg, record.args = msg, None
        return True


def configurar_log(nome: str, nivel: int = logging.INFO) -> logging.Logger:
    """Configura o log raiz (arquivo + console) e devolve o logger `nome`.

    Chame depois de carregar o .env, para que a máscara conheça os segredos.
    """
    PASTA_LOGS.mkdir(exist_ok=True)
    arquivo = PASTA_LOGS / f"{datetime.now():%Y%m%d_%H%M%S}_{nome}.log"

    raiz = logging.getLogger()
    raiz.setLevel(nivel)
    for h in list(raiz.handlers):
        raiz.removeHandler(h)

    mascara = MascaraSegredos()
    formatador = logging.Formatter(FORMATO, datefmt="%Y-%m-%d %H:%M:%S")

    em_arquivo = logging.FileHandler(arquivo, encoding="utf-8")
    em_tela = logging.StreamHandler(sys.stdout)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for h in (em_arquivo, em_tela):
        h.setFormatter(formatador)
        h.addFilter(mascara)
        raiz.addHandler(h)

    # bibliotecas barulhentas
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    log = logging.getLogger(nome)
    log.info("Log desta execução: %s", arquivo)
    return log
