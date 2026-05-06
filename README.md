<div align="center">
  <img src="URL_DA_SUA_LOGO_AQUI" width="120" alt="Guitar Studio IA Logo">
  <h1>Guitar Studio IA</h1>
  <p><i>Virtual Fretboard & Harmonic Field Engine</i></p>
  
  <img src="https://github.com/user-attachments/assets/b2bbfc5d-4f0e-469d-8c6d-feff0a189fe9" width="800" alt="Guitar Studio IA Main Interface">

  <p>
    <img src="https://img.shields.io/badge/Version-0.8.2--beta-orange" alt="Version Beta">
    <img src="https://img.shields.io/badge/Python-3.10+-blue" alt="Python Version">
    <img src="https://img.shields.io/badge/License-Copyright-red" alt="License">
  </p>
</div>

---

## 🇧🇷 Português

### ⚠️ Status do Projeto: Versão Beta
Este projeto está atualmente em sua fase **Beta**. Isso significa que, embora a lógica musical e as funcionalidades principais estejam operacionais, o software ainda passa por constantes refinamentos de interface e performance.

**Procuramos Colaboradores!** Se você é um desenvolvedor Python, designer de UI/UX ou entusiasta de teoria musical, seu apoio é muito bem-vindo para:
* **Melhorias de Design:** Refinamento da identidade visual e experiência do usuário (UX).
* **Novas Implementações:** Criação de novos módulos e otimização de performance.
* **Reporte de Bugs:** Identificação de falhas técnicas para melhoria da estabilidade.

### 📝 Sobre o Projeto
O **Guitar Studio IA** é uma ferramenta interativa avançada para guitarristas, baixistas e estudantes de música. Desenvolvido em Python com a biblioteca Pygame, o software oferece uma visualização dinâmica do braço do instrumento, mapeamento de escalas e análise de campo harmônico.

O diferencial deste projeto é o sistema de **Filtro CAGED Automático**, onde a seleção de um acorde no campo harmônico destaca instantaneamente suas tríades por todo o braço, facilitando o estudo de arpejos e memorização de formas.

### 🛠️ Como Funciona
O software utiliza uma arquitetura modular baseada em estados:
1. **Estado Global (`estado_app.py`):** Gerencia a memória central e variáveis do aplicativo.
2. **Motor Gráfico (`renderizador_ui.py`):** Lida com o ciclo de renderização e clipping (máscaras de corte).
3. **Lógica Musical (`modulo_campo_harmonico.py`):** Cálculos matemáticos de intervalos e formação de acordes.
4. **Fábrica de Escalas:** Sistema que gera dinamicamente os objetos para cada modo grego.

### 🔮 Adições Futuras
- [ ] **Treinador de Ritmo:** Exercícios interativos com metrônomo visual.
- [ ] **Análise de IA Avançada:** Sugestão de escalas sobre progressões de acordes.
- [ ] **Exportação MIDI:** Gravação direta para arquivos MIDI.
- [ ] **Dicionário de Tétrades:** Expansão para acordes de sétima (7M, m7, etc).

---

## 🛠️ Como Executar / How to Run

### 🔹 Via VS Code (Desenvolvimento / Development)
Para rodar o projeto a partir do código-fonte, siga estes passos:

1. **Pré-requisitos:** Certifique-se de ter o **Python 3.10 ou superior** instalado.
2. **Clone o repositório:**
   ```bash
   git clone [https://github.com/SEU_USUARIO/EIGUIT.git](https://github.com/SEU_USUARIO/EIGUIT.git)
   cd EIGUIT
   
---

## 🇺🇸 English

### ⚠️ Project Status: Beta Version
This project is currently in its **Beta** phase. This means that while the core musical logic and main features are operational, the software is still undergoing constant UI and performance refinements.

**We are Looking for Supporters!** If you are a Python developer, UI/UX designer, or music theory enthusiast, your support is highly appreciated for:
* **Design Improvements:** Refining the visual identity and user experience (UX).
* **New Implementations:** Creating new modules and performance optimization.
* **Bug Reporting:** Identifying technical flaws to improve stability.

### 📝 About the Project
**Guitar Studio IA** is an advanced interactive tool for guitarists, bassists, and music students. Developed in Python with the Pygame library, the software offers a dynamic visualization of the instrument's fretboard, scale mapping, and harmonic field analysis.

The standout feature of this project is the **Automatic CAGED Filter**. Selecting a chord in the harmonic field instantly highlights its triads across the entire fretboard, making it easier to study arpeggios and memorize shapes.

### 🛠️ How It Works
The software uses a state-driven modular architecture:
1. **Global State (`estado_app.py`):** Manages core application memory and variables.
2. **Graphics Engine (`renderizador_ui.py`):** Handles the rendering cycle and clipping masks.
3. **Musical Logic (`modulo_campo_harmonico.py`):** Mathematical calculations of intervals and chord formations.
4. **Scale Factory:** A system that dynamically generates objects for each Greek mode.

### 🔮 Future Roadmap
- [ ] **Rhythm Trainer:** Interactive exercises with a visual metronome.
- [ ] **Advanced AI Analysis:** Scale suggestions over chord progressions.
- [ ] **MIDI Export:** Direct recording to MIDI files.
- [ ] **7th Chord Expansion:** Expanding to include tetrads (maj7, min7, etc).

---

## 📂 Estrutura de Arquivos / File Structure
```text
├── main.py                 # Ponto de entrada / Entry point
├── estado_app.py           # Gestão de estado / State management
├── renderizador_ui.py      # Motor gráfico / Graphics engine
├── controlador_eventos.py  # Input do usuário / Input handling
├── config.py               # Configurações / User settings
├── Modulos/
│   ├── modulo_campo_harmonico.py   # Lógica de acordes / Chord logic
│   ├── modulo_metronomo.py         # Metrônomo / Metronome
│   └── modulo_processamento.py     # Áudio & IA / Audio & AI
└── assets/                 # Imagens e Sons / Images & Sounds
