# Mapeamento do WBA Securitização para RPA

Consolidado de três fontes, com a origem de cada achado indicada:

| Origem | O que é | Confiança |
|---|---|---|
| **[BLOQUEIO]** | RPA `rpa-wba-bloqueio` (bloquear cedente): login, pesquisa, aba Crédito › Restrições | validado em execução real |
| **[SIGNATURE]** | `Grlis-Projects/Signature-Project` (PDFs de borderô) | só leitura de código, **não executado** |
| **[CEDENTE]** | este projeto `rpa_cadastro_cedente`: cadastro de cedente, sócios e representantes | validado em execução real (envio real nº 6 e teste final 9004, 2026-11-05) |

Versão do WBA observada: **24.7.1 (Build 6847)**. Aplicação Delphi de 32 bits (`Securitizacao.exe`) com navegador embutido na janela principal. Banco: SQL Server 2019 (base do WBA no ambiente de teste: `TESTESEC`).
Dicas gerais de outras automações Windows estão na seção 12.

Legenda: ✅ usado e validado · 🔎 mapeado mas nunca clicado por RPA · ⚠️ frágil / não validado.

---

## 1. Regras que valem para qualquer RPA no WBA

| Assunto | O que fazer | Origem |
|---|---|---|
| Janela principal | Achar pela **classe** `TFactMain`, nunca pelo título (o título traz versão e build e muda a cada atualização). Conectar por **handle**. | BLOQUEIO, SIGNATURE (⚠️ usa título fixo) |
| `auto_id` | Os numéricos mudam a cada execução (são handles). Só valem os `auto_id` de texto da barra principal (`BotaoCadClientes`…). | BLOQUEIO |
| Backends do pywinauto | Janela principal (HTML embutido) → **uia**. Janelas Delphi → **win32** (`TBitBtn`, `TEdit`, `TRadioButton`, `TDrawGrid`) e **uia** para abas (`TabItem`) e rádios do Crédito. Botões da `TToolBar` das janelas de coleção só aparecem no uia. | BLOQUEIO, CEDENTE |
| `Desktop().windows()` | Devolve `UIAWrapper`; para navegar use `Desktop(backend=...).window(handle=h)`. | BLOQUEIO |
| Janelas invisíveis | `TFactMain`/`TLoginVCForm` existem com `is_visible() == False`: filtre por visível. | BLOQUEIO |
| Esperas | Por condição (janela nova, valor escrito, grade mudou), não `sleep` fixo. | todos |
| DPI | `SetProcessDpiAwareness(2)` antes de tudo; coordenadas só batem assim (principalmente via RDP/AnyDesk). | BLOQUEIO |
| Mouse | Só onde não há alternativa (barra de ícones, grades). Prefira `invoke()`, `select()`, `click()` (BM_CLICK) ou teclado. | BLOQUEIO |
| Ordem dos controles | A árvore lista **de baixo para cima**: índice 0 = campo de baixo. Ordenar por `rectangle().top`. Login: usuário = o de cima, senha = o de baixo. Confirmado por BLOQUEIO e SIGNATURE. | BLOQUEIO, SIGNATURE |
| `TabItem.select()` (UIA) | Só **marca** a aba; o conteúdo pode **não trocar** (Empresas/Detalhes/Complemento mostraram a PFísica). Use **clique real** (`click_input`). | CEDENTE |
| `BM_CLICK` em botão | **Não muda o foco**: campos com máscara não confirmam o valor. Quando o valor depende de sair do campo, use clique físico. | CEDENTE |
| Campos de abas ocultas | O dump win32 traz controles de abas **ocultas** com valores de fichas anteriores. Nunca ler campo oculto como se fosse da ficha atual. | CEDENTE |
| Processo | `Securitizacao.exe` é 32 bits; Python de 64 bits funciona (o pywinauto só avisa). | BLOQUEIO |

---

## 2. Janelas (classe Delphi → o que é)

