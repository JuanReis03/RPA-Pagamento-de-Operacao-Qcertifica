# CHECKLIST — RPA Pagamento de Operação (QCertifica)

Documentos de referência:
- `docs/ROTEIRO_PAGAMENTO_OPERACAO.md` — o processo a automatizar.
- `docs/PERGUNTAS_REUNIAO.md` — perguntas em aberto para o negócio.
- `docs/PROMPT_RPA_WBA.md` — regras de trabalho e de robustez para RPA no WBA.
- `docs/MAPEAMENTO_WBA_RPA.md` — mapa de telas/controles do WBA (de outros RPAs; a seção 15 cobre a janela *Desconto de títulos*, só por leitura de código).

## Decisões
- 2026-11-11 — Teams é lido **pela tela do próprio Teams** (sem Microsoft Graph), com usuário ADMIN.
- 2026-11-16 — Teams lido e escrito via **Microsoft Graph** (substitui a leitura pela tela). App "RPA Pagamento Operação" registrado no Entra (locatário único, permissões delegadas `Chat.Read`, `ChatMessage.Send`, `User.Read`, consentimento do admin dado, fluxo de cliente público ativo). "Pagamento Operação" é **chat em grupo**.
- 2026-11-16 — Conta do Teams tem **MFA**: login por **código de dispositivo** uma vez (`scripts/teste_teams.py login`); depois o login fica em `data/msal_cache.bin` (fora do git). `MS_PASSWORD` não é usado.
- 2026-11-16 — O RPA **pula OP que já tem reação ✅** (alguém já tratou).
- 2026-11-16 — **Nunca enviar no chat de PROD** até ordem expressa do usuário. Trava no código: `TeamsGraph.enviar_no_chat_teste` só envia para `TEAMS_CHAT_ID_TESTE` e recusa ID igual ao de prod, ignorando `TEAMS_AMBIENTE` (testes em `tests/test_trava_prod.py`).
- 2026-11-11 — Portal FIDC **não** é o Portal Nacional Cred: automação pela tela (navegador). O RPA **só lê**.
- 2026-11-11 — No Portal FIDC a operação é achada pelo **nome da empresa**; o número da OP não serve lá. Valor pode virar 2º critério (a avaliar).
- 2026-11-11 — No WBA a operação é achada pelo **número da OP**. O RPA **só lê** o estado "Concluída", como garantia (se está no grupo, já está concluída).
- 2026-11-11 — Assinatura no QCertifica é **via conta com certificado** (o usuário providencia).
- 2026-11-11 — Marcar OP tratada no Teams: reagir com emoji ou responder "OK" (a definir qual).
- 2026-11-11 — QCertifica: usar **homologação**. Token e login ficam só no `.env`.

## Pendências
Perguntas ao negócio: ver `docs/PERGUNTAS_REUNIAO.md`.

Técnicas:
- [ ] **PDF anexado à OP** (talvez não seja necessário): o RPA já vê o nome do PDF. Baixar o conteúdo exige a permissão extra `Files.Read.All` no app do Entra. Só pedir se o RPA precisar ler algum dado do PDF.
- [ ] Acesso ao **WBA Securitização FIDC** e ao **Portal FIDC** (com usuário aguardando).
- [ ] Operação de teste no **QCertifica** homologação para ver como ela aparece na tela Documentos Pendentes.

## Achados
- 2026-11-11 — A API do QCertifica (`apidocs.qcertifica.quicksoft.com.br`) é de **integração do ERP para o QCertifica** (importar remessa, cedentes, documentos; status de assinatura; download). Na página principal **não há** endpoint para listar pendentes nem para assinar: assinatura pelo portal. Falta abrir cada endpoint para ver se dá para **consultar** status.
- 2026-11-11 — Formato da 1ª linha da mensagem varia: `OP 54826 CITYGUSA`, `OP. 54825 - OLIVEIRA HORA`, `OP 54824 - POLLUX`. Regra de leitura: `OP` + ponto opcional + número + hífen opcional + sigla (pode ter espaços). Sigla = parte ou todo o nome da empresa.
- 2026-11-11 — O mesmo cedente pode ter 2 OPs no mesmo dia (GANDULAR 54831 e 54834): buscar só pelo nome no Portal FIDC pode ser ambíguo.

