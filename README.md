# 🎸 Guitar Studio IA - Virtual Fretboard & Harmonic Field

<div align="center">
  <img src="https://github.com/user-attachments/assets/b2bbfc5d-4f0e-469d-8c6d-feff0a189fe9" width="800" alt="Guitar Studio IA Main Interface">
  
 

</div>

---

## 🇧🇷 Português

### 📝 Sobre o Projeto
O **Guitar Studio IA** é uma ferramenta interativa avançada para guitarristas, baixistas e estudantes de música. Desenvolvido em Python com a biblioteca Pygame, o software oferece uma visualização dinâmica do braço do instrumento (guitarra e baixo), mapeamento de escalas, análise de campo harmônico e integração com processamento de áudio em tempo real.

O diferencial deste projeto é o sistema de **Filtro CAGED Automático**, onde a seleção de um acorde no campo harmônico destaca instantaneamente suas tríades por todo o braço, facilitando o estudo de arpejos e memorização de formas.

### 🚀 Funcionalidades Atuais
* **Braço Dinâmico:** Suporte para Guitarra (6 e 7 cordas) e Baixo (4 cordas) com alteração de afinação em tempo real.
* **Campo Harmônico Integrado:** Visualização dos 7 graus da escala em algarismos romanos.
* **Filtro de Acordes (CAGED):** Destaque de tônica, terça e quinta de qualquer acorde selecionado, com transparência ajustável para notas fora da tríade.
* **Interface Modular (UI Flexbox):** Painéis de escalas, acordes e configurações com sistema de rolagem (scroll) independente.
* **Processamento de Áudio:** Detecção de frequência via microfone para feedback visual de afinação.
* **Customização Total:** Alteração de cores do braço, transparência das notas e fontes do sistema.

### 🛠️ Como Funciona
O software utiliza uma arquitetura modular baseada em estados:
1.  **Estado Global (`estado_app.py`):** Gerencia a memória central do aplicativo.
2.  **Módulos de Desenho (`renderizador_ui.py`):** Lida com o ciclo de renderização e clipping (máscaras de corte) para a interface.
3.  **Lógica Musical (`modulo_campo_harmonico.py`):** Cálculos matemáticos de intervalos musicais e formação de acordes.
4.  **Fábrica de Escalas:** Sistema que gera dinamicamente os objetos de shapes para cada modo grego.

### 🔮 Adições Futuras
- [ ] **Treinador de Ritmo:** Exercícios interativos com metrônomo visual.
- [ ] **Análise de IA Avançada:** Sugestão de escalas sobre progressões de acordes carregadas.
- [ ] **Exportação MIDI:** Gravação das notas tocadas diretamente para arquivos MIDI.
- [ ] **Dicionário de Tétrades:** Expansão das tríades para acordes de sétima (7, 7M, m7, m7b5).

---

## 🇺🇸 English

### 📝 About the Project
**Guitar Studio IA** is an advanced interactive tool for guitarists, bassists, and music students. Built in Python using Pygame, the software provides a dynamic visualization of the instrument's fretboard, scale mapping, harmonic field analysis, and real-time audio processing integration.

The project's highlight is the **Automatic CAGED Filter**, where selecting a chord in the harmonic field instantly highlights its triads across the entire fretboard, simplifying the study of arpeggios and shapes.

### 🚀 Key Features
* **Dynamic Fretboard:** Supports Guitar (6 & 7 strings) and Bass (4 strings) with real-time tuning changes.
* **Integrated Harmonic Field:** Visualization of the 7 scale degrees in Roman numerals.
* **Chord Filter (CAGED System):** Highlighting the root, third, and fifth of any selected chord, with adjustable transparency for notes outside the triad.
* **Modular UI:** Scrollable panels for scales, chords, and settings using a custom flexbox-like logic.
* **Audio Processing:** Real-time frequency detection via microphone for pitch feedback.
* **Full Customization:** Change fretboard colors, note transparency, and system fonts.

### 🛠️ How It Works
The software uses a state-driven modular architecture:
1.  **Global State (`estado_app.py`):** Manages the core application memory.
2.  **Render Engine (`renderizador_ui.py`):** Handles the frame cycle and clipping masks for the UI.
3.  **Musical Logic (`modulo_campo_harmonico.py`):** Mathematical calculations of musical intervals and chord formation.
4.  **Scale Factory:** Dynamically generates shape objects for each Greek mode.

### 🔮 Future Roadmap
- [ ] **Rhythm Trainer:** Interactive exercises with a visual metronome.
- [ ] **Advanced AI Analysis:** AI-powered scale suggestions over loaded chord progressions.
- [ ] **MIDI Export:** Record notes played directly into MIDI files.
- [ ] **7th Chord Expansion:** Expanding triads to include four-note chords (maj7, min7, dom7, m7b5).

---

## 📂 Estrutura de Arquivos / File Structure
```text
├── main.py                 # Ponto de entrada / Entry point
├── estado_app.py           # Gestão de estado / State management
├── renderizador_ui.py      # Motor gráfico / Graphics engine
├── controlador_eventos.py  # Input do usuário / Input handling
├── config.py               # Configurações do usuário / User settings
├── Modulos/
│   ├── modulo_campo_harmonico.py   # Lógica de acordes / Chord logic
│   ├── modulo_metronomo.py         # Metrônomo / Metronome
│   └── modulo_processamento.py     # Áudio & IA / Audio & AI
└── assets/                 # Imagens e Sons / Images & Sounds
