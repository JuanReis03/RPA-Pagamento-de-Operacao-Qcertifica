# Roteiro: RPA Pagamento de Operação (Teams → WBA FIDC → Portal FIDC → QCertifica)

Registrado em 2026-11-11 a partir da descrição do processo manual. Nada aqui foi mapeado nem executado ainda.

## Regra central

- A operação fica **Concluída** no WBA depois de aprovada; nesse momento ela vai sozinha para o QCertifica e é postada no grupo do Teams **Pagamento Operação**, pronta para pagar.
- **Só se assina uma operação se ela apareceu no grupo** (ou seja, está Concluída no WBA).
- Toda operação Concluída no WBA tem de ter uma operação correspondente no QCertifica para assinar.

## Passo a passo (processo manual de hoje)

| # | Sistema | Ação | Dado que sai |
|---|---|---|---|
| 1 | Teams (chat *Pagamento Operação*, NAC) | Ler a mensagem `OP xxxxx yy` (`xxxxx` = nº do borderô, só dígitos; `yy` = sigla/nome da empresa) | nº do borderô, sigla do cedente |
| 2 | WBA Securitização **FIDC** | Clicar em **Estados** › **Fluxo**; achar a OP do borderô `xxxxx` | linha do borderô |
| 3 | WBA | Clicar no borderô → abre a janela **Desconto de títulos** (abre na aba *Títulos*) › clicar na aba **Pagamento** | valor, banco, agência, conta no WBA |
| 4 | Portal FIDC (Liquidação: `portal/financeiro/aprovarLiquidação`) | Pesquisar pelo nome do cedente e abrir | valor, banco, agência **sem dígito**, conta corrente |
| 5 | Comparação | Conferir se os 4 dados do portal batem com os da aba Pagamento do WBA | bate / não bate |
| 6 | QCertifica | Achar a operação (borderô + cedente). Para saber se é **NAC** ou **FIDC**, entrar nas contas do QCertifica (o RPA precisa entrar nas duas; a pessoa sabe "de cabeça") | operação a assinar |
| 7 | QCertifica | Assinar (somente se passou em 1 e 5) | assinatura feita |

## Exemplo de mensagem no Teams

```
OP 54826 CITYGUSA
LIBERADA PELO FIDC

OP. 54825 - OLIVEIRA HORA
LIBERADA PELO FIDC

OP 54824 - POLLUX
LIBERADA PELO FIDC

OP 54827 PREMOL
LIBERADA PELO FIDC

OP 54833 FEIRA AMERICAN
ITAU X ITAU

OP 54831 GANDULAR
LIBERADA PELO FIDC

OP 54834 GANDULAR
ITAÚ X BRADESCO

OP. 54829 - LACGLORIA
LIBERADA PELO FIDC
```

A 1ª linha segue sempre o formato `OP[.] número [-] sigla`. A 2ª linha varia: `LIBERADA PELO FIDC`, `100% RECOMPRA` ou `BANCO X BANCO`, em que o **1º é o banco de origem e o 2º o de destino** (ex.: `ITAÚ X SANTANDER`: sai do Itaú, vai para o Santander). Toda mensagem de OP traz o **PDF da operação** anexado.

## Acessos

| Sistema | Situação |
|---|---|
| QCertifica (com ambiente de homologação) | OK |
| Teams da NAC (chat Pagamento Operação) | OK |
| WBA Securitização FIDC | pendente |
| Portal FIDC (aprovar liquidação) | pendente |

Credenciais ficam só no `.env` (fora do git), nunca em código, log ou documentação.

## Perguntas em aberto

Ver `CHECKLIST.md` › Pendências.