- 2026-11-11 — **QCertifica login** (`Authentication/Login.aspx`): IDs estáveis `#ctl00_body_txtUsuario` (CPF), `#ctl00_body_txtSenha`, `#ctl00_body_btnEntrar`. Login com CPF + senha provisória **funcionou**, mas cai em `Authentication/AlterarSenha.aspx` ("Sua senha expirou"): `#ctl00_body_txtNovaSenha`, `#ctl00_body_txtConfirmarNovaSenha`, `#ctl00_body_btnAlterarSenha`. O RPA **não** troca senha: foi parado aí.

- 2026-11-11 — Login recusado mostra o aviso "Senha Incorreta ou Usuário não cadastrado" e fica em `Login.aspx`. O script trata como falha (código 3) e **não tenta de novo** (risco de bloquear a conta).
- 2026-11-11 — ✅ **Login do RPA validado** com a senha nova (CPF + senha). Cai direto em **Documentos Pendentes (FAS906)** (`DigitalSignature/FAS906.aspx`): grades *Contratantes*, *Remessas* (Código, Descrição, Títulos, Dt. Recebimento) e *Poderes* (filtro Todos); abas "pendentes de assinatura com" **Cedente / Contratante / Administradora / Ignorar**; botões **Buscar / Rejeitar / Assinar**; grade principal com Remessa, Contratante, Cedente, Poder, Documento, Tipo, Título, Sacado, Valor, Dt. Recebimento. Em homologação: nenhum documento pendente. Esta deve ser a tela onde o RPA acha e assina a operação (a confirmar com uma operação de teste).
- 2026-11-16 — ✅ **Teams validado:** leitura dos chats de teste e prod e envio de 1 mensagem no chat de **teste** (lida de volta pelo Graph). Leitor `ler_mensagem_op` acertou todas as OPs reais do chat de prod.
- 2026-11-16 — Novas variações da 2ª linha vistas em prod: `ITAÚ X SANTANDER`, `100% RECOMPRA`. Siglas com ponto/apóstrofo: `EST. GANDULAR`, `D'CHICO`, `LER`.
- 2026-11-16 — O chat de prod também tem conversa entre as pessoas ("Falta subir no banco", "Feito Jaque", "pago. obrigada", "Favor considerar o borderô correto este:" seguido de nova OP). O RPA ignora mensagens que não são OP, mas uma correção ("borderô correto este") pode substituir uma OP anterior: **perguntar como tratar**.
- 2026-11-16 — 2ª linha `BANCO X BANCO`: **1º = banco de origem, 2º = banco de destino** (ex.: `ITAÚ X SANTANDER`). `ler_mensagem_op` devolve `banco_origem`/`banco_destino`.
- 2026-11-16 — Cada mensagem de OP vem com **PDF da operação** anexado (ex.: `OP 54930 VC DISTRIBUIDORA.pdf`). No Graph o anexo é `reference` apontando para o OneDrive de quem postou (`nacionalcred-my.sharepoint.com`). Baixar o PDF exigiria a permissão extra `Files.Read.All`: só pedir se o RPA precisar do conteúdo.
- 2026-11-16 — **Reações** vêm no Graph: OPs pagas têm ✅; a 54922 tem 🟨 e ✅. Pode servir para o RPA pular OP já tratada. Respostas como "pago. obrigada" citam a mensagem original (`messageReference`).

## Log
- 2026-11-11 — Projeto iniciado; documentos de referência e roteiro adicionados em `docs/`.
- 2026-11-11 — Respostas do negócio registradas; `.env` (fora do git) e `.env.example` criados; primeira leitura da documentação da API do QCertifica.
- 2026-11-11 — 2ª rodada de respostas; exemplos reais de mensagens; perguntas restantes em `docs/PERGUNTAS_REUNIAO.md`.
- 2026-11-11 — Projeto Python (uv + Playwright) criado; script `scripts/mapear_qcertifica.py`; login do QCertifica mapeado (cai em troca de senha); log por execução em `logs/` com máscara de segredos (`src/infrastructure/log.py`, teste em `tests/test_log.py`).
