<div align="center">
  <img src="https://github.com/user-attachments/assets/a8fadb13-ea2e-44e0-aead-4abb4989a3c6" width="250" style="border-radius: 50%; opacity: 0.3;" alt="Guitar Studio IA Logo">

  <h1>🎸 EIGUIT </h1>
  <p><i>Estúdio virtual de guitarra e baixo: braço interativo, campo harmônico, editor de tablatura, estúdio de estudos guiados, mini-jogos e processamento de áudio com IA</i></p>
  <p><i>Virtual guitar/bass studio: interactive fretboard, harmonic field, tablature editor, guided study tracks, mini-games and AI-assisted audio processing</i></p>

  <p>
    <img src="docs/screenshots/braco_guitarra.png" width="410" alt="Braço interativo com escala e campo harmônico">
    <img src="docs/screenshots/editor_tablatura.png" width="410" alt="Editor de tablatura">
  </p>
  <p>
    <img src="docs/screenshots/estudos.png" width="410" alt="Painel de Estudos guiados">
    <img src="docs/screenshots/jogo_acerte_a_nota.png" width="410" alt="Mini-jogo Acerte a Nota">
  </p>

  <br>

  <p>
    <img src="https://img.shields.io/badge/Status-Beta-orange?style=for-the-badge" alt="Version Beta">
    <img src="https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python Version">
    <img src="https://img.shields.io/badge/Engine-Pygame-6c5ce7?style=for-the-badge" alt="Pygame">
    <img src="https://img.shields.io/badge/Platform-Windows_|_Linux_|_macOS-lightgrey?style=for-the-badge" alt="Platforms">
    <img src="https://img.shields.io/badge/License-Copyright_Reserved-red?style=for-the-badge" alt="License">
  </p>
</div>

---

## 🇧🇷 Português

### ⚠️ Status do Projeto: Beta

O EIGUIT deixou de ser "só um braço de guitarra": depois de uma refatoração grande, o projeto virou um **estúdio completo**, organizado em camadas (`core/`, `ui/`, `audio/`, `Jogos/`, `DragDrop/`, `BD/`, `config/`) com um sistema de design próprio. A matemática musical, a renderização do braço, o DSP de áudio e o editor de tablatura já estão operacionais; a interface e os módulos mais novos (Estúdio de Estudos, editor de tablatura, busca de músicas/timbre, perfis na nuvem) ainda recebem ajustes visuais e de estabilidade com frequência.

**Procuramos colaboradores!**
* **Design (UI/UX):** refino visual, responsividade e microinterações do sistema de design próprio (`config/design_system.py`).
* **Desenvolvimento (Python/Pygame):** performance de renderização, novos módulos de `core/modulos/` e integração com o serviço de transcrição por IA.
* **Teoria musical:** novas trilhas em `Estudos/`, escalas exóticas, tétrades e progressões.
* **QA/Testes:** reportar bugs, sugerir melhorias e ampliar as suítes de validação em `_validacao/` (rodam sem janela e sem placa de som).

### 📝 Sobre o Projeto

O **Guitar Studio IA (EIGUIT)** é uma ferramenta interativa para guitarristas, baixistas, estudantes de teoria musical e produtores, escrita inteiramente em Python com Pygame. O núcleo é um loop de 60 FPS (`main.py`) que combina em tempo real:

* a visualização dinâmica do braço de **sete instrumentos diferentes** (não só guitarra);
* o **campo harmônico** e o **filtro de acordes** (o antigo "CAGED", hoje generalizado para tríades, tétradas, inversões, diminutos e suspensos);
* um **editor/tocador de tablatura** com sintetizador próprio;
* um **estúdio de estudos guiados** (nota, escala, acorde, ciclo de quintas, padrões, improviso e uma trilha de aulas);
* **mini-jogos** de precisão rítmica e auditiva;
* **processamento de áudio em tempo real** (afinador, detecção polifônica de notas, detector de ataque/palhetada);
* busca de **músicas** (Songsterr) e de **timbres/equipamento**, com favoritos salvos na nuvem;
* **login e perfis na nuvem** (PostgreSQL), para levar tema, cores, afinações e projetos salvos de um computador para o outro.

O diferencial didático continua sendo o **Filtro de Acordes automático**: ao selecionar um acorde gerado dinamicamente a partir do campo harmônico (Jônico, Dórico, Frígio, etc.), o software mapeia instantaneamente Tônica, Terça e Quinta (ou a tétrade completa) por toda a extensão do braço, aplicando transparência inteligente (*alpha blending*) às notas fora do acorde — o que facilita o estudo de arpejos e a memorização fotográfica das formas (*shapes*).

### 🚀 Funcionalidades

As funcionalidades abaixo estão organizadas por área. Itens marcados **(novo)** não existiam na versão anterior deste README; os demais foram mantidos e, na maioria dos casos, ampliados.

#### 🎸 Instrumento e braço
* **Multi-instrumento (novo):** guitarra de 6 e 7 cordas, baixo de 4 e 5 cordas, ukulele, cavaquinho e teclado — todos compartilham o mesmo motor de diagrama (`config/instrumentos.py`), então estudos, jogos e visualizações funcionam em qualquer um deles.
* **Braço interativo dinâmico:** recálculo automático de espaçamento por instrumento, com dezenas de afinações abertas (Drop A, Standard B, All 4ths, etc.) prontas para uso.
* **Câmera com pan & zoom (novo):** o workspace roda numa superfície virtual (`core/modulos/modulo_camera.py`) que pode ser arrastada e ampliada independentemente da barra superior fixa.
* **Sistema de "gaveteiro" (novo):** os painéis (escalas, acordes, sessão, etc.) vivem em gavetas que se abrem/fecham e se auto-organizam na tela (`ui/components/gaveteiro.py`), com apoio de *drag & drop* com guias de encaixe (*snap guides*, `DragDrop/`).