| Classe | Título | Papel | Origem |
|---|---|---|---|
| `TGerConexoes` | Gerenciador de Conexões | 1ª tela; botão **Conectar** | ✅ |
| `TLoginVCForm` | Identificação | Login: 2 campos + OK/Cancelar | ✅ |
| `TFactMain` | WBA Securitização - Versão… | Janela principal | ✅ |
| `TCadCliFor` | Cadastro: *nome* | Ficha do cadastro (uma só; o título troca ao abrir outro cadastro) | ✅ |
| `TPesquisaSigcadVCForm` | Pesquisa de Cadastro | Pesquisa por 8 critérios; cada abertura = janela nova | ✅ |
| `TInputQueryForm` | Alteração no cadastro / Registro Inserido / Alteração em Sócio/Procurador | Pop-up de **motivo** (campo de texto + OK/Cancel) | ✅ |
| `#32770` | Verifica se há atualização de arquivos | Pop-up de início → **Sim** | ✅ |
| `#32770` | Atualização Diária | Pop-up de início → **OK** | ✅ |
| `THintWindow` | texto do tooltip | Tooltip Delphi; única forma de identificar os ícones da barra da ficha | ✅ |
| `TPopupListbox` | (vazio) | Lista flutuante do combo *Tipo* da grade de baixo; janela nova, fecha se o mouse se mover | ✅ CEDENTE |
| `TCollectionCadFaturamentoContabilVCForm` › `TCadFaturamentoContabilSimpleForm` | Faturamento contábil | Grade + Novo/Editar/Apagar/Excel; formulário Data/Valor/Validade | ✅ CEDENTE |
| `TCollectionCadContratoSocialVCForm` › `TCadContratoSocialSimpleForm` | Contrato social | Data + Descrição (`TMemo`) | 🔎 escrita testada |
| `TDetalhes` | Informações comerciais | Abas Observações · Imobilizado · Bens · Veículos · Cartões · Referências · Sacados · Fornecedores (botão *Complemento Ficha Cadastral*) | 🔎 |
| `TfrmProgresso`, `TSelecaoData`, `TfrmSelectStr`, `TALDbConsultaFrm`, `TfacAboutBox` | — | Progresso, seleções, consulta, "Sobre". Ficam abertas se um fluxo falha. | 🔎 |
| (por título) | Desconto de títulos · Central de Impressão de Operações · Printing progress · Salvar Saída de Impressão como · Confirmar Salvar como | Fluxo de borderô/PDF | ⚠️ SIGNATURE |

---

## 3. Abrir, conectar e logar

1. Matar qualquer `Securitizacao.exe` aberto (psutil) e iniciar com `Application(backend="uia").start(cmd_line=<exe>, work_dir=<pasta>)`. ✅ BLOQUEIO, SIGNATURE, CEDENTE.
2. `TGerConexoes`: botão **Conectar** (`invoke()`, cai para clique).
3. `TLoginVCForm`: usuário (Edit de cima), senha (Edit de baixo), **OK**. Nunca logar o valor da senha.
4. Pop-ups de início (**Sim** / **OK**) aparecem **em qualquer ordem**: tratar em loop em toda espera. O SIGNATURE não trata e pode travar atrás deles.
5. Esperar `TFactMain` visível (até ~120 s) e repetir login se falhar (SIGNATURE tenta até 5× reiniciando).

---

## 4. Janela principal (`TFactMain`, uia)

Barra superior (`Image`, `auto_id` estável): `BotaoBordero` (Borderô), **`BotaoCadClientes` (Cadastro ✅)**, `BotaoRegresso` (Recompra), `BotaoLancamentos`, `BotaoCCLancamentos`, `BotaoTrocaUsuario`, `BotaoCalculadora`, `BotaoCalendario`, `BotaoHaDeNovo`. Menu: Mais acessados, Arquivo, Consolidado, Contas, Simples Cobrança, Desconto, C/Corrente, Operação, Gerência, Ferramentas, Ajuda (submenus não mapeados).

---

## 5. Ficha do cadastro (`TCadCliFor`)

### 5.1 Barra de ícones (`TWBADBNavigator`)
- **Sem controles filhos.** Só se identifica pelo **tooltip** (`THintWindow`): exige janela ativa e mouse parado; varrer da direita para a esquerda na altura `top + 14`.
- Distância da **borda direita** do navegador (escala de referência: altura do navegador 57 px): **Excluir 6 · Alterar/Cancelar 36 · Novo/Salvar 56 · Localizar 86**. As distâncias são **proporcionais** (`altura_atual / 57`); só testado em 2 monitores.
- Dois **modos** na mesma posição: **navegação** (Alterar, Novo) e **edição** (Cancelar, Salvar). Depois de *Novo* já aparece Salvar. Com a ficha em inclusão (tela zerada) **não existe Novo**: Cancelar (descarta o digitado).
- Regra: conferir o tooltip antes de clicar; se o modo for o outro, adaptar em vez de varrer a barra inteira (houve travamento de ~1100 px de varredura).
- Os ~15 ícones da esquerda são módulos (Documentos, Análise PLD, Ficha de crédito, Impressões…), não usados.

