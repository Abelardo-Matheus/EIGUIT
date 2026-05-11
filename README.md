

<div align="center">
  <img src="https://github.com/user-attachments/assets/a8fadb13-ea2e-44e0-aead-4abb4989a3c6" width="250" style="border-radius: 50%; opacity: 0.3;" alt="Guitar Studio IA Logo">
  
  <h1>🎸 EIGUIT </h1>
  <p><i>Braço de guitarra virtual, motor de campo harmônico e processamento de áudio</i></p>
  <p><i>Virtual Fretboard, Harmonic Field Engine & Audio Processing</i></p>
  
  <img src="https://github.com/user-attachments/assets/2d5ffac7-f68f-4418-9845-cb4d508d2c65" width="400" alt="Guitar Studio IA Main Interface">
  <img src="https://github.com/user-attachments/assets/afa59f64-ae8a-434c-bb4c-b26103066716" width="400" alt="Guitar Studio IA Main Interface">
  
  <br><br>

  <p>
    <img src="https://img.shields.io/badge/Status-Beta_1-orange?style=for-the-badge" alt="Version Beta">
    <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python Version">
    <img src="https://img.shields.io/badge/Platform-Windows_|_Linux_|_macOS-lightgrey?style=for-the-badge" alt="Platforms">
    <img src="https://img.shields.io/badge/License-Copyright_Reserved-red?style=for-the-badge" alt="License">
  </p>
</div>


## 🇧🇷 Português

### ⚠️ Status do Projeto: Versão Beta
Este projeto está atualmente em sua fase **Beta**. Embora a lógica musical matemática, a renderização do braço e os cálculos de processamento de áudio estejam operacionais, o software ainda passa por constantes refinamentos visuais, correção de pequenos *glitches* de interface e otimizações de performance.

**Procuramos Colaboradores!** O projeto tem grande potencial de expansão. Seu apoio é muito bem-vindo para:
* **Design (UI/UX):** Melhorar a interface gráfica, responsividade e experiência do usuário.
* **Desenvolvimento (Python):** Otimização de performance de renderização do Pygame e integração de novos módulos analíticos e de gamificação.
* **Teoria Musical:** Expansão do sistema para suportar tétrades, escalas exóticas e afinadores estroboscópicos.
* **QA / Testes:** Reportar falhas (*bugs*) e sugerir melhorias de estabilidade.

### 📝 Sobre o Projeto
O **Guitar Studio IA** é uma ferramenta interativa e avançada voltada para guitarristas, baixistas, estudantes de teoria musical e produtores. Desenvolvido inteiramente em Python utilizando a biblioteca Pygame para renderização e processamento vetorial, o software oferece uma visualização dinâmica e em tempo real do braço do instrumento acoplada à análise de campo harmônico.

O grande diferencial tecnológico e didático deste projeto é o sistema de **Filtro CAGED Automático**. Ao selecionar um acorde gerado dinamicamente dentro do campo harmônico (Jônio, Dórico, Frígio, etc.), o software mapeia instantaneamente as notas da tríade (Tônica, Terça, Quinta) por toda a extensão do braço, aplicando transparência inteligente (Alpha blending) às notas irrelevantes, o que facilita o estudo de arpejos e a memorização fotográfica dos *shapes*.

### 🚀 Funcionalidades Principais
* **Braço Interativo Dinâmico:** Suporte nativo para Guitarra (6 e 7 cordas) e Baixo (4 cordas), com recálculo automático de espaçamento e dezenas de afinações abertas disponíveis.
* **Campo Harmônico Inteligente:** Visualização em tempo real dos 7 graus da escala em algarismos romanos, respondendo diretamente à tônica selecionada.
* **Filtro de Acordes (CAGED):** Destaque seletivo das tríades, com cálculo instantâneo de intervalos Maiores, Menores e Diminutos.
* **Interface Modular com Flexbox Customizado:** Menus de escalas e configurações com sistema próprio de barra de rolagem (scroll) e *clipping* de renderização, permitindo uma UI limpa e moderna.
* **Processamento de Áudio (IA e DSP):** Detecção contínua de frequência via microfone com destaque visual de afinação (*Pitch detection*).
* **Mini-Jogos de Percepção e Precisão:** Módulos de gamificação interativos (como o "Acerte a Nota") que avaliam a precisão rítmica e de afinação do usuário em tempo real, utilizando a captação do microfone.
* **Personalização Total:** Ajuste em tempo real de opacidade das notas, cores do braço/fundo e tipografia do sistema, refletindo as alterações sem atraso de quadros.

### 🛠️ Como Executar o Projeto

#### 🔹 Opção A: Via Código-Fonte e VS Code (Desenvolvimento)
Para rodar o software diretamente do código e fazer suas próprias modificações:

