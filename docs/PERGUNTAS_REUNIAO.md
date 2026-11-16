# Perguntas em aberto — RPA Pagamento de Operação

Atualizado em 2026-11-11.

## Mensagem do Teams
1. Quais são **todas as variações da 2ª linha** da mensagem e o que cada uma significa? Exemplos já vistos: "LIBERADA PELO FIDC", "ITAU X ITAU", "ITAÚ X BRADESCO".
2. Para cada variação: o RPA **processa** a OP ou **ignora**? O que significa "ITAU X BRADESCO" (banco de saída × banco do cedente?) e isso muda alguma conferência?
3. **Resposta do RPA no chat:** reagir com emoji ou responder "OK"? Qual emoji? Reage só quando os dados batem ou sempre? Se o responsável já reagiu, o RPA deve pular a OP?

3a. Quando alguém escreve **"Favor considerar o borderô correto este:"** e posta uma nova OP, a OP anterior deve ser **descartada** pelo RPA? Como saber qual foi substituída?
3b. O que significa **"100% RECOMPRA"** na 2ª linha? O RPA deve processar essa OP?

3c. O RPA vai pular OP com ✅ (já tratada). O que significa o 🟨 e as outras reações usadas no chat?
3d. O RPA precisa ler o **PDF anexado** à OP (para conferir algum dado), ou basta a mensagem? Se precisar, o app do Teams vai precisar de mais uma permissão.

## Divergência
4. Quando os dados do Portal FIDC **não batem** com o WBA, o que o RPA faz? (avisar no chat, avisar uma pessoa, só registrar e não assinar)

## Portal FIDC
5. **Acesso:** endereço, usuário, senha e ambiente de teste.
6. Um mesmo cedente pode ter **várias liquidações abertas** ao mesmo tempo? Ex.: GANDULAR teve as OPs 54831 e 54834 no mesmo dia. Como saber qual é a de cada OP? Usar o **valor** como critério resolve?

## WBA Securitização FIDC
7. **Acesso:** onde fica o executável, usuário e senha, ambiente de teste.
8. É a **mesma versão** do WBA usado nos outros robôs (24.7.1)? Tem **banco de dados** com acesso de leitura?

## QCertifica
9. Como a operação aparece no QCertifica: pelo **número da OP**, pelo **nome do cedente** ou pelos dois?
10. Como o RPA sabe em **qual conta/empresa** a operação está para assinar (NAC ou outra)? Precisa entrar em mais de uma?

## Operação do robô
11. Em qual **máquina** o RPA vai rodar?
12. Como o RPA é **acionado**: uma pessoa dispara quando vê a mensagem, ou ele vigia o chat sozinho? Quantas OPs aparecem por dia, em média?