### 5.2 Abas principais (uia `TabItem`, clique real)
Identificação, PFísica (vira **PJurídica** no cedente), Detalhes, Empresas (vira **Profissionais** no cedente), Crédito, Contrato, Decs. R, Alterações, Consulta, Negociações, Histórico, Contabilidade, Complemento, Borderôs, Anotações. "Complemento" aparece duas vezes (aba principal e sub-aba do Crédito). ⚠️ A aba **Detalhes** do sócio derrubou o WBA uma vez (não confirmado).

### 5.3 Rodapé (win32 `TBitBtn`)
Complemento Ficha Cadastral, iWBA, iWBA Recebíveis, Formalizações, **Fechar** ✅.

### 5.4 Código e título
O **Código** só é gerado ao **salvar**; o título passa a mostrar o nome; o CNPJ/CPF é formatado sozinho **ao sair do campo seguinte** (o RPA trata mudança só de máscara como "nada mudou").

---

## 6. Identificação (24 controles, por posição)

CNPJ/CPF · Código · Cód. Rápido · **Tipo Cadastro** (combo fechado: Cedente, Clientes, Colaborador, Conjuge, Debenturista, Depositário, Empresa, **Fiador**, Fornecedor, Impostos, Inativo, Represent., Sacado, **Sócio**, Testemunha) · Subtipo · Nome · **Logradouro** (tipo: `AV`, `RUA`…) · Endereço · Número · Complemento · **CEP** · Bairro · Cidade (texto) · Estado (combo UF) · Cód. SIAFI · Cód. IBGE · Fone · Ramal · Fax · Celular · E-mail · Home page · Senha · Região.

Regras aprendidas:
- **CEP primeiro.** O WBA preenche logradouro, endereço, bairro, cidade, UF e IBGE **sozinho, mas só quando o foco sai do campo CEP**, alguns segundos depois. Fluxo: escrever o CEP logo depois do nome → **TAB** → esperar o autopreenchimento aparecer (até ~8 s) e ficar quieto ~1,5 s → só então escrever o endereço da API **por cima**. (Custa ~8 s por pessoa; ainda não otimizado.)
- Fone com pontuação caía no Ramal: digitar **só dígitos** (+ `{HOME}`) e limpar Ramal/Fax/Celular.
- Nenhum campo é obrigatório; o RPA só escreve o que a API manda.
- Campo seguinte ao CEP perdia caracteres: esperar ~0,4 s depois de focar, reler e reescrever se não conferir, conferir se **outro** campo mudou.
- Siafi e IBGE: usar tabela própria (BA). A coluna "IBGE" do arquivo/PDF do Siafi está errada (Salvador 2928000; correto 2927408). Exemplo conferido: Feira de Santana = Siafi `3515` / IBGE `2910800`.

## 7. PJurídica (cedente)

Nome Fantasia · Inscrição Estadual · Inscrição Municipal · Data da Fundação · Registro Junta Comercial · Ramo de Atividade · Grupo Econômico · Nº de Filiais · CNAE; 4 botões *Cadastro* (faturamento contábil, alteração no contrato social, balanço patrimonial, total endividamento); 9 checkboxes tri-state (Isento de Retenções, Micro Empresa/EPP, Órgão Público, Optante pelo Simples, Retenção de ISS, Isenção de IOF, Isenção de IOF Adicional, Possui e-CNPJ?, CNPJ é Ativo?).

- Ao salvar, o WBA abre **um pop-up de motivo por campo alterado** ("Nome Fantasia foi alterado. Qual motivo?"). Responder em sequência, **sem limite**, até não aparecer mais.
- Faturamento: no cadastro recém-criado a grade vem **vazia** e *Editar* fica desabilitado → usar **Novo**. Data (`TDateTimePicker`): digitar dígitos com `{RIGHT}` entre os segmentos (ele não avança sozinho); valor (`TJvValidateEdit`): digitar por cima e `TAB`; **OK com clique físico**. A *Validade* é ajustada pelo próprio WBA (não mexer).
- Pendente: regra de `regime_tributario` → checkboxes; balanço; endividamento; contrato social (OK gravando).

