import pytest

from src.domain.mensagem_op import MensagemOP, ler_mensagem_op


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("OP 54826 CITYGUSA\nLIBERADA PELO FIDC", MensagemOP("54826", "CITYGUSA", "LIBERADA PELO FIDC")),
        ("OP. 54825 - OLIVEIRA HORA  \nLIBERADA PELO FIDC", MensagemOP("54825", "OLIVEIRA HORA", "LIBERADA PELO FIDC")),
        ("OP 54824 - POLLUX\nLIBERADA PELO FIDC\n ", MensagemOP("54824", "POLLUX", "LIBERADA PELO FIDC")),
        ("OP 54833 FEIRA AMERICAN\nITAU X ITAU", MensagemOP("54833", "FEIRA AMERICAN", "ITAU X ITAU", "ITAU", "ITAU")),
        ("OP 54834 GANDULAR\nITAÚ X BRADESCO", MensagemOP("54834", "GANDULAR", "ITAÚ X BRADESCO", "ITAÚ", "BRADESCO")),
        ("OP. 54930 - VC DISTRIBUIDORA\nITAÚ X SANTANDER",
         MensagemOP("54930", "VC DISTRIBUIDORA", "ITAÚ X SANTANDER", "ITAÚ", "SANTANDER")),
        ("OP 54918 GABRIELA\n100% RECOMPRA", MensagemOP("54918", "GABRIELA", "100% RECOMPRA")),
        ("OP. 54914 - D'CHICO\nLIBERADA PELO FIDC", MensagemOP("54914", "D'CHICO", "LIBERADA PELO FIDC")),
        ("OP. 54829 - LACGLORIA\nLIBERADA PELO FIDC", MensagemOP("54829", "LACGLORIA", "LIBERADA PELO FIDC")),
        ("OP 54827 PREMOL", MensagemOP("54827", "PREMOL", "")),
    ],
)
def test_mensagens_reais(texto, esperado):
    assert ler_mensagem_op(texto) == esperado


@pytest.mark.parametrize("texto", ["", "bom dia", "OPERAÇÃO pendente", "OP sem numero", "ok"])
def test_mensagens_que_nao_sao_op(texto):
    assert ler_mensagem_op(texto) is None