#### 🎵 Teoria musical
* **Campo harmônico inteligente:** os 7 graus da escala em algarismos romanos, recalculados em tempo real a partir da tônica selecionada.
* **Filtro de acordes ampliado (era só CAGED):** tríades, **tétrades**, **inversões**, **diminutos** e **suspensos** (`ui/blocks/painel_acordes.py`) — o antigo painel CAGED agora é um caso particular desse painel maior.
* **Banco de escalas amplo:** maior, menor, pentatônicas, blues, modos gregos, escalas exóticas, harmônica/menor melódica e teoria avançada (`core/modulos/modulos_*`), geradas dinamicamente por `ui/fabrica_escalas.py`.
* **Blocos extras de teoria (novo):** círculo das quintas/quartas, histórico de notas tocadas, drone de referência, notas por corda, capotraste virtual e progressões prontas — todos arrastáveis (`ui/components/blocos_extras.py`).
* **Paleta de acordes (novo, `ui/components/paleta_acordes.py`):** bloco "Acordes" ao lado do braço com cartões (C, Cm, C7, Cmaj7, sus, dim...). Clicar liga o acorde no braço inteiro; arrastar e soltar no braço encaixa o acorde na forma CAGED mais próxima. Até 6 acordes ao mesmo tempo, cada um com sua cor, e as notas em comum ganham um anel.
* **Graus vs. letras:** alterna a exibição das notas entre nomes absolutos (C D E) e graus (1 2 3) para focar em intervalos.

#### 🧑‍🏫 Estúdio de Estudos guiados (novo)
Um modo de prática dedicado (`Estudos/`, orquestrado por `core/modulos/modulos_estudos.py`), com nove frentes:
* **Notas** — adivinhar, mapear ou reconhecer de ouvido, em qualquer instrumento.
* **Escalas** — prática guiada pelas famílias de escalas do banco de dados musical.
* **Acordes** — reconhecimento e prática de tríades/tétrades comuns.
* **Teoria (ciclo de quintas/quartas)** — roda interativa, montagem de progressões e modo desafio (relativa, armadura, quinta/quarta).
* **Padrões** — sequências melódicas (terças, quartas, arpejos) e células rítmicas clássicas, sincronizadas ao metrônomo.
* **Improvisação** — mostra, acorde a acorde, as notas alvo, as notas de passagem e as notas a evitar, junto com guias de fraseado.
* **Aulas** — trilha guiada do iniciante ao avançado que encadeia os motores de Padrões e Improvisação já pré-configurados, com progresso marcável.
* **Pedais** — o que faz cada pedal, do boost ao whammy, com um áudio de exemplo que muda na hora enquanto você mexe nos botões.
* **Tempo** — abre um MIDI (ou PDF de partitura/tablatura), separa cada compasso em tempos e subdivisões e toca o trecho escolhido em loop com metrônomo.

#### 🎼 Editor e tocador de tablatura (novo)
* Editor de tablatura em grade (`ui/editor_musical.py`, `ui/blocks/tablatura_view.py`) com visão de **Tablatura** e **Partitura** sempre sincronizadas (a partitura é derivada da tablatura, não é um dado separado).
* Sintetizador próprio (`audio/tab_synth.py`) para tocar a tablatura criada, com técnicas marcadas na grade.
* Integração com o **gerenciador de dados de tablatura** (`core/modulos/modulo_dados_tab.py`) e leitura de arquivos **MIDI** (`core/modulos/leitor_midi.py`).

#### 🎮 Mini-jogos
* **Acerte a Nota:** as notas descem numa pauta de 5 linhas com cabeça, haste e acidentes; a nota captada pelo microfone precisa bater com a figura ao cruzar a faixa de acerto. Em dificuldades mais altas também cobra o ataque no tempo certo. Quatro níveis: Fácil, Média, Difícil e Impossível.
* **Rhythm Hero (novo):** jogo de ritmo cujo acerto é medido pelo **ataque** do instrumento (não pelo sustain, então segurar uma nota não pontua). Cada acerto guarda o desvio em milissegundos até o tempo exato, exibido num medidor de precisão — mostra se você atrasa ou adianta o tempo.
* Presets rápidos de configuração (Iniciante, Prática, Desafio) e subdivisões rítmicas (semínima, colcheia, tercina, semicolcheia).

#### 🎚️ Áudio, IA e afinação
* **Processamento de áudio contínuo:** captura por microfone com detecção de frequência (`audio/global_audio.py`) e afinador visual com indicador de desvio em cents.
* **Detecção polifônica de notas (novo):** o motor de áudio global identifica mais de uma nota tocada ao mesmo tempo.
* **Detector de ataque/palhetada (novo, `core/modulos/detector_palhetadas.py`):** usado pelos jogos e estudos para julgar o tempo real da execução, não só a altura da nota.
* **Cliente de transcrição por IA (novo, `core/modulos/modulo_ia_transcricao.py`):** envia um áudio para o microsserviço de transcrição do repositório (FastAPI + Celery + Demucs + basic-pitch, fora do escopo deste README) e recebe notas/BPM de volta.
* **Analisador IA (novo, `Analisador/`):** em Análise de IA → Analisador, compara o timbre gravado da sua pedaleira com uma música de referência, detecta os efeitos usados e sugere ajustes de preset. Roda localmente, sem chave de API.
* **Metrônomo completo:** bloco arrastável da coluna lateral, BPM de 40 a 300, presets rápidos e fórmulas de compasso (2/4, 3/4, 4/4, 6/8), com o primeiro tempo do compasso sempre destacado.

#### 🌐 Músicas, timbre e nuvem (novo)
* **Busca de músicas (Songsterr):** busca tablaturas por artista/música, baixa MIDI de referência e mantém uma lista de **favoritos sincronizada na nuvem**.
* **Minhas músicas:** biblioteca de arquivos MIDI adicionados localmente (também por *drag & drop* de um `.mid`).
* **Busca de timbre:** agrega, para "Artista - Música", quem já timbrou aquele som (fóruns, vídeos, presets) e sites/fontes institucionais, com um botão para copiar um prompt pronto para uma IA de texto.
* **Login e perfis na nuvem:** autenticação (`ui/tela_login.py`, CustomTkinter) contra um banco PostgreSQL na nuvem; tema, cores, afinação e projetos salvos ficam ligados à conta do usuário (`BD/gerenciador_remoto_db.py`, `core/modulos/modulo_perfil.py`).
* **Sessão de estudo:** contabiliza tempo de prática, notas tocadas e o percentual delas dentro do contexto harmônico ativo (`core/sessao_estudo.py`).