## 8. PFísica › Geral (sócio e representante)

R.G. · Órgão Emissor (**com UF**: `SSP/BA`) · Data de Expedição · Sexo (`M`/`F`) · Estado Civil (Solteiro, Casado, Divorciado, Viúvo, Separado) · Profissão (combo fechado de **147** opções; sem equivalente → `Outros`) · Nacionalidade (gentílico) · Naturalidade (**`CIDADE/UF`**) · Aniversário · Pai · Mãe · **Cônjuge** · Regime (só com estado civil Casado etc.) · Nº de Dependentes · "Possui e-CPF?". Combos fechados: `select(texto)`. Data com máscara: dígitos `ddmmaaaa`.

- **Cônjuge** aceita só dígitos = **código de 5 dígitos de outro cadastro**; ao lado, um rótulo mostra o nome do cadastro (serve para validar) e uma caixinha abre a pesquisa. No banco o tipo é `Conjuge`. ⚠️ Não implementado: hoje só o estado civil é escrito.
- PFísica › Complemento: Renda, Outras Rendas, 4 checkboxes (PPE, Parente de PPE, Isenções), Inscrição Estadual. ⚠️ A API não manda.
- Sócio › Empresas: duas grades só de leitura (espelho das do cedente).

---

## 9. Pesquisa de Cadastro (`TPesquisaSigcadVCForm`) ✅

- Abas (uia `TabItem`, **clique real**): `1-CNPJ/CPF`, `2-Razão Social/Fantasia/Nome`, `3-Código Rápido`, `4-Contato`, `5-Fone`, `6-E-mail`, `7-Endereço/Cidade`, `8-Vários` (o `select()` da 8 falhou). **Não existe aba só de Código.**
- Controles win32: `TTabControl`, `TRadioButton` *Iniciando com* / *Contendo* (Contendo desabilitado na aba CNPJ), `TEdit` único, `TBitBtn` *Localizar* (clique físico, desabilitado até digitar), `TDrawGrid` (**sem texto legível**; esperar o resultado comparando o hash da imagem), `OK` / `Cancelar`.
- Funciona pesquisar por 8 dígitos do CNPJ ou pelo nome. *OK* **troca a ficha na mesma janela** `TCadCliFor`.
- Abrir a lupa: **Localizar** na barra de ícones (tooltip). Alternativa sem lupa: ver seção 11 (banco).
- Caso "não encontrado" via lupa nunca foi mapeado a fundo; hoje a existência é decidida pelo banco.

## 10. Aba Profissionais do cedente (vínculo de sócios e fiadores) ✅

Uma aba (*Geral*) com **duas grades `TDBGrid`** (win32, sem texto de célula; só o editor da célula é legível):

| Grade | Colunas | Tabela no banco |
|---|---|---|
| **De cima:** Sócios e Procuradores | Código · Participação · Gr. Assinatura · Procurador · Nome · CPF | `cadsocio` |
| **De baixo:** Fiadores, Testemunhas, Funcionários, etc. | Código · Tipo · Nome · Ramal/Fone · Cargo · Tempo de Serviço | `cadprof` (mostra **todos os tipos**) |

Geometria (escala = altura atual do navegador / referência): as duas grades têm mesma esquerda e largura; a Código da 1ª linha fica em `(80, 44) × escala` a partir do canto da grade, nas duas.

### Controles
- `TDBGrid` (sem texto) · `TDBGridInplaceEdit` (editor da célula, é o único legível) · `TPopupListbox` (lista do combo Tipo).

### Regras da grade (valem para as duas)
1. O editor da célula abre no clique **só se a célula já é a atual**; em **outra linha** abre no **2º clique**.
2. A **seta para baixo** cria linha nova **só com o editor ativo na última linha** e **só se a linha anterior está salva e completa**. Receita: **clicar no Código da ÚLTIMA linha + UMA seta** (descer N vezes não cria).
3. Em linha **nova**, o editor **só aparece ao digitar**: "editor ausente" ali é normal. Distinguir `None` (sem editor) de `''` (vazio).
4. **Um Alterar/Salvar por pessoa.**
5. O pop-up *Registro Inserido* vem **ao salvar**. Qualquer outro (ex.: *Alteração em Sócio/Procurador* = sobrescreveu uma linha existente) deve ser **cancelado**, nunca confirmado.
6. Remover/editar linha **não mapeado** (Ctrl+Delete não funciona; hipótese: mudar o Tipo do cadastro).
7. Não confiar na leitura da grade: confirmar **no banco** depois de salvar.

