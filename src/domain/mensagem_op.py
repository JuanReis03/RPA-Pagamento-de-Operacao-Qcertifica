"""Leitura da mensagem de operação postada no chat Pagamento Operação.

Formato da 1ª linha: ``OP[.] <número> [-] <sigla>``; a 2ª linha (situação) varia.
Exemplos reais: "OP 54826 CITYGUSA", "OP. 54825 - OLIVEIRA HORA".
"""

import re
from dataclasses import dataclass

_PRIMEIRA_LINHA = re.compile(r"^\s*OP\.?\s*(\d{3,})\s*[-–]?\s*(.+?)\s*$", re.IGNORECASE)
# "ITAÚ X SANTANDER": 1º = banco de origem, 2º = banco de destino
_BANCOS = re.compile(r"^\s*(.+?)\s+X\s+(.+?)\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class MensagemOP:
    numero: str
    sigla: str
    situacao: str  # 2ª linha em diante, "" se não houver
    banco_origem: str | None = None
    banco_destino: str | None = None


def ler_mensagem_op(texto: str) -> MensagemOP | None:
    """Devolve a OP da mensagem, ou None se a mensagem não segue o formato."""
    linhas = [l.strip() for l in texto.strip().splitlines() if l.strip()]
    if not linhas:
        return None
    m = _PRIMEIRA_LINHA.match(linhas[0])
    if not m:
        return None
    situacao = " ".join(linhas[1:])
    b = _BANCOS.match(situacao)
    return MensagemOP(
        numero=m.group(1),
        sigla=m.group(2).upper(),
        situacao=situacao,
        banco_origem=b.group(1).upper() if b else None,
        banco_destino=b.group(2).upper() if b else None,
    )