#### 🎨 Personalização e interface
* **Sistema de design próprio (novo, `config/design_system.py`):** paletas clara/escura consistentes, com alternância de tema em tempo real.
* **Cor de destaque customizável (novo):** além de 5 temas prontos, dá para digitar um hexadecimal exato ou escolher em um seletor de cor.
* **5 idiomas com tradução dinâmica (novo):** Português, English, Español, Français e Deutsch, traduzidos sob demanda e cacheados (`core/i18n.py`).
* **3 tamanhos de fonte** e 5 fontes de sistema, com reconstrução instantânea da UI ao trocar.
* **Modos de exibição de nota:** letras, graus ou "só a bolinha" (para focar no *shape*).
* **Suporte e tutoriais integrados:** modal com abas (Escalas, Configurações, Metrônomo, Acordes, Vídeos) e reprodução de vídeo-aulas embutida (`core/modulos/modulo_suporte.py`, `modulo_video_aula.py`).

### 🏗️ Arquitetura e Estrutura de Arquivos

A base de código foi refatorada em camadas. A estrutura abaixo reflete o repositório atual (o app desktop; o microsserviço de transcrição e o frontend web em `services/` e `web_frontend/` são programas separados no mesmo repositório e não estão detalhados aqui):

```text
EIGUIT/
├── main.py                       # Entry point / loop principal do motor (60 FPS)
├── studio_cli.py                 # CLI de teoria musical (TUI com "rich")
├── INSTALAR.bat / instalar.ps1   # Instalador do Windows (dependências, banco e atalhos)
├── instalar.sh                   # Instalador do Linux (pacotes, dependências, banco e menu)
├── core/
│   ├── estado_app.py             # EstadoGlobal: fonte única de verdade do app
│   ├── controlador_eventos.py    # Único ponto de tratamento de mouse/teclado
│   ├── config.py                 # Preferências do usuário (cores, fontes, tema, idioma)
│   ├── i18n.py                   # Tradução dinâmica (5 idiomas) com cache
│   ├── sessao_estudo.py          # Rastreamento de tempo/precisão de prática
│   └── modulos/                  # Módulos de features (campo harmônico, metrônomo,
│                                  # processamento de áudio, timbre, songsterr, perfil,
│                                  # transcrição IA, dados de tablatura, câmera, etc.)
├── ui/
│   ├── renderizador_ui.py        # Todos os draw calls: workspace + UI fixa
│   ├── fabrica_escalas.py        # Gera os dicionários de escalas/modos
│   ├── editor_musical.py         # Editor de tablatura/partitura sincronizados
│   ├── tela_login.py             # Tela de autenticação (CustomTkinter)
│   ├── blocks/                   # Braço da guitarra, painel de acordes, tablatura
│   └── components/                # Barra superior, navegação inferior, gaveteiro,
│                                  # sidebar de áudio, blocos extras de teoria
├── Estudos/                       # As trilhas do Estúdio de Estudos
├── Analisador/                    # Analisador IA de timbre (pedaleira x referência)
├── Jogos/                         # Acerte a Nota, Rhythm Hero e o gerenciador de jogos
├── DragDrop/                      # Elementos arrastáveis e guias de encaixe (snap)
├── audio/                         # Motor de áudio global (mic) e sintetizador de tablatura
├── BD/                            # Acesso ao PostgreSQL na nuvem (perfis, favoritos)
├── config/                        # Design system, instrumentos, layout, temas
├── assets/                        # Imagens, ícones, timbres e áudios do projeto
└── _validacao/                    # Suítes de teste sem janela (python _validacao/<suite>.py)
```

### 🛠️ Instalação