### Sócio (grade de cima)
clique no Código da última linha › (seta para baixo se já há linha) › digitar o **código** do sócio › conferir o digitado **antes** do TAB (depois do TAB o editor some) › TAB › Salvar › responder *Registro Inserido*. Nome e CPF aparecem sozinhos depois de salvar; Participação=0 e Gr. Assinatura=1 são padrão do WBA.

### Fiador (grade de baixo)
clique no Código › digitar código › **TAB** (foco vai para *Tipo*, sem editor) › **clique no Tipo** (vira `TDBGridInplaceEdit` de ~87 px; posição = direita do Código + `66 × escala`) › **clique na seta** (`coords=(largura-8, altura//2)`, abre `TPopupListbox`) › `F` › `Enter` › Salvar › *Registro Inserido*. Itens da lista: Depositário, Diretor, Diretor C/C, **Fiador**, Funcionário, Gerente C/C, Testemunha.

> **Regra do popup:** depois de abrir a lista, nada pode mover o mouse (`diagnostico`, `modo_barra`, inspeção) antes de escolher; ela fecha. Tirar print só com `ImageGrab`.

### Regra de negócio da equipe
Todo sócio também é **Fiador** (grade de baixo). **Representante** (vem `Represent.` da API) é cadastrado no WBA como **Fiador**, inclusive no *Tipo Cadastro* da Identificação (⚠️ decisão de 2026-11-05, **ainda não rodada no WBA real**).

---

## 11. Banco do WBA (SQL Server, somente leitura) ✅ CEDENTE

Conexão por `pyodbc`; credenciais em `.env` (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD`, `DB_DRIVER`), **nunca** em código, log ou documentação. ⚠️ `DB_NAME` tem de ser a **mesma base a que o WBA conecta** (no teste: `TESTESEC`; a `SECURITIZACAO` é outra). Senha com caracteres especiais vai entre chaves na connection string. Hoje o usuário é administrador: pedir um com `SELECT` apenas.

| Tabela | Colunas úteis | Uso |
|---|---|---|
| `sigcad` (117 colunas) | `ID`, `CODIGO` (= código do WBA), `NOME`, `TIPO`, `CGC` (**com máscara**) | existência do cadastro, código |
| `cadsocio` | `codigopj` (cedente), `codigopf` (sócio), participação, grupo, procurador… | grade de cima |
| `cadprof` | `codigopj`, `tipo`, `codigopf`, tempo de serviço, ramal, cargo, departamento | grade de baixo |

Consultas:
- Existe? `SELECT ID, CODIGO, NOME, TIPO, CGC FROM sigcad WHERE CGC IN (<com máscara>, <sem máscara>) AND TIPO IN ('Cedente','Sócio','Fiador','Represent.','Conjuge')` (**`Inativo` ignorado de propósito**; ~2 linhas com grafia `SOCIO`/`SOCIA` não são pegas).
- Código de um documento (qualquer tipo): `SELECT CODIGO FROM sigcad WHERE CGC IN (…)`. Mudar o Tipo altera a mesma linha, não cria outra.
- Linha genérica com CGC `00.000.000/0000-00` (código 3): rejeitada na validação.
- O que o banco permite: decidir **antes de abrir o WBA** se o cedente já existe, conferir que o código da tela = código do banco, reaproveitar o código de CPF existente sem abrir a ficha, e **conferir cada vínculo** depois de salvar.

---

## 12. Fluxo de cadastro validado (resumo ponta a ponta)

1. Validar o envio (CNPJ/CPF com dígitos verificadores, nomes, município da BA com Siafi/IBGE) e consultar o banco (existente e não nosso → `fail` sem abrir o WBA).
2. Abrir o WBA do zero (login automático, pop-ups de início).
3. **Cedente:** Novo › Identificação (CEP primeiro) › Salvar › conferir código no banco › PJurídica (todos os pop-ups de motivo) › Faturamento (Novo se vazio).
4. **Cada pessoa física:** CPF já existe → usar o código do banco, sem alterar a ficha; senão Novo › Identificação › PFísica › Geral.
5. **Vínculos** na aba Profissionais do cedente (um Salvar por pessoa), conferidos em `cadsocio` / `cadprof`.
6. `POST /complete` ou `POST /fail` (mensagem em português simples, ≤ 500 caracteres).
7. **Falha → fechar o WBA**; a próxima tentativa abre do zero e retoma pelos **checkpoints** (`pendente → em_andamento → salvo → validado | falhou`; o checkpoint é gravado **antes** de clicar em Salvar).

Resultado: envio real nº 6 (cedente + 2 sócios + 1 representante, 14/14 blocos) e teste final 9004 (cedente + sócio + representante, ~6,5 min, uma execução).

---

## 13. Pop-ups e cuidados

- **Motivo** (`TInputQueryForm`): o UIA **não expõe o texto da pergunta**; o campo é achado via win32. Títulos conhecidos: *Alteração no cadastro* (um por campo alterado), *Registro Inserido*, *Alteração em Sócio/Procurador* (rejeitar). Texto padrão do motivo configurável (`CADASTRO AUTOMATICO RPA - ENVIO {id}`).
- Falha no meio deixa **janelas modais abertas** (Pesquisa, Seleção de Dados, Consulta) que desabilitam a principal e quebram o passo seguinte sem mostrar a causa. Duas abordagens: **fechar o que reconheço** (BLOQUEIO; nunca responder o pop-up de motivo nessa rotina) ou **matar o processo e reabrir** (SIGNATURE, e a regra adotada em CEDENTE: mais simples e confiável).
- O WBA recarrega o cadastro depois do OK e **descarta edições feitas antes**.
- Um teste que "para no primeiro erro" não impede o operador de salvar um cadastro incompleto: sempre reconferir tudo depois de salvar.

---

## 14. Aba Crédito › Restrições (bloquear cedente) ✅ BLOQUEIO

Aba **Crédito** (uia `TabItem`) › sub-aba **Restrições**. Sub-abas do Crédito: Restrições, Borderô, Bord. C. Própria, Contas - Fatores, Contas - Reemb., Limites, Complemento, Gerente, SC CR, Antecipação, Cobrança, Controle, Limite Sacado, Limite Grupo Empresarial, Outros, Custódia. Campos do topo: Limite Crédito, Vcto do Limite, Classificação, Limite NP, Validade NP, Risco BACEN, Calculado.

Restrições tem 3 grupos empilhados (*gerais*, *como Cedente*, *como sacado*), cada um com rádios **Liberado / Em Alerta / Bloqueado**, data "até" (`  /  /    `) e observação (`Edit` largo abaixo). Ordenar os 3 `RadioButton` "Bloqueado" por `top`: 0 = gerais, **1 = cedente**, 2 = sacado. Ao fechar a ficha alterada aparece o pop-up de motivo ("Restrição/Bloqueio como Cedente foi alterado. Qual o motivo?"). Rodapé **Fechar** (`TBitBtn`).

---

## 15. Fluxo de borderô e impressão de PDFs ⚠️ SIGNATURE (só leitura de código)

Principal › **Borderô** (`Image` título "Borderô"; melhor `auto_id="BotaoBordero"`) › janela *Desconto de títulos* (campo do nº do borderô = `Edit` `found_index=8`, índice frágil; digitar + `{ENTER}`) › ícone de **imprimir** (busca por imagem `print.png` com pyautogui: frágil a DPI/tema; melhor achar por hint) › *Central de Impressão de Operações* (marcar `ListItem` **Carta Cessão**, **Declaração de Recebimento - Resumida**, **duplicata novo**, **Pendências Liquidadas Contas Pagas e Deduzidas - CP**, clicando na caixinha `click_input(coords=(8,7))`) › **Imprimir selecionados** › diálogo *Salvar Saída de Impressão como* (filho de *Printing progress*): *Locais Anteriores*, digitar caminho + Enter, **Abrir**, digitar nome (`carta_de_cessao_<nº>`, `declaracao_de-recebimento_resumida_<nº>`, `duplicata_<nº>`, `pendencias_liquidadas_<nº>`), **Salvar**, e **Sim** em *Confirmar Salvar como* › **Fechar** (Central) › **Fechar** (Desconto).
Confirmação do PDF por **dois sinais**: arquivo no disco com tamanho estável (2 leituras, 1 s) **e** botão Salvar habilitado/diálogo fechado, em laço de até 120 s. O serviço roda o WBA numa **thread** com prazo e mata o processo se estourar.
Pontos frágeis: título fixo da versão, `found_index`, busca por imagem, `sleep` fixo, não trata pop-ups de início.

---

## 16. Dicas gerais de outras automações Windows (reaproveitáveis)

**Antes de escrever:** mapear a tela primeiro (`print_control_identifiers()`); testar **win32 e uia**; em campos sem rótulo, **numerar todos de uma vez** (escrever o índice dentro de cada campo, tirar print); desconfiar de **títulos de janela repetidos** (conectar por handle/janela do topo).
**Padrões contra bugs graves:** nunca tratar "qualquer exceção" como sucesso (separar *não consegui confirmar* de *confirmei que deu certo*); **dois sinais** para confirmar ação assíncrona; **teclado em vez de coordenada**; cuidado com **modal esquecida**; **DPI awareness** no início.
**Produção:** gravar **transcrição completa** de cada execução; projetar **retomada** cedo (estado + fonte da verdade externa: banco/arquivo); **isolar falhas** por unidade de trabalho; tratar "app travou" como categoria própria (matar + reabrir + reconectar), sabendo qual fase é destrutiva de interromper; usar o Agendador do Windows (`RestartCount`/`RestartInterval`, `MultipleInstances=Queue`).
**Disciplina:** diagnosticar por **evidência** (log, screenshot, erro exato); documentar incidentes num arquivo vivo; **configuração em vez de código** para cada item novo; ferramentas de diagnóstico isoladas cedo.

---

## 17. O que ainda NÃO está mapeado / validado

- ⚠️ **Representante com Tipo Cadastro = Fiador** (mudança de 2026-11-05, nunca rodada no WBA).
- ⚠️ **CNPJ alfanumérico** (`CR.SK7.JXU/0001-15` é válido pelo algoritmo novo da Receita): testar se o campo do WBA aceita letras; hoje bloqueado.
- **Cônjuge** (código de outro cadastro) e **regime de bens**; Nº de dependentes; e-CPF; PFísica › Complemento.
- Editar/remover linha das grades (Participação, Gr. Assinatura, Procurador).
- Checkboxes da PJurídica por `regime_tributario`; balanço; total de endividamento; dados bancários (qual aba); contrato social gravando.
- Acentos e minúsculas; confirmação ao Cancelar uma ficha com dados; escala de monitor/DPI da barra e da grade; menus da barra principal; abas Detalhes/Empresas do sócio.
- Travamento **sem erro** (watchdog), usuário de banco **somente leitura**, checkpoints **locais a cada máquina**, agendamento em produção.
- Por que `modo_barra` leu o modo errado 3× (causa não achada; o RPA se recupera).

---

## 18. Onde está cada coisa (este projeto)

| Assunto | Arquivo |
|---|---|
| Primitivas de UI do WBA (campos, barra, grades, pop-ups) | `src/infrastructure/rpa/wba_ui.py` |
| Filtro de janelas relevantes | `src/infrastructure/rpa/janelas_util.py` |
| Abrir/logar o WBA | `src/infrastructure/rpa/sessao.py` |
| Gateway (porta do domínio → UI) | `src/infrastructure/rpa/gateway.py` |
| Consulta ao banco do WBA | `src/infrastructure/persistence/wba_sql_consulta.py` |
| Orquestração (blocos, checkpoints, retomada) | `src/application/use_cases/cadastrar_envio.py`, `processar_fila.py` |
| Mensagem de falha para o portal | `src/application/use_cases/mensagem_falha.py` |
| Conversões API → WBA | `src/application/mapping/conversores.py`, `formularios.py` |
| Notebook de mapeamento por células | `notebooks/rpa_cedente.ipynb` |
| Dumps e prints de cada tela | `docs/mapeamento/` |
| Diário de achados e pendências | `CHECKLIST.md`, `docs/MAPA_WBA.md`, `docs/PENDENCIAS_API.md` |
