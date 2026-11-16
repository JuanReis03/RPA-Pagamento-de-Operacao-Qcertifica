# RPA Pagamento de Operação - Qcertifica

Robô (RPA) que acompanha o chat **Pagamento Operação** do Microsoft Teams da Nacional Cred, confere os dados de pagamento de cada operação entre o **WBA Securitização FIDC** e o **Portal FIDC** e prepara a assinatura no **QCertifica**.

> **Status:** em desenvolvimento. Teams e login no QCertifica (homologação) estão funcionando. WBA FIDC e Portal FIDC aguardam acesso. Veja [Situação atual](#situação-atual).

---

## Sumário

- [O processo que o robô automatiza](#o-processo-que-o-robô-automatiza)
- [Regras de negócio](#regras-de-negócio)
- [Situação atual](#situação-atual)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração (.env)](#configuração-env)
- [Como usar](#como-usar)
- [Teams: Microsoft Graph](#teams-microsoft-graph)
- [QCertifica](#qcertifica)
- [Segurança](#segurança)
- [Logs](#logs)
- [Testes](#testes)
- [Documentação](#documentação)
- [Convenções de desenvolvimento](#convenções-de-desenvolvimento)

---

## O processo que o robô automatiza

Quando uma operação é aprovada e fica **Concluída** no WBA, ela vai automaticamente para o QCertifica e alguém posta no chat do Teams uma mensagem como:

```
OP. 54930 - VC DISTRIBUIDORA
ITAÚ X SANTANDER
```

junto com o PDF da operação. A partir daí, o processo manual (que o robô vai reproduzir) é:

| # | Sistema | O que acontece |
|---|---|---|
| 1 | **Teams** (chat *Pagamento Operação*) | Ler a mensagem: número da OP (borderô) e sigla/nome da empresa |
| 2 | **WBA Securitização FIDC** | *Estados* › *Fluxo* › achar a OP pelo número e conferir que está **Concluída** |
| 3 | **WBA** | Abrir o borderô (janela *Desconto de títulos*) › aba **Pagamento**: valor, banco, agência e conta |
| 4 | **Portal FIDC** (aprovar liquidação) | Pesquisar pelo **nome da empresa** e ler valor, banco, agência (sem dígito) e conta |
| 5 | Comparação | Os dados do Portal FIDC batem com os do WBA? |
| 6 | **QCertifica** | Achar a operação em *Documentos Pendentes* e assinar |
| 7 | **Teams** | Marcar a OP como tratada (reação ou resposta) |

O roteiro completo, com exemplos reais de mensagens, está em [docs/ROTEIRO_PAGAMENTO_OPERACAO.md](docs/ROTEIRO_PAGAMENTO_OPERACAO.md).

### Formato da mensagem

- **1ª linha:** `OP[.] <número> [-] <sigla>`. Exemplos: `OP 54826 CITYGUSA`, `OP. 54825 - OLIVEIRA HORA`, `OP. 54914 - D'CHICO`.
- **2ª linha (varia):** `LIBERADA PELO FIDC`, `100% RECOMPRA` ou `BANCO X BANCO`, em que o **1º banco é a origem e o 2º o destino** (`ITAÚ X SANTANDER`: sai do Itaú, vai para o Santander).
- **Anexo:** PDF da operação (ex.: `OP 54930 VC DISTRIBUIDORA.pdf`).
- Mensagens que não seguem o formato (conversa entre as pessoas) são ignoradas.

---

## Regras de negócio

- **Só se trata uma operação que apareceu no grupo.** Ela só aparece lá quando está Concluída no WBA; o robô lê esse estado apenas como garantia.
- No **WBA** a operação é achada pelo **número da OP**. No **Portal FIDC** pelo **nome da empresa** (o número não existe lá).
- No **Portal FIDC** o robô **só lê**: não aprova liquidação.
- OP que já tem reação **✅** no Teams foi tratada por alguém: o robô **pula**.
- A assinatura no QCertifica é feita **com a conta que tem certificado digital**.

Perguntas ainda em aberto com o negócio: [docs/PERGUNTAS_REUNIAO.md](docs/PERGUNTAS_REUNIAO.md).

---

## Situação atual

| Parte | Situação |
|---|---|
| Teams: ler o chat de pagamentos | ✅ funcionando (Microsoft Graph) |
| Teams: reconhecer a OP na mensagem | ✅ número, sigla, situação, banco de origem e de destino |
| Teams: ver reações e nome do PDF anexado | ✅ |
| Teams: enviar mensagem | ✅ **somente no chat de teste** (prod travado no código) |
| QCertifica: login (homologação) | ✅ chega em *Documentos Pendentes (FAS906)* |
| QCertifica: achar e assinar a operação | ⏳ falta uma operação de teste em homologação |
| WBA Securitização FIDC | ⏳ aguardando acesso |
| Portal FIDC | ⏳ aguardando acesso |
| Comparação WBA × Portal FIDC | ⏳ depende dos dois acima |
| Fluxo ponta a ponta | ⏳ |

O diário com decisões, achados e pendências fica em [CHECKLIST.md](CHECKLIST.md).

---

## Estrutura do projeto

```
.
├── src/
│   ├── domain/
│   │   └── mensagem_op.py         # leitura da mensagem "OP número sigla" (regra pura, sem I/O)
│   └── infrastructure/
│       ├── log.py                 # log por execução, com máscara de segredos
│       └── teams/
│           └── graph_teams.py     # Teams via Microsoft Graph (ler, enviar só no chat de teste)
├── scripts/
│   ├── teste_teams.py             # login / leitura / envio de teste no Teams
│   └── mapear_qcertifica.py       # login no QCertifica e mapeamento das telas (print + JSON)
├── tests/                         # testes automáticos (sem acessar sistemas reais)
├── docs/
│   ├── ROTEIRO_PAGAMENTO_OPERACAO.md
│   ├── PERGUNTAS_REUNIAO.md
│   ├── PROMPT_RPA_WBA.md          # regras de trabalho para RPA no WBA
│   ├── MAPEAMENTO_WBA_RPA.md      # mapa de telas e controles do WBA (de outros robôs)
│   └── mapeamento/                # prints e JSON gerados (fora do git)
├── CHECKLIST.md                   # decisões, achados, pendências e log datado
├── pyproject.toml
├── .env.example                   # modelo de configuração
├── data/                          # login guardado do Teams (fora do git)
└── logs/                          # um arquivo de log por execução (fora do git)
```

A organização segue Clean Architecture: `domain` não depende de nada externo; `infrastructure` fala com os sistemas (Teams, QCertifica e, depois, WBA e Portal FIDC).

---

## Requisitos

- Windows 10/11
- Python **3.12+**
- [uv](https://docs.astral.sh/uv/) (gerenciador de pacotes e ambiente)
- Acesso de rede ao Microsoft 365 da Nacional Cred e ao QCertifica
- Para o WBA (futuro): `Securitizacao.exe` instalado na máquina

---

## Instalação

```powershell
git clone <url-do-repositório>
cd RPA_Qcertifica

uv sync --extra dev                  # cria o ambiente e instala as dependências
uv run playwright install chromium   # navegador usado no QCertifica e no Portal FIDC

copy .env.example .env               # depois preencha o .env
```

---

## Configuração (.env)

Todas as credenciais ficam **só** no arquivo `.env`, que está no `.gitignore`. Use o [.env.example](.env.example) como modelo.

| Variável | Para que serve |
|---|---|
| `QCERTIFICA_PORTAL_URL` | Endereço do portal QCertifica (homologação ou produção) |
| `QCERTIFICA_API_URL` | API do QCertifica (`ws-hom` em homologação, `ws` em produção) |
| `QCERTIFICA_TOKEN` | Token de integração da API |
| `QCERTIFICA_CPF` / `QCERTIFICA_SENHA` | Login no portal (CPF sem pontuação) |
| `MS_CLIENT_ID` | *ID do aplicativo (cliente)* do app "RPA Pagamento Operação" no Entra ID |
| `MS_TENANT_ID` | *ID do diretório (locatário)* ou o domínio da empresa |
| `MS_USERNAME` | Conta do Microsoft 365 que participa do chat |
| `MS_PASSWORD` | Não usado (a conta tem MFA; ver abaixo) |
| `MS_GRAPH_BASE_URL` | `https://graph.microsoft.com` |
| `TEAMS_CHAT_ID_TESTE` | ID do chat de teste (`19:...@thread.v2`) |
| `TEAMS_CHAT_ID_PROD` | ID do chat *Pagamento Operação* |
| `TEAMS_AMBIENTE` | `teste` ou `prod`; **o envio vai sempre para o chat de teste**, seja qual for |
| `WBA_*` / `PORTAL_FIDC_*` | Acessos ao WBA FIDC e ao Portal FIDC (pendentes) |

---

## Como usar

### Teams

```powershell
# 1ª vez (ou quando o login expirar): login por código + MFA
uv run python scripts/teste_teams.py login

# só leitura: últimas mensagens do chat de teste e do chat de prod, com a OP reconhecida
uv run python scripts/teste_teams.py ler

# envia 1 mensagem de teste no chat de TESTE
uv run python scripts/teste_teams.py enviar-teste
```

### QCertifica

```powershell
# só abre e mapeia a tela de login
uv run python scripts/mapear_qcertifica.py login

# faz login e mapeia a tela seguinte
uv run python scripts/mapear_qcertifica.py entrar
```

Cada tela gera um print (`.png`) e a lista de campos/botões (`.json`) em `docs/mapeamento/qcertifica/`.

Códigos de saída do `entrar`: `0` login concluído · `1` erro inesperado · `2` senha expirada (trocar manualmente e atualizar o `.env`) · `3` CPF ou senha recusados. O script **não tenta de novo**, para não bloquear a conta.

---

## Teams: Microsoft Graph

O robô usa um app registrado no **Microsoft Entra ID** da Nacional Cred:

- **Nome:** RPA Pagamento Operação · **Tipo de conta:** somente locatário único
- **Permissões delegadas:** `Chat.Read`, `ChatMessage.Send`, `User.Read` (consentimento do administrador concedido)
- **Autenticação:** *Permitir fluxos de clientes públicos* ativado

Permissões delegadas significam que o robô só enxerga os chats da própria conta que fez login.

**Login:** a conta tem verificação em duas etapas, então login com senha é recusado (`AADSTS50076`). O robô usa **login por código de dispositivo**: na primeira vez, `scripts/teste_teams.py login` mostra um link e um código; a pessoa abre o link, digita o código e aprova o MFA. O login fica guardado em `data/msal_cache.bin` e é renovado sozinho enquanto o robô é usado. Se expirar, o robô avisa e basta repetir o `login`.

**O que o Graph entrega de cada mensagem:** texto, autor, data, **reações** (ex.: ✅) e **anexos**. O PDF da OP vem como link para o OneDrive de quem postou; ler o conteúdo exigiria a permissão extra `Files.Read.All` (pendente, talvez desnecessária).

---

## QCertifica

- **Homologação:** portal `portal-novo-hom.qcertifica.com.br`, API `ws-hom.qcertifica.com.br`.
- **Produção:** API `ws.qcertifica.com.br`.
- **Login:** campos `#ctl00_body_txtUsuario`, `#ctl00_body_txtSenha`, botão `#ctl00_body_btnEntrar`. No 1º acesso o portal exige troca de senha (`AlterarSenha.aspx`); o robô não troca senha.
- **Depois do login:** tela **Documentos Pendentes (FAS906)**, com quadros *Contratantes*, *Remessas* e *Poderes*, abas *Cedente / Contratante / Administradora / Ignorar*, botões **Buscar / Rejeitar / Assinar** e a lista de documentos (remessa, cedente, documento, tipo, título, sacado, valor, data).
- **API** ([documentação](https://apidocs.qcertifica.quicksoft.com.br)): é de integração do ERP para o QCertifica (importar remessa, cedentes, documentos; status de assinatura; download). Não tem endpoint para listar pendentes nem para assinar, por isso a assinatura é feita pelo portal.

---

## Segurança

- **Nenhum envio no chat de produção.** A única função que envia (`TeamsGraph.enviar_no_chat_teste`) usa sempre `TEAMS_CHAT_ID_TESTE` e recusa um ID igual ao de prod, ignorando `TEAMS_AMBIENTE`. Se os IDs de teste e prod forem iguais no `.env`, o robô nem inicia. Liberar prod exige mudar o código de propósito, depois de autorização expressa.
- **Credenciais só no `.env`**, nunca em código, log, documentação ou commit.
- **Log com máscara:** valores de variáveis terminadas em `SENHA`, `TOKEN`, `CPF`, `USUARIO`, `PASSWORD` ou `USERNAME` viram `***`.
- **Fora do git:** `.env`, `data/` (login do Teams), `logs/`, `docs/mapeamento/` (prints com dados reais), `uv.lock`.
- **Sem tentativas repetidas de login** no QCertifica, para não bloquear a conta.
- O robô **só lê** no WBA e no Portal FIDC.

---

## Logs

Cada execução cria `logs/AAAAMMDD_HHMMSS_<nome>.log` e mostra o mesmo conteúdo na tela:

```
2026-11-16 14:00:01 [INFO] teste_teams: Conectado como: ...
2026-11-16 14:00:06 [INFO] teste_teams: ... | [OP 54930 | VC DISTRIBUIDORA | ITAÚ X SANTANDER] | ...
```

Para usar em código novo:

```python
from dotenv import load_dotenv
from src.infrastructure.log import configurar_log

load_dotenv(".env")              # antes, para a máscara conhecer os segredos
log = configurar_log("meu_fluxo")
log.info("Abrindo o WBA")
```

---

## Testes

```powershell
uv run pytest
```

Os testes não acessam nenhum sistema real:

| Arquivo | O que garante |
|---|---|
| `tests/test_mensagem_op.py` | Leitura das mensagens reais de OP (número, sigla, situação, bancos) e rejeição do que não é OP |
| `tests/test_trava_prod.py` | Envio vai sempre para o chat de teste; ID de teste igual ao de prod é recusado |
| `tests/test_log.py` | O log grava em arquivo e esconde CPF e senha |

---

## Documentação

| Arquivo | Conteúdo |
|---|---|
| [CHECKLIST.md](CHECKLIST.md) | Decisões, pendências técnicas, achados e log datado |
| [docs/ROTEIRO_PAGAMENTO_OPERACAO.md](docs/ROTEIRO_PAGAMENTO_OPERACAO.md) | O processo manual passo a passo e exemplos reais |
| [docs/PERGUNTAS_REUNIAO.md](docs/PERGUNTAS_REUNIAO.md) | Perguntas em aberto para o negócio |
| [docs/PROMPT_RPA_WBA.md](docs/PROMPT_RPA_WBA.md) | Regras de trabalho e robustez para RPA no WBA |
| [docs/MAPEAMENTO_WBA_RPA.md](docs/MAPEAMENTO_WBA_RPA.md) | Telas, controles e armadilhas do WBA (de outros robôs; a janela *Desconto de títulos* está na seção 15) |

---

## Convenções de desenvolvimento

- **Mapear antes de automatizar:** nunca adivinhar seletor ou controle; gerar print + JSON da tela primeiro.
- **Evidência, não suposição:** log, print, erro exato.
- **Documentar enquanto descobre:** cada achado vai para o `CHECKLIST.md` com data.
- **Commits em inglês**, sem `--force`.
- Antes de subir: `uv run pytest` passando.