1. **Pré-requisitos:** Certifique-se de ter o **Python 3.10 ou superior** e o `git` instalados no seu sistema.
2. **Clone o repositório oficial:**
   ```bash
   git clone [https://github.com/SEU_USUARIO/EIGUIT.git](https://github.com/SEU_USUARIO/EIGUIT.git)
   cd EIGUIT



3. **Crie e ative um ambiente virtual (VENV):**
```bash
# Criação do ambiente
python -m venv venv_novo

# Ativação no Windows (PowerShell/CMD)
.\venv_novo\Scripts\activate

# Ativação no Linux / macOS (Terminal)
source venv_novo/bin/activate

```


4. **Instale as dependências rigorosas:**
```bash
pip install pygame-ce pyaudio numpy librosa sounddevice

```


5. **Execute a aplicação:**
Abra a pasta clonada no VS Code, abra o arquivo `main.py` e pressione `F5`, ou execute diretamente no terminal ativado:
```bash
python main.py

```



#### 🔹 Opção B: Via Executável (.EXE Standalone)

Caso queira apenas testar a ferramenta no Windows sem configurar o Python:

1. Navegue até a aba **Releases** no lado direito deste repositório GitHub.
2. Baixe o arquivo `.zip` da versão mais recente.
3. Extraia todo o conteúdo para uma pasta dedicada no seu computador.
4. **Importante:** Mantenha a pasta `assets` e a pasta `Audios` (com os arquivos `.wav`) no mesmo diretório do executável `main.exe`.
5. Dê um duplo clique em **`main.exe`**.
* *Aviso do Windows:* Por ser um executável compilado de forma independente (sem assinatura digital paga), o Windows SmartScreen pode bloqueá-lo inicialmente. Clique em *"Mais informações"* e, em seguida, em *"Executar assim mesmo"*.



### 🎮 Guia de Uso Rápido e Atalhos

1. **Seleção de Instrumento:** Utilize os botões azuis na barra de ferramentas superior para alternar instantaneamente entre Guitarra e Baixo. A interface se redimensionará sozinha.
2. **Sistema CAGED:** Role até a aba "Campo Harmônico". Clique em qualquer um dos blocos azuis (I, II, III...). O software isolará as notas da tríade correspondente no braço, aplicando transparência ao restante da escala. Clique novamente para desmarcar.
3. **Navegação (Scroll):** Posicione o mouse sobre o painel inferior (Escalas, Acordes, Configurações) e use a rodinha do mouse (*scroll wheel*) para subir ou descer pelas opções.
4. **Gamificação (Modo Jogos):** Na seção inferior, acesse a área de Análise por IA e abra os **Mini-Jogos**. O jogo "Acerte a Nota" exige que você toque fisicamente a nota exigida na tela usando sua guitarra. O sistema julgará sua precisão rítmica e de afinação.
5. **Treinamento Rítmico:** O metrônomo pode ser acionado de forma miniaturalizada no canto inferior direito, ou configurado profundamente na aba "Configurações".
6. **Graus vs Letras:** Em "Configurações", altere a exibição das notas de "C D E" (Letras) para "1 2 3" (Graus) para focar na visualização de intervalos em vez do nome absoluto da nota.

---

## 🇺🇸 English

### ⚠️ Project Status: Beta Version

This project is currently in its **Beta** phase. While the core musical mathematics, fretboard rendering, and audio processing pipelines are fully operational, the software is continually undergoing visual refinements, minor UI glitch corrections, and performance optimizations.

**Contributors Wanted!** This project has significant expansion potential. Your support is highly appreciated in areas such as:

* **Design (UI/UX):** Enhancing the graphical interface, responsiveness, and overall user flow.
* **Development (Python):** Optimizing Pygame rendering performance and integrating new analytical and gamification modules.
* **Music Theory:** Expanding the mathematical engine to support tetrads (7th chords), exotic scales, and strobe tuning systems.
* **QA / Testing:** Reporting bugs and submitting PRs to improve application stability.

### 📝 About the Project

**Guitar Studio IA** is an advanced interactive tool designed for guitarists, bassists, music theory students, and producers. Developed entirely in Python using the Pygame library for rendering and vector processing, the software provides a dynamic, real-time visualization of the instrument's fretboard coupled with deep harmonic field analysis.

The technological and educational centerpiece of this project is the **Automatic CAGED Filter System**. By selecting a dynamically generated chord within a given harmonic field (Ionian, Dorian, Phrygian, etc.), the software instantly maps the triad notes (Root, Third, Fifth) across the entire fretboard. It applies smart Alpha blending transparency to irrelevant notes, drastically simplifying arpeggio study and the photographic memorization of shape patterns.

### 🚀 Key Features

* **Dynamic Interactive Fretboard:** Native rendering for Guitar (6 & 7 strings) and Bass (4 strings), with automatic spacing recalculation and dozens of built-in open tunings.
* **Smart Harmonic Field:** Real-time visualization of the 7 scale degrees in Roman numerals, reacting instantly to the selected root note.
* **CAGED Chord Filter:** Selective highlighting of triads with instant on-the-fly calculation of Major, Minor, and Diminished intervals.
* **Custom Modular UI:** Settings and scale menus utilize a custom flexbox-like logic with an independent scrollbar and clipping masks, delivering a clean and modern interface.
* **Audio Processing (DSP & AI):** Continuous real-time frequency detection via microphone with visual pitch feedback logic.
* **Gamification & Accuracy Mini-Games:** Interactive modules (such as "Hit the Note") that evaluate the user's rhythmic and pitch accuracy in real-time using microphone input.
* **Total Customization:** Adjust note opacity, fretboard wood color, and system typography in real-time without frame lag.

### 🛠️ How to Run the Project

#### 🔹 Option A: Via Source Code and VS Code (Development)

To run the software directly from the source and make your own modifications:

1. **Prerequisites:** Ensure you have **Python 3.10 or higher** and `git` installed on your system.
2. **Clone the official repository:**
```bash
git clone [https://github.com/YOUR_USER/EIGUIT.git](https://github.com/YOUR_USER/EIGUIT.git)
cd EIGUIT

```


3. **Create and activate a virtual environment (VENV):**
```bash
# Creation
python -m venv venv_novo

# Windows Activation (PowerShell/CMD)
.\venv_novo\Scripts\activate

# Linux / macOS Activation (Terminal)
source venv_novo/bin/activate

```


4. **Install strict dependencies:**
```bash
pip install pygame-ce pyaudio numpy librosa sounddevice

```


5. **Run the application:**
Open the cloned folder in VS Code, open `main.py`, and press `F5`, or run directly in the activated terminal:
```bash
python main.py

```



#### 🔹 Option B: Via Standalone Executable (.EXE)

If you just want to test the tool on Windows without dealing with Python configurations:

1. Navigate to the **Releases** tab on the right side of this GitHub repository.
2. Download the latest version's `.zip` file.
3. Extract all contents to a dedicated folder on your computer.
4. **Crucial:** Ensure the `assets` and `Audios` folders (with the `.wav` files) remain in the same directory as `main.exe`.
5. Double-click **`main.exe`**.
* *Windows Warning:* Because this is an independently compiled executable (without a paid digital signature), Windows SmartScreen might block it initially. Click *"More info"* and then *"Run anyway"*.



### 🎮 Quick Start Guide & Workflow

1. **Instrument Selection:** Use the blue buttons on the top toolbar to switch instantly between Guitar and Bass. The UI will resize and recalculate automatically.
2. **CAGED System:** Scroll down to the "Harmonic Field" tab. Click on any of the blue degree blocks (I, II, III...). The software will isolate the corresponding triad notes on the neck, turning the rest of the scale transparent. Click it again to deselect.
3. **Scroll Navigation:** Hover your mouse over the bottom panel area (Scales, Chords, Settings) and use the mouse wheel to scroll through options smoothly.
4. **Gamification (Game Mode):** In the bottom section, access the AI Analysis area and open the **Mini-Games**. The "Hit the Note" game requires you to physically play the requested note on your instrument. The system will judge your timing and pitch accuracy in real-time.
5. **Rhythm Training:** The metronome can be toggled via the miniature widget in the bottom right corner or configured in-depth within the "Settings" tab.
6. **Degrees vs Letters:** In "Settings", change the text display mode from "C D E" (Letters) to "1 2 3" (Degrees) to focus strictly on interval visualization rather than absolute pitch names.

---

## 📂 Arquitetura e Estrutura de Arquivos / System Architecture & File Structure

A base de código foi inteiramente refatorada para seguir padrões modernos de Orientação a Objetos e Separação de Preocupações (Separation of Concerns).

```text
EIGUIT/
├── main.py                     # Entry point / Loop principal do motor (60 FPS)
├── estado_app.py               # Singleton de gestão de estado (Global State variables)
├── renderizador_ui.py          # View Engine / Responsável pelos draw calls do Pygame
├── controlador_eventos.py      # Input Handler / Lógica de Mouse e Keyboard events
├── config.py                   # Persistência de preferências do usuário / Flexbox UI config
├── fabrica_escalas.py          # Lógica geracional estrutural de dicionários (Modos Gregos)
├── Jogos/                      # Módulo de Gamificação
│   ├── Jogos_interativos.py    # Gerenciador de transições e UI dos jogos
│   └── acerte_a_nota.py        # Core logic do mini-jogo de precisão musical
├── Modulos/                    # Módulos encapsulados (Features)
│   ├── modulo_campo_harmonico.py   # Cálculos de matemática intervalar e renderização do CAGED
│   ├── modulo_metronomo.py         # Threading e temporização precisa de áudio (BPM)
│   └── modulo_processamento.py     # Captura de áudio, DSP e análise Fast Fourier Transform
├── Audios/                     # Banco de timbres sintetizados e gravações do projeto
└── assets/                     # Pasta local contendo recursos estáticos (Imagens/Ícones)

```

```

```
