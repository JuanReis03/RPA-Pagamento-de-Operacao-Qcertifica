"""Mapeamento do portal QCertifica (homologação).

Uso:
    uv run python scripts/mapear_qcertifica.py login     # só abre e mapeia a tela de login
    uv run python scripts/mapear_qcertifica.py entrar    # faz login com CPF/senha do .env e mapeia a tela seguinte

Grava PNG + JSON (campos, botões, links) em docs/mapeamento/qcertifica/ e o log
da execução em logs/. Nunca registra CPF nem senha.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import Page, sync_playwright

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src.infrastructure.log import configurar_log  # noqa: E402

SAIDA = RAIZ / "docs" / "mapeamento" / "qcertifica"

JS_DUMP = """
() => {
  const vis = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const pega = sel => [...document.querySelectorAll(sel)].map(el => ({
    tag: el.tagName.toLowerCase(), id: el.id || null, name: el.getAttribute('name'),
    type: el.getAttribute('type'), placeholder: el.getAttribute('placeholder'),
    text: (el.innerText || el.value || '').trim().slice(0, 120),
    href: el.getAttribute('href'), classe: el.className && String(el.className).slice(0, 120),
    visivel: vis(el)
  }));
  return {
    title: document.title, url: location.href,
    inputs: pega('input, select, textarea').map(c => (c.type === 'password' ? {...c, text: '***'} : c)),
    botoes: pega('button, input[type=submit], input[type=button], a.btn, [role=button]'),
    links: pega('a').filter(a => a.visivel).slice(0, 150),
    frames: [...document.querySelectorAll('iframe')].map(f => f.src),
  };
}
"""


def salvar(page: Page, nome: str, log) -> dict:
    SAIDA.mkdir(parents=True, exist_ok=True)
    base = SAIDA / f"{datetime.now():%Y%m%d_%H%M%S}_{nome}"
    page.screenshot(path=f"{base}.png", full_page=True)
    dump = page.evaluate(JS_DUMP)
    Path(f"{base}.json").write_text(json.dumps(dump, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Tela '%s' salva em %s.png/.json", nome, base.name)
    return dump


def resumo(dump: dict, log) -> None:
    log.info("Título: %s | URL: %s", dump["title"], dump["url"])
    for c in dump["inputs"]:
        if c["visivel"]:
            log.info("  campo: %s type=%s id=%s", c["tag"], c["type"], c["id"])
    for b in dump["botoes"]:
        if b["visivel"]:
            log.info("  botão: %s id=%s texto=%r", b["tag"], b["id"], b["text"])
    if dump["frames"]:
        log.info("  iframes: %s", dump["frames"])


def main() -> int:
    modo = sys.argv[1] if len(sys.argv) > 1 else "login"
    load_dotenv(RAIZ / ".env")
    log = configurar_log("mapear_qcertifica")
    url = os.environ["QCERTIFICA_PORTAL_URL"]
    log.info("Modo '%s'. Vou abrir o portal QCertifica.", modo)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1366, "height": 900}, locale="pt-BR")
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            resumo(salvar(page, "01_login", log), log)

            if modo == "entrar":
                log.info("Preenchendo CPF e senha do .env e clicando em Entrar.")
                page.locator("#ctl00_body_txtUsuario").fill(os.environ["QCERTIFICA_CPF"])
                page.locator("#ctl00_body_txtSenha").fill(os.environ["QCERTIFICA_SENHA"])
                page.locator("#ctl00_body_btnEntrar").click()
                page.wait_for_load_state("networkidle", timeout=60000)
                page.wait_for_timeout(2000)
                dump = salvar(page, "03_pos_login", log)
                resumo(dump, log)

                if "AlterarSenha.aspx" in page.url:
                    log.error("Senha expirada: o portal pede troca de senha. O RPA não troca senha; "
                              "troque manualmente e atualize QCERTIFICA_SENHA no .env.")
                    return 2
                if "Login.aspx" in page.url:
                    log.error("Continua na tela de login: CPF ou senha recusados (ver print 03_pos_login).")
                    return 3
                log.info("Login concluído.")
        except Exception:
            log.exception("Falha no mapeamento do QCertifica")
            return 1
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
