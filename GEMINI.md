# Contexto do Projeto: Guitar Studio IA
Você é o assistente de desenvolvimento sênior deste projeto. Este é um software educacional focado no ensino e prática de guitarra e baixo, desenvolvido em Python utilizando a biblioteca Pygame para renderização visual e manipulação de áudio.

## Regras de Segurança (Arquivos a Ignorar)
Para economizar tokens e evitar travamentos, **NUNCA** leia, vasculhe ou referencie o conteúdo das seguintes pastas e arquivos, a menos que eu peça explicitamente:
- `venv_novo/` (Ambiente virtual)
- `.venv/` ou `__pycache__/`
- Arquivos `.exe`, `.dll`, `.ogg`, `.wav`, `.png`
- Pastas `build/` e `dist/`

## Arquitetura do Sistema (Mapeamento de Pastas)
O projeto segue uma estrutura modular baseada em estados e gerenciadores. Se eu pedir para você criar ou alterar algo, consulte a arquitetura abaixo para saber onde o código deve ficar:

### 1. Raiz do Projeto (Core)
- `main.py`: Ponto de entrada, loop principal do Pygame e inicialização.
- `config_eiguit.json`: Gerenciamento de preferências do usuário (cores, opacidade).

### 2. /Core/ (Gestão e Lógica Central)
- `estado_app.py`: Classe central que guarda todas as variáveis globais, draggers e estado atual da interface.
- `config.py`: Persistência de preferências do usuário / Flexbox UI config.
- `constantes_ui.py`: Dicionários estáticos (afinações, códigos de cores, medidas).
- `controlador_eventos.py`: Cérebro de interações. Lê teclado e mouse e despacha para os módulos corretos.

### 3. /Interface/ (Renderização e UI)
- `renderizador_ui.py`: Cérebro visual. Chama os métodos de desenho de todos os outros painéis.
- `gerenciador_interface.py` e `ui_componentes.py`: Lógica de botões, sliders e elementos base da UI.
- `fabrica_escalas.py`: Construtor dinâmico dos blocos do braço da guitarra.

### 4. /Assets/ e /Audios/
- `Imagens/`: Recursos visuais estáticos.
- `Audios/`: Banco de timbres sintetizados e gravações do projeto.

### 5. /Modulos/ (Motor e Lógica)
Contém os sistemas independentes que rodam por trás da UI:
- **Áudio/Hardware:** `modulo_gravador.py`, `modulo_processamento.py`, `modulo_metronomo.py`, `gerenciador_ritmo.py`, `detector_palhetadas.py`.
- **Integração:** `modulo_songsterr.py` (Busca e metadados do Songsterr).
- **Teoria Musical:** `escalas.py`, `modulo_campo_harmonico.py`, `modulos_acordes.py`, `modulos_escala_maior.py`, `modulos_escala_menor.py`, `modulos_penta.py`, `modulos_teoria_avancada.py`.
- **UI Flutuante:** `modulo_menu_superior.py`, `modulo_menu_contexto.py`, `modulo_perfil.py`.
- **Módulo de Estudos Base:** `modulos_estudos.py` (Roteador da tela cheia de estudos).

### 3. /Estudos/ (Telas de Estudo Prático)
Submódulos de treino que assumem a tela inteira quando ativados:
- `estudo_notas.py`: Treino de encontrar notas no braço.
- `estudo_escalas.py`: Treino de desenhar e adivinhar shapes (Maior, Menor, Pentas).

### 4. /Jogos/ (Gamificação)
Experiências interativas de aprendizado:
- `Jogos_interativos.py`: Gerenciador principal das abas de jogo.
- `acerte_a_nota.py`, `jogo2.py`, `jogo3.py`, `jogo4.py`: Mini-games específicos.

### 5. /DragDrop/ (Mecânicas da Interface)
- `elemento_arrastavel.py`: Classe base para os painéis que se movem no Workspace (braço da guitarra, campo harmônico, etc).

## Diretrizes de Resposta
1. Ao me entregar código, mande apenas a função ou a classe alterada, a menos que eu peça o arquivo inteiro.
2. Mantenha os cabeçalhos de Copyright intactos.
3. Considere que o projeto foca muito em desempenho, pois lida com áudio em tempo real e Pygame.