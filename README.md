
<div align="center">
  <img src="URL_DA_SUA_LOGO_AQUI" width="120" alt="Guitar Studio IA Logo">
  
  <h1>🎸 Guitar Studio IA</h1>
  <p><i>Virtual Fretboard, Harmonic Field Engine & Audio Processing</i></p>
  
  <img src="https://github.com/user-attachments/assets/b2bbfc5d-4f0e-469d-8c6d-feff0a189fe9" width="800" alt="Guitar Studio IA Main Interface">

  <br><br>

  <p>
    <img src="https://img.shields.io/badge/Status-Beta_0.8.2-orange?style=for-the-badge" alt="Version Beta">
    <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python Version">
    <img src="https://img.shields.io/badge/Platform-Windows_|_Linux_|_macOS-lightgrey?style=for-the-badge" alt="Platforms">
    <img src="https://img.shields.io/badge/License-Copyright_Reserved-red?style=for-the-badge" alt="License">
  </p>
</div>

---

## 🇧🇷 Português

### ⚠️ Status do Projeto: Versão Beta
Este projeto está atualmente em sua fase **Beta**. Embora a lógica musical matemática, a renderização do braço e os cálculos de processamento de áudio estejam operacionais, o software ainda passa por constantes refinamentos visuais, correção de pequenos *glitches* de interface e otimizações de performance.

**Procuramos Colaboradores!** O projeto tem grande potencial de expansão. Seu apoio é muito bem-vindo para:
* **Design (UI/UX):** Melhorar a interface gráfica, responsividade e experiência do usuário.
* **Desenvolvimento (Python):** Otimização de performance de renderização do Pygame e integração de novos módulos analíticos.
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
* **Personalização Total:** Ajuste em tempo real de opacidade das notas, cores do braço/fundo e tipografia do sistema, refletindo as alterações sem atraso de quadros.

### 🛠️ Como Executar o Projeto

#### 🔹 Opção A: Via Código-Fonte e VS Code (Desenvolvimento)
Para rodar o software diretamente do código e fazer suas próprias modificações:

1. **Pré-requisitos:** Certifique-se de ter o **Python 3.10 ou superior** e o `git` instalados no seu sistema.
2. **Clone o repositório oficial:**
   ```bash
   git clone [https://github.com/SEU_USUARIO/EIGUIT.git](https://github.com/SEU_USUARIO/EIGUIT.git)
   cd EIGUIT
   ```
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
   pip install pygame-ce pyaudio numpy
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
4. **Importante:** Mantenha a pasta `assets` e quaisquer arquivos `.wav` (como `tick.wav`) no mesmo diretório do executável `main.exe`.
5. Dê um duplo clique em **`main.exe`**.
   * *Aviso do Windows:* Por ser um executável compilado de forma independente (sem assinatura digital paga), o Windows SmartScreen pode bloqueá-lo inicialmente. Clique em *"Mais informações"* e, em seguida, em *"Executar assim mesmo"*.

### 🎮 Guia de Uso Rápido e Atalhos
1. **Seleção de Instrumento:** Utilize os botões azuis na barra de ferramentas superior para alternar instantaneamente entre Guitarra e Baixo. A interface se redimensionará sozinha.
2. **Sistema CAGED:** Role até a aba "Campo Harmônico". Clique em qualquer um dos blocos azuis (I, II, III...). O software isolará as notas da tríade correspondente no braço, aplicando transparência ao restante da escala. Clique novamente para desmarcar.
3. **Navegação (Scroll):** Posicione o mouse sobre o painel inferior (Escalas, Acordes, Configurações) e use a rodinha do mouse (*scroll wheel*) para subir ou descer pelas opções.
4. **Treinamento Rítmico:** O metrônomo pode ser acionado de forma miniaturalizada no canto inferior direito, ou configurado profundamente na aba "Configurações".
5. **Graus vs Letras:** Em "Configurações", altere a exibição das notas de "C D E" (Letras) para "1 2 3" (Graus) para focar na visualização de intervalos em vez do nome absoluto da nota.

---

## 🇺🇸 English

### ⚠️ Project Status: Beta Version
This project is currently in its **Beta** phase. While the core musical mathematics, fretboard rendering, and audio processing pipelines are fully operational, the software is continually undergoing visual refinements, minor UI glitch corrections, and performance optimizations.

**Contributors Wanted!** This project has significant expansion potential. Your support is highly appreciated in areas such as:
* **Design (UI/UX):** Enhancing the graphical interface, responsiveness, and overall user flow.
* **Development (Python):** Optimizing Pygame rendering performance and integrating new analytical modules.
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
   pip install pygame-ce pyaudio numpy
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
4. **Crucial:** Ensure the `assets` folder and any `.wav` files (like `tick.wav`) remain in the same directory as `main.exe`.
5. Double-click **`main.exe`**.
   * *Windows Warning:* Because this is an independently compiled executable (without a paid digital signature), Windows SmartScreen might block it initially. Click *"More info"* and then *"Run anyway"*.

### 🎮 Quick Start Guide & Workflow
1. **Instrument Selection:** Use the blue buttons on the top toolbar to switch instantly between Guitar and Bass. The UI will resize and recalculate automatically.
2. **CAGED System:** Scroll down to the "Harmonic Field" tab. Click on any of the blue degree blocks (I, II, III...). The software will isolate the corresponding triad notes on the neck, turning the rest of the scale transparent. Click it again to deselect.
3. **Scroll Navigation:** Hover your mouse over the bottom panel area (Scales, Chords, Settings) and use the mouse wheel to scroll through options smoothly.
4. **Rhythm Training:** The metronome can be toggled via the miniature widget in the bottom right corner or configured in-depth within the "Settings" tab.
5. **Degrees vs Letters:** In "Settings", change the text display mode from "C D E" (Letters) to "1 2 3" (Degrees) to focus strictly on interval visualization rather than absolute pitch names.

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
├── Modulos/                    # Módulos encapsulados (Features)
│   ├── modulo_campo_harmonico.py   # Cálculos de matemática intervalar e renderização do CAGED
│   ├── modulo_metronomo.py         # Threading e temporização precisa de áudio (BPM)
│   └── modulo_processamento.py     # Captura PyAudio, NumPy arrays e análise Fast Fourier Transform
└── assets/                     # Pasta local contendo recursos estáticos (Imagens/Sons)
```

---

## ⚖️ Termos de Uso e Licença Comercial / Terms of Use & Commercial License

**© 2026 Guitar Studio IA - MATHEUS ABELARDO TREVENZOLI ARAUJO Todos os Direitos Reservados / All Rights Reserved.**

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
```
