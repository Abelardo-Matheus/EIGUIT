Você é o desenvolvedor principal do Guitar Studio. Nossa missão agora é criar uma nova aba no aplicativo: O Criador de Tablaturas. O usuário poderá escrever tablaturas do zero, usar técnicas (bend, slide) e dar "Play" ouvindo um sintetizador básico.

Por favor, implemente o sistema seguindo rigorosamente a arquitetura modular abaixo:

## TAREFA 1: O Motor de Áudio (Sintetizador Numpy)
1. Crie um arquivo `@modulo_synth.py`.
2. Use `pygame.sndarray` e `numpy` para criar uma classe `SintetizadorTablatura`.
3. Essa classe deve ter uma função que recebe uma "Corda" (1 a 6) e uma "Casa" (0 a 24). Ela deve calcular a frequência em Hertz (baseado na afinação padrão EADGBE) e gerar um som curto.
4. Adicione suporte básico para interpretar técnicas: se a nota tiver 'b' (bend), a frequência deve subir meio tom durante a reprodução; se tiver '/' (slide), a frequência desliza.

## TAREFA 2: Estrutura de Dados e Lógica
1. No arquivo central do estado, crie a estrutura de dados da tablatura. Ela deve ser uma lista de "colunas" (tempos), onde cada coluna tem 6 espaços (um para cada corda).
2. O valor de cada espaço pode ser vazio (`-`), um número (casa), ou número + técnica (ex: `12b`, `5/7`, `7h9`).
3. Crie a lógica do botão "Play": um loop não-bloqueante que avança coluna por coluna baseado em um BPM (ex: 120 batidas por minuto) e dispara o `SintetizadorTablatura`.

## TAREFA 3: Interface Gráfica (Grid e Scroll) no Pygame
1. Crie um arquivo `@renderizador_tablatura.py` (ou adicione ao renderizador existente).
2. Desenhe 6 linhas horizontais ocupando a maior parte da tela.
3. Desenhe as colunas verticais indicando a divisão do tempo.
4. Implemente controle de Scroll (usando a roda do mouse ou barra inferior) para mover a grade para a esquerda/direita.
5. Implemente um "Cursor" de edição: ao clicar em um cruzamento (Corda x Tempo), o bloco fica ativo. Se o usuário digitar um número ou letra (b, s, h, p), isso é gravado na estrutura de dados.

## TAREFA 4: Salvar e Carregar (Banco de Dados)
1. Conecte essa aba ao nosso `@gerenciador_db.py` (ou `gerenciador_remoto_db.py`).
2. Crie campos de texto no topo da tela para: "Nome da Música" e "BPM".
3. Adicione um botão "Salvar no Perfil". Ele deve pegar a estrutura de dados da tablatura, converter para JSON, e dar um INSERT/UPDATE na tabela `projetos`, vinculando ao ID do usuário atual.

Entregue os códigos focando em manter a performance do Pygame (renderize apenas as colunas que estão visíveis na tela no momento do scroll).