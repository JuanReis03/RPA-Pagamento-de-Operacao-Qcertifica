import logging

from src.infrastructure import log as modulo_log


def test_log_mascara_segredos_e_grava_arquivo(tmp_path, monkeypatch):
    monkeypatch.setattr(modulo_log, "PASTA_LOGS", tmp_path)
    monkeypatch.setenv("QCERTIFICA_SENHA", "senha-super-secreta")
    monkeypatch.setenv("QCERTIFICA_CPF", "12345678909")

    log = modulo_log.configurar_log("teste")
    log.info("login com %s e %s", "12345678909", "senha-super-secreta")
    for h in logging.getLogger().handlers:
        h.flush()

    arquivos = list(tmp_path.glob("*_teste.log"))
    assert len(arquivos) == 1
    texto = arquivos[0].read_text(encoding="utf-8")
    assert "login com *** e ***" in texto
    assert "senha-super-secreta" not in texto
    assert "12345678909" not in texto