O EIGUIT roda em **Windows 10/11** e **Linux** (Ubuntu/Debian, Fedora, Arch, openSUSE e derivados). Ele usa **Python 3.12**, gerenciado pelo **[uv](https://docs.astral.sh/uv/)**. O `pyproject.toml` e o `uv.lock` fixam todas as versões, então todo mundo instala exatamente o mesmo ambiente. Você **não precisa instalar o Python antes**: o uv baixa o Python 3.12 sozinho quando ele não existe na máquina.

#### 1. Baixe o projeto

Escolha um dos jeitos:

* **Com git:**
  ```bash
  git clone https://github.com/Abelardo-Matheus/EIGUIT.git
  cd EIGUIT
  ```
* **Sem git:** no GitHub, clique em **Code → Download ZIP** e extraia a pasta onde quiser deixar o programa (por exemplo, em Documentos). Não extraia dentro de uma pasta temporária: os atalhos apontam para esse lugar.

#### 2. Instalação automática (recomendada)

Os instaladores fazem tudo: instalam o que faltar no sistema, criam o ambiente Python com as dependências, perguntam a URL do banco de login e criam o atalho do programa. Nenhum deles precisa ser rodado como administrador/root.

**🪟 Windows**

1. Abra a pasta do EIGUIT e dê dois cliques em **`INSTALAR.bat`**.
2. Na primeira vez, o download das dependências leva alguns minutos.
3. Quando ele perguntar, cole a URL do banco (veja o [passo 4](#4-banco-de-dados-do-login)) ou aperte Enter para configurar depois.
4. Pronto: abra pelo atalho **EIGUIT** na Área de Trabalho ou no Menu Iniciar.

> Se o Windows mostrar "O Windows protegeu o computador" (SmartScreen), clique em **Mais informações → Executar assim mesmo**. O aviso aparece porque o `.bat` não tem assinatura digital.

**🐧 Linux**

1. Abra um terminal na pasta do EIGUIT e rode:
   ```bash
   bash instalar.sh
   ```
2. O script pede sua senha **só** para instalar os pacotes do sistema (via `apt`, `dnf`, `pacman` ou `zypper`, conforme a distribuição).
3. Quando ele perguntar, cole a URL do banco ou aperte Enter para configurar depois.
4. Pronto: abra pelo menu de aplicativos (**EIGUIT**) ou digite `eiguit` no terminal.

Opções do script: `bash instalar.sh --sem-sistema` pula os pacotes do sistema (útil sem sudo, se eles já estiverem instalados); `bash instalar.sh --desinstalar` remove o atalho e o ambiente.

#### 3. Instalação manual (passo a passo)

Use este caminho se preferir saber exatamente o que entra na sua máquina, ou se o instalador automático falhar.

**🪟 Windows**

1. Instale o **uv** (e, se for usar, o git). No PowerShell:
   ```powershell
   winget install astral-sh.uv
   winget install Git.Git
   ```
   Sem o winget, instale o uv com: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`. Feche e abra o terminal depois de instalar.
2. Na pasta do EIGUIT, instale as dependências:
   ```powershell
   uv sync
   ```
   No Windows todas as dependências têm pacotes prontos (não é preciso compilador). Os DLLs do FluidSynth e os SoundFonts já vêm em `assets\`.
3. Execute:
   ```powershell
   uv run python main.py
   ```

**🐧 Linux**

1. Instale os pacotes do sistema. Eles são necessários porque o `pyaudio` (exigido pelo `tinysoundfont`) não tem pacote pronto para Linux e é compilado na instalação, e porque o OpenCV, o Tk e o áudio usam bibliotecas nativas:

   | Distribuição | Comando |
   |---|---|
   | Ubuntu, Debian, Mint, Pop!_OS | `sudo apt install build-essential python3-dev portaudio19-dev libportaudio2 libsndfile1 python3-tk libgl1 libglib2.0-0 ffmpeg curl git` |
   | Fedora | `sudo dnf install gcc gcc-c++ make python3-devel portaudio-devel libsndfile python3-tkinter mesa-libGL glib2 ffmpeg-free curl git` |
   | Arch, Manjaro | `sudo pacman -S --needed base-devel portaudio libsndfile tk mesa glib2 ffmpeg curl git` |
   | openSUSE | `sudo zypper install gcc gcc-c++ make python3-devel portaudio-devel libsndfile1 python3-tk Mesa-libGL1 glib2 curl git` (ffmpeg opcional: `ffmpeg` ou `ffmpeg-7`, conforme a versão) |

2. Instale o **uv**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   Depois abra um terminal novo (ou rode `source ~/.local/bin/env`).
3. Na pasta do EIGUIT, instale as dependências e execute:
   ```bash
   uv sync
   uv run python main.py
   ```

> Rode o programa sempre **a partir da pasta do EIGUIT**: ele procura `assets/`, perfis e SoundFonts em caminhos relativos a ela. Os atalhos criados pelos instaladores já fazem isso.

#### 4. Banco de dados do login

O app abre primeiro uma **tela de login** e só continua depois de autenticar num banco PostgreSQL na nuvem. A URL de conexão **não fica no código**. O programa procura, nesta ordem:

1. a variável de ambiente `EIGUIT_DB_URL`;
2. o arquivo `banco.txt` na pasta de configuração do usuário:
   * Windows: `%APPDATA%\EIGUIT\banco.txt`
   * Linux: `~/.config/EIGUIT/banco.txt`
3. o arquivo `banco.local.txt` na pasta do projeto (ignorado pelo git).

O arquivo deve ter só a URL, numa linha (`postgresql://usuario:senha@servidor/banco?sslmode=require`). Os instaladores criam o `banco.txt` por você. Sem a URL, a tela de login abre, mas não conecta.

#### 5. Recursos opcionais

Nada disto é necessário para o programa abrir:

* **Ler PDF de partitura no estudo "Tempo"** e **baixar músicas de referência no Analisador IA:**
  ```bash
  uv pip install pypdf yt-dlp
  ```
  Para o Analisador converter o áudio baixado também é preciso o **ffmpeg**: no Linux ele já entra com os pacotes acima; no Windows, `winget install Gyan.FFmpeg`. Como o `uv sync` deixa o ambiente igual ao `uv.lock`, rode esse `uv pip install` de novo depois de cada `uv sync`.
* **Serviço de transcrição por IA e frontend web** (`services/`, `web_frontend/`): são programas separados, com instalação própria (Docker/Redis, um Python 3.11 e Node.js). O `Ligar_GuitarStudio.bat` liga os quatro serviços no Windows.

#### 6. Atualizar e desinstalar

* **Atualizar:** na pasta do EIGUIT, rode `git pull` (ou baixe o ZIP novo por cima) e depois `uv sync`. Rodar o instalador de novo também funciona.
* **Desinstalar:** Windows, `powershell -ExecutionPolicy Bypass -File instalar.ps1 -Desinstalar`; Linux, `bash instalar.sh --desinstalar`. Isso remove atalhos e o ambiente `.venv`. Depois é só apagar a pasta do EIGUIT. Seus perfis locais e a URL do banco ficam em `%APPDATA%\EIGUIT` / `~/.config/EIGUIT`, caso queira apagar também.

#### 7. Problemas comuns

| Sintoma | Causa e solução |
|---|---|
| `uv sync` falha com **`portaudio.h`** (Linux) | Faltam os pacotes de compilação. Instale os da tabela do passo 3 e rode `uv sync` de novo. |
| **`libGL.so.1: cannot open shared object file`** (Linux) | Falta a biblioteca OpenGL usada pelo OpenCV: `libgl1` (Debian/Ubuntu) ou `mesa-libGL` (Fedora). |
| **`No module named '_tkinter'`** (Linux) | Falta o Tk do sistema: `python3-tk` (Debian/Ubuntu), `python3-tkinter` (Fedora) ou `tk` (Arch). |
| **`uv` não é reconhecido** depois de instalar | O terminal não recarregou o PATH. Feche e abra o terminal (ou reinicie a sessão). |
| PowerShell diz que **a execução de scripts foi desabilitada** | Use o `INSTALAR.bat`, que já chama o script com `-ExecutionPolicy Bypass` só para essa execução. |
| Login **não conecta** | A URL do banco não foi configurada ou está errada. Veja o [passo 4](#4-banco-de-dados-do-login). |
| O app abre, mas **sem som ou sem microfone** | Confira o dispositivo de entrada/saída padrão do sistema. No Linux, o usuário precisa ter acesso ao áudio (PipeWire/PulseAudio rodando). |
| O atalho abre e **fecha na hora** | Rode no terminal para ver o erro: `.venv\Scripts\python main.py` (Windows) ou `.venv/bin/python main.py` (Linux), sempre de dentro da pasta do EIGUIT. |

Também existe um executável standalone gerado com PyInstaller (`build/GuitarStudioIA/GuitarStudioIA.exe`); se preferir testar sem configurar o ambiente Python, gere ou baixe o `.zip` da build mais recente e mantenha a pasta `assets/` no mesmo diretório do `.exe`.

### 🎮 Guia de Uso Rápido

1. **Login:** autentique-se na tela inicial (CustomTkinter). Seu tema, cores e afinações favoritas ficam salvos na sua conta.
2. **Instrumento:** troque entre guitarra (6/7 cordas), baixo (4/5 cordas), ukulele, cavaquinho ou teclado nos controles de instrumento — o braço se redimensiona sozinho.
3. **Escalas e acordes:** abra a gaveta de Escalas ou Acordes na barra inferior e arraste uma forma para o braço (ou use o bloco "Acordes" da coluna lateral); clique com o botão direito sobre o braço para devolver tudo ao painel de origem.
4. **Campo harmônico:** clique num grau (I, II, III...) para isolar as notas daquele acorde no braço, com transparência no restante da escala; clique de novo para desmarcar.
5. **Estúdio de Estudos:** abra a gaveta "Estudos" e escolha uma trilha (Notas, Escalas, Acordes, Teoria, Padrões, Improvisação, Aulas, Pedais ou Tempo).
6. **Editor de tablatura:** na gaveta "Músicas", vá em "Criação Musical" → "Criar Tablatura" para abrir o editor/tocador.
7. **Mini-jogos:** na gaveta de Análise de IA/Jogos, escolha "Acerte a Nota" ou "Rhythm Hero" e toque fisicamente no seu instrumento — o jogo julga afinação e tempo.
8. **Busca de músicas e timbre:** na gaveta "Músicas", use "Busca" para procurar tablaturas no Songsterr (e favoritar), ou a aba de Timbre para pesquisar como outros músicos tocaram determinada música.
9. **Metrônomo:** abra o bloco "Metronomo" na coluna lateral (à esquerda) e ajuste BPM, compasso e presets.
10. **Personalização:** na aba Configurações, troque tema, cor de destaque (inclusive por hexadecimal), fonte, tamanho de fonte, idioma (5 opções) e o modo de exibição das notas (letras, graus ou só a bolinha).

### 📸 Capturas de tela / Screenshots

Prints do programa rodando (tema escuro):

<p align="center">
  <img src="docs/screenshots/campo_harmonico.png" width="410" alt="Campo harmônico / filtro de acordes">
  <img src="docs/screenshots/jogo_rhythm_hero.png" width="410" alt="Mini-jogo Rhythm Hero">
</p>
<p align="center">
  <img src="docs/screenshots/musicas_busca.png" width="410" alt="Busca de músicas Songsterr">
  <img src="docs/screenshots/configuracoes.png" width="410" alt="Painel de configurações">
</p>
<p align="center">
  <img src="docs/screenshots/afinador_ia.png" width="560" alt="Afinador e detecção em tempo real">
  <img src="docs/screenshots/login.png" width="210" alt="Tela de login">
</p>

---

## 🇺🇸 English

### ⚠️ Project Status: Beta

EIGUIT outgrew being "just a fretboard viewer": after a large refactor, it's now a **full studio**, organized in layers (`core/`, `ui/`, `audio/`, `Jogos/`, `DragDrop/`, `BD/`, `config/`) with its own design system. The core musical math, fretboard rendering, audio DSP and tablature editor are fully operational; the newest modules (Study Studio, tablature editor, song/gear search, cloud profiles) still get frequent visual and stability refinements.

**Contributors wanted!**
* **Design (UI/UX):** visual polish, responsiveness and micro-interactions for the custom design system (`config/design_system.py`).
* **Development (Python/Pygame):** rendering performance, new modules under `core/modulos/`, and integration with the AI transcription service.
* **Music theory:** new tracks under `Estudos/`, exotic scales, tetrads and progressions.
* **QA/Testing:** bug reports, suggestions and new checks for the validation suites in `_validacao/` (they run headless, with no window or sound card).

### 📝 About the Project

**Guitar Studio IA (EIGUIT)** is an interactive tool for guitarists, bassists, music theory students and producers, written entirely in Python with Pygame. The core is a 60 FPS loop (`main.py`) that combines in real time:

* a dynamic fretboard/neck for **seven different instruments** (not just guitar);
* the **harmonic field** and **chord filter** (the former "CAGED", now generalized to triads, tetrads, inversions, diminished and suspended chords);
* a built-in **tablature editor/player** with its own synthesizer;
* a **guided Study Studio** (notes, scales, chords, circle of fifths, patterns, improvisation and a lesson track);
* **mini-games** for rhythmic and pitch accuracy;
* **real-time audio processing** (tuner, polyphonic note detection, pick/attack detection);
* **song search** (Songsterr) and **gear/tone search**, with cloud-synced favorites;
* **cloud login and profiles** (PostgreSQL), carrying theme, colors, tunings and saved projects between computers.

The educational centerpiece remains the **Automatic Chord Filter**: selecting a chord dynamically generated from the harmonic field (Ionian, Dorian, Phrygian, etc.) instantly maps the Root, Third and Fifth (or the full tetrad) across the entire fretboard, applying smart alpha-blending transparency to notes outside the chord — drastically simplifying arpeggio study and shape memorization.

### 🚀 Features

Grouped by area. Items marked **(new)** did not exist in the previous version of this README; everything else was kept and, in most cases, expanded.

#### 🎸 Instrument and fretboard
* **Multi-instrument (new):** 6- and 7-string guitar, 4- and 5-string bass, ukulele, cavaquinho and keyboard — all sharing the same diagram engine (`config/instrumentos.py`), so studies, games and visualizations work on any of them.
* **Dynamic interactive fretboard:** automatic spacing recalculation per instrument, with dozens of ready-to-use open tunings (Drop A, Standard B, All 4ths, etc.).
* **Pan & zoom camera (new):** the workspace renders onto a virtual surface (`core/modulos/modulo_camera.py`) that can be panned/zoomed independently of the fixed top bar.
* **"Drawer" system (new):** panels (scales, chords, session, etc.) live in drawers that open/close and self-arrange on screen (`ui/components/gaveteiro.py`), backed by drag & drop with snap guides (`DragDrop/`).

#### 🎵 Music theory
* **Smart harmonic field:** the 7 scale degrees in Roman numerals, recalculated live from the selected root.
* **Expanded chord filter (used to be just CAGED):** triads, **tetrads**, **inversions**, **diminished** and **suspended** chords (`ui/blocks/painel_acordes.py`) — the old CAGED panel is now a special case of this larger panel.
* **Large scale library:** major, minor, pentatonics, blues, Greek modes, exotic scales, harmonic/melodic minor and advanced theory (`core/modulos/modulos_*`), generated dynamically by `ui/fabrica_escalas.py`.
* **Extra theory blocks (new):** circle of fifths/fourths, played-note history, reference drone, notes-per-string, virtual capo and ready-made progressions — all draggable (`ui/components/blocos_extras.py`).
* **Chord palette (new, `ui/components/paleta_acordes.py`):** an "Acordes" block next to the neck with chord cards (C, Cm, C7, Cmaj7, sus, dim...). Click to light a chord across the whole neck; drag it onto the neck to snap it to the nearest CAGED shape. Up to 6 chords at once, each in its own color, with shared notes ringed.
* **Degrees vs. letters:** toggle note display between absolute names (C D E) and degrees (1 2 3) to focus on intervals.

#### 🧑‍🏫 Guided Study Studio (new)
A dedicated practice mode (`Estudos/`, orchestrated by `core/modulos/modulos_estudos.py`) with nine tracks:
* **Notes** — guess, map or ear-train, on any instrument.
* **Scales** — guided practice through the scale library.
* **Chords** — recognition and practice of common triads/tetrads.
* **Theory (circle of fifths/fourths)** — interactive wheel, progression building and a challenge mode (relative key, key signature, fifth/fourth).
* **Patterns** — melodic sequences (thirds, fourths, arpeggios) and classic rhythmic cells, synced to the metronome.
* **Improvisation** — shows, chord by chord, target notes, passing scale notes and notes to avoid, plus phrasing guides.
* **Lessons** — a guided beginner-to-advanced track that opens the Patterns/Improvisation engines already pre-configured, with completion tracking.
* **Pedals** — what each effect pedal does, from boost to whammy, with an example sound that changes live as you turn the knobs.
* **Timing** — opens a MIDI (or a score/tab PDF), splits every measure into beats and subdivisions and loops the selected passage with a metronome.

#### 🎼 Tablature editor and player (new)
* Grid-based tablature editor (`ui/editor_musical.py`, `ui/blocks/tablatura_view.py`) with always-in-sync **Tablature** and **Sheet Music** views (sheet music is derived from the tab grid, not stored separately).
* Its own synthesizer (`audio/tab_synth.py`) to play back the created tablature, including grid-marked techniques.
* Integrates with the **tablature data manager** (`core/modulos/modulo_dados_tab.py`) and **MIDI** file reading (`core/modulos/leitor_midi.py`).

#### 🎮 Mini-games
* **Hit the Note:** notes fall on a 5-line staff with noteheads, stems and accidentals; the note detected by the microphone must match the figure as it crosses the hit zone. Higher difficulties also require hitting the attack on time. Four levels: Easy, Medium, Hard and Impossible.
* **Rhythm Hero (new):** a rhythm game where hits are judged by the instrument's **attack** (not sustain, so holding a note earns nothing). Every hit stores its deviation in milliseconds from the exact beat, shown on a precision meter — revealing whether you rush or drag.
* Quick setup presets (Beginner, Practice, Challenge) and rhythmic subdivisions (quarter, eighth, triplet, sixteenth notes).

#### 🎚️ Audio, AI and tuning
* **Continuous audio processing:** microphone capture with frequency detection (`audio/global_audio.py`) and a visual tuner with cents-deviation feedback.
* **Polyphonic note detection (new):** the global audio engine identifies more than one note played at once.
* **Pick/attack detector (new, `core/modulos/detector_palhetadas.py`):** used by games and studies to judge real playing timing, not just pitch.
* **AI transcription client (new, `core/modulos/modulo_ia_transcricao.py`):** sends audio to the repository's transcription microservice (FastAPI + Celery + Demucs + basic-pitch, out of scope for this README) and gets notes/BPM back.
* **AI Analyzer (new, `Analisador/`):** under AI Analysis → Analyzer, compares the recorded tone of your pedalboard with a reference song, detects the effects in use and suggests preset tweaks. Runs locally, no API key.
* **Full metronome:** a draggable block from the side column, 40–300 BPM, quick presets and time signatures (2/4, 3/4, 4/4, 6/8), always accenting the downbeat.

#### 🌐 Songs, gear and cloud (new)
* **Song search (Songsterr):** search tabs by artist/song, download reference MIDI, and keep a **cloud-synced favorites** list.
* **My Songs:** a library of locally added MIDI files (also via drag & drop of a `.mid`).
* **Gear/tone search:** for "Artist - Song", aggregates who already dialed in that tone (forums, videos, presets) and official sites/sources, with a button to copy a ready-made prompt for a text AI.
* **Cloud login and profiles:** authentication (`ui/tela_login.py`, CustomTkinter) against a cloud PostgreSQL database; theme, colors, tuning and saved projects are tied to the user's account (`BD/gerenciador_remoto_db.py`, `core/modulos/modulo_perfil.py`).
* **Study session tracking:** tracks practice time, notes played and how many of them fall inside the active harmonic context (`core/sessao_estudo.py`).

#### 🎨 Customization and interface
* **Custom design system (new, `config/design_system.py`):** consistent light/dark palettes with live theme switching.
* **Custom accent color (new):** besides 5 ready-made themes, type an exact hex color or pick one from a color picker.
* **5 languages with dynamic translation (new):** Portuguese, English, Spanish, French and German, translated on demand and cached (`core/i18n.py`).
* **3 font sizes** and 5 system fonts, with instant UI rebuild on change.
* **Note display modes:** letters, degrees, or "dot only" (to focus on the shape).
* **Built-in support and tutorials:** a tabbed modal (Scales, Settings, Metronome, Chords, Videos) with embedded video-lesson playback (`core/modulos/modulo_suporte.py`, `modulo_video_aula.py`).

### 🏗️ Architecture and File Structure

The codebase was refactored into layers. The tree below reflects the current repository (the desktop app; the transcription microservice and web frontend under `services/` and `web_frontend/` are separate programs in the same repo and are out of scope here):

```text
EIGUIT/
├── main.py                       # Entry point / main engine loop (60 FPS)
├── studio_cli.py                 # Music-theory CLI (rich TUI)
├── INSTALAR.bat / instalar.ps1   # Windows installer (dependencies, database, shortcuts)
├── instalar.sh                   # Linux installer (packages, dependencies, database, menu)
├── core/
│   ├── estado_app.py             # EstadoGlobal: the single source of truth
│   ├── controlador_eventos.py    # The only mouse/keyboard input handler
│   ├── config.py                 # User preferences (colors, fonts, theme, language)
│   ├── i18n.py                   # Dynamic translation (5 languages) with caching
│   ├── sessao_estudo.py          # Practice time/accuracy tracking
│   └── modulos/                  # Feature modules (harmonic field, metronome,
│                                  # audio processing, gear search, Songsterr, profile,
│                                  # AI transcription, tab data, camera, etc.)
├── ui/
│   ├── renderizador_ui.py        # All draw calls: workspace + fixed UI
│   ├── fabrica_escalas.py        # Generates the scale/mode dictionaries
│   ├── editor_musical.py         # Synced tablature/sheet-music editor
│   ├── tela_login.py             # Authentication screen (CustomTkinter)
│   ├── blocks/                   # Fretboard, chord panel, tablature block
│   └── components/                # Top bar, bottom navigation, drawer system,
│                                  # audio sidebar, extra theory blocks
├── Estudos/                       # The Study Studio tracks
├── Analisador/                    # AI tone analyzer (pedalboard vs. reference)
├── Jogos/                         # Hit the Note, Rhythm Hero and the games manager
├── DragDrop/                      # Draggable elements and snap guides
├── audio/                         # Global (mic) audio engine and tab synthesizer
├── BD/                            # Cloud PostgreSQL access (profiles, favorites)
├── config/                        # Design system, instruments, layout, themes
├── assets/                        # Project images, icons, timbres and audio
└── _validacao/                    # Headless test suites (python _validacao/<suite>.py)
```

### 🛠️ Installation

EIGUIT runs on **Windows 10/11** and **Linux** (Ubuntu/Debian, Fedora, Arch, openSUSE and derivatives). It uses **Python 3.12**, managed by **[uv](https://docs.astral.sh/uv/)**; `pyproject.toml` and `uv.lock` pin every version, so everyone gets exactly the same environment. You **don't need to install Python first**: uv downloads Python 3.12 by itself when the machine doesn't have it.

#### 1. Get the project

* **With git:**
  ```bash
  git clone https://github.com/Abelardo-Matheus/EIGUIT.git
  cd EIGUIT
  ```
* **Without git:** on GitHub, click **Code → Download ZIP** and extract the folder where you want the program to live (e.g. Documents). Don't run it from a temporary folder: the shortcuts point to this location.

#### 2. Automatic install (recommended)

The installers do everything: install whatever the system is missing, create the Python environment with all dependencies, ask for the login database URL and create the app shortcut. Neither needs to run as administrator/root.

**🪟 Windows**

1. Open the EIGUIT folder and double-click **`INSTALAR.bat`**.
2. The first time, downloading the dependencies takes a few minutes.
3. When asked, paste the database URL (see [step 4](#4-login-database)) or press Enter to set it up later.
4. Done: open it from the **EIGUIT** shortcut on the Desktop or in the Start Menu.

> If Windows shows "Windows protected your PC" (SmartScreen), click **More info → Run anyway**. The warning appears because the `.bat` is not digitally signed.

**🐧 Linux**

1. Open a terminal in the EIGUIT folder and run:
   ```bash
   bash instalar.sh
   ```
2. The script asks for your password **only** to install system packages (via `apt`, `dnf`, `pacman` or `zypper`, depending on the distro).
3. When asked, paste the database URL or press Enter to set it up later.
4. Done: open it from the applications menu (**EIGUIT**) or type `eiguit` in a terminal.

Script options: `bash instalar.sh --sem-sistema` skips the system packages (useful without sudo, if they're already installed); `bash instalar.sh --desinstalar` removes the shortcut and the environment.

#### 3. Manual install (step by step)

Use this path if you'd rather know exactly what goes on your machine, or if the automatic installer fails.

**🪟 Windows**

1. Install **uv** (and git, if you'll use it). In PowerShell:
   ```powershell
   winget install astral-sh.uv
   winget install Git.Git
   ```
   Without winget, install uv with: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`. Close and reopen the terminal afterwards.
2. In the EIGUIT folder, install the dependencies:
   ```powershell
   uv sync
   ```
   On Windows every dependency ships as a prebuilt package (no compiler needed). The FluidSynth DLLs and the SoundFonts already come in `assets\`.
3. Run:
   ```powershell
   uv run python main.py
   ```

**🐧 Linux**

1. Install the system packages. They're required because `pyaudio` (pulled in by `tinysoundfont`) has no prebuilt Linux package and is compiled during install, and because OpenCV, Tk and audio rely on native libraries:

   | Distribution | Command |
   |---|---|
   | Ubuntu, Debian, Mint, Pop!_OS | `sudo apt install build-essential python3-dev portaudio19-dev libportaudio2 libsndfile1 python3-tk libgl1 libglib2.0-0 ffmpeg curl git` |
   | Fedora | `sudo dnf install gcc gcc-c++ make python3-devel portaudio-devel libsndfile python3-tkinter mesa-libGL glib2 ffmpeg-free curl git` |
   | Arch, Manjaro | `sudo pacman -S --needed base-devel portaudio libsndfile tk mesa glib2 ffmpeg curl git` |
   | openSUSE | `sudo zypper install gcc gcc-c++ make python3-devel portaudio-devel libsndfile1 python3-tk Mesa-libGL1 glib2 curl git` (optional ffmpeg: `ffmpeg` or `ffmpeg-7`, depending on the release) |

2. Install **uv**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   Then open a new terminal (or run `source ~/.local/bin/env`).
3. In the EIGUIT folder, install the dependencies and run:
   ```bash
   uv sync
   uv run python main.py
   ```

> Always run the program **from the EIGUIT folder**: it looks up `assets/`, profiles and SoundFonts relative to it. The shortcuts created by the installers already do this.

#### 4. Login database

The app first opens a **login screen** and only continues after authenticating against a cloud PostgreSQL database. The connection URL is **not in the code**; the program looks, in this order, for:

1. the `EIGUIT_DB_URL` environment variable;
2. a `banco.txt` file in the user's config folder:
   * Windows: `%APPDATA%\EIGUIT\banco.txt`
   * Linux: `~/.config/EIGUIT/banco.txt`
3. a `banco.local.txt` file in the project folder (ignored by git).

The file must contain only the URL, on one line (`postgresql://user:password@host/database?sslmode=require`). The installers create `banco.txt` for you. Without the URL, the login screen opens but can't connect.

#### 5. Optional features

None of this is needed for the program to start:

* **Reading score PDFs in the "Timing" study** and **downloading reference songs in the AI Analyzer:**
  ```bash
  uv pip install pypdf yt-dlp
  ```
  The Analyzer also needs **ffmpeg** to convert the downloaded audio: on Linux it comes with the packages above; on Windows, `winget install Gyan.FFmpeg`. Since `uv sync` resets the environment to match `uv.lock`, run that `uv pip install` again after each `uv sync`.
* **AI transcription service and web frontend** (`services/`, `web_frontend/`): separate programs with their own setup (Docker/Redis, a Python 3.11 and Node.js). `Ligar_GuitarStudio.bat` starts all four services on Windows.

#### 6. Update and uninstall

* **Update:** in the EIGUIT folder, run `git pull` (or extract the new ZIP over it) and then `uv sync`. Running the installer again also works.
* **Uninstall:** Windows, `powershell -ExecutionPolicy Bypass -File instalar.ps1 -Desinstalar`; Linux, `bash instalar.sh --desinstalar`. This removes the shortcuts and the `.venv` environment; then just delete the EIGUIT folder. Your local profiles and the database URL live in `%APPDATA%\EIGUIT` / `~/.config/EIGUIT`, in case you want to delete them too.

#### 7. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `uv sync` fails with **`portaudio.h`** (Linux) | Build packages are missing. Install the ones from the step 3 table and run `uv sync` again. |
| **`libGL.so.1: cannot open shared object file`** (Linux) | The OpenGL library used by OpenCV is missing: `libgl1` (Debian/Ubuntu) or `mesa-libGL` (Fedora). |
| **`No module named '_tkinter'`** (Linux) | System Tk is missing: `python3-tk` (Debian/Ubuntu), `python3-tkinter` (Fedora) or `tk` (Arch). |
| **`uv` is not recognized** after installing | The terminal didn't reload PATH. Close and reopen it (or log out and back in). |
| PowerShell says **running scripts is disabled** | Use `INSTALAR.bat`, which already calls the script with `-ExecutionPolicy Bypass` for that run only. |
| Login **won't connect** | The database URL isn't set or is wrong. See [step 4](#4-login-database). |
| The app opens but has **no sound or microphone** | Check the system's default input/output device. On Linux, your user needs audio access (PipeWire/PulseAudio running). |
| The shortcut opens and **closes immediately** | Run it in a terminal to see the error: `.venv\Scripts\python main.py` (Windows) or `.venv/bin/python main.py` (Linux), always from inside the EIGUIT folder. |

A standalone PyInstaller-built executable also exists (`build/GuitarStudioIA/GuitarStudioIA.exe`); if you'd rather test it without a Python setup, build or download the latest `.zip` and keep the `assets/` folder next to the `.exe`.

### 🎮 Quick Start Guide

1. **Login:** authenticate on the startup screen (CustomTkinter). Your theme, colors and favorite tunings are saved to your account.
2. **Instrument:** switch between guitar (6/7 strings), bass (4/5 strings), ukulele, cavaquinho or keyboard in the instrument controls — the fretboard resizes itself.
3. **Scales and chords:** open the Scales or Chords drawer in the bottom bar and drag a shape onto the fretboard (or use the "Acordes" block in the side column); right-click the fretboard to send everything back to its panel.
4. **Harmonic field:** click a degree (I, II, III...) to isolate that chord's notes on the fretboard, dimming the rest of the scale; click again to clear it.
5. **Study Studio:** open the "Estudos" drawer and pick a track (Notes, Scales, Chords, Theory, Patterns, Improvisation, Lessons, Pedals or Timing).
6. **Tablature editor:** in the "Músicas" drawer, go to "Criação Musical" → "Criar Tablatura" to open the editor/player.
7. **Mini-games:** in the AI Analysis/Games drawer, pick "Hit the Note" or "Rhythm Hero" and physically play your instrument — the game judges pitch and timing.
8. **Song and gear search:** in the "Músicas" drawer, use "Search" to look up tabs on Songsterr (and favorite them), or the Gear tab to see how other musicians got a particular tone.
9. **Metronome:** open the "Metronomo" block from the left side column and set BPM, time signature and presets.
10. **Customization:** in Settings, change theme, accent color (including by hex code), font, font size, language (5 options) and note display mode (letters, degrees, or dot only).

### 📸 Screenshots

Screenshots of the running program are in the [Capturas de tela](#-capturas-de-tela--screenshots) section above.

---

## ⚖️ Termos de Uso e Licença Comercial / Terms of Use & Commercial License

**© 2026 Guitar Studio IA - MATHEUS ABELARDO TREVENZOLI ARAUJO. Todos os Direitos Reservados / All Rights Reserved.**

Este documento estabelece as regras estritas de utilização para o código-fonte, algoritmos de renderização, matemática de interface e ativos visuais presentes neste repositório.

1. **PROPRIEDADE INTELECTUAL:** Todo o código-fonte e algoritmos contidos neste repositório são de propriedade intelectual exclusiva do autor.
2. **USO PERMITIDO (CÓDIGO ABERTO):** É concedida permissão para clonar, baixar, compilar e executar este software **exclusivamente para fins educacionais, acadêmicos, estudo de código e uso recreativo/pessoal.** Contribuições via *Pull Requests* para melhoria do repositório original são bem-vindas e incentivadas.
3. **RESTRIÇÕES DE USO (NÃO COMERCIAL E SEM DERIVADOS):**
   * É expressamente **PROIBIDA** a venda, comercialização, aluguel, assinatura ou monetização direta/indireta deste software, bem como a integração do seu código em softwares pagos ou de terceiros.
   * É expressamente **PROIBIDA** a criação e distribuição pública de produtos derivados (*forks* que alterem a marca para se passarem por outro produto) com intenções de lucro ou sem a devida atribuição.
   * A cópia e redistribuição em massa deste software em plataformas externas sem os créditos originais, links para este repositório do GitHub e a manutenção desta licença anexada resultará em violação de direitos autorais.
4. **GARANTIA LIMITADA:** O software é fornecido "no estado em que se encontra" (*as is*), sem garantias de comercialização, funcionalidade livre de falhas ou adequação a propósitos específicos. O autor não se responsabiliza por danos lógicos ou problemas de processamento de áudio derivados do uso deste código.

---
*Desenvolvido com dedicação, lógica e muito ☕ para músicos que buscam a verdadeira evolução. / Engineered with logic, dedication, and ☕ for musicians pursuing true evolution.*
