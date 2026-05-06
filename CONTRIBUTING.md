# 🤝 Como Contribuir para o EIGUIT (Guitar Studio IA)

Primeiramente, muito obrigado pelo seu interesse em contribuir com o **Guitar Studio IA**! Este projeto está em fase Beta e a ajuda da comunidade é fundamental para expandir suas capacidades didáticas e tecnológicas.

Antes de enviar o seu *Pull Request* (PR), por favor, leia atentamente as regras e diretrizes abaixo. Elas garantem que o projeto mantenha sua organização modular e respeite os termos de licença originais.

---

## ⚖️ 1. A Regra de Ouro (Licença e Direitos Autorais)
Este projeto possui uma licença restrita de **Copyright Reservado**. Ao contribuir com o seu código para este repositório, você concorda que:
* Suas contribuições farão parte de um projeto voltado **exclusivamente para fins educacionais e de estudo**.
* Você **não pode** utilizar o código base ou suas próprias modificações para criar produtos derivados com fins lucrativos ou comerciais.
* Todo o código mesclado (*merged*) no branch `main` respeitará as regras de uso não-comercial estabelecidas no arquivo `LICENSE`.

## 🏗️ 2. Padrões de Código e Arquitetura
Nosso software foi refatorado para seguir uma arquitetura modular rígida. Para que seu PR seja aceito, siga estas regras:

* **Mantenha a Modularidade:** Não adicione lógicas pesadas no `main.py`. O arquivo principal serve apenas para inicialização e controle do loop (60 FPS).
* **Gestão de Estado:** Qualquer nova variável global ou configuração deve ser adicionada no arquivo `estado_app.py` ou `config.py`.
* **Idioma do Código:** As variáveis, funções e classes devem ser escritas em **Português**, seguindo o padrão `snake_case` para variáveis/funções (ex: `meu_campo_harmonico`) e `PascalCase` para classes (ex: `CampoHarmonico`).
* **Performance Gráfica (Pygame):** Evite criar novas `Surfaces` dentro de loops de renderização (`for` ou `while`), a menos que seja estritamente necessário (como o uso de `SRCALPHA` para a transparência do sistema CAGED). Renderize com eficiência para evitar quedas de FPS.
* **Interface (UI):** Qualquer novo painel ou menu deve respeitar o sistema customizado de *Scroll* (rolagem) e *Clipping* (máscaras de corte) já implementado no `renderizador_ui.py`.

## 🎸 3. Onde Precisamos de Ajuda (Roadmap Beta)
Sua contribuição é especialmente bem-vinda nestas áreas:
* **UI/UX Design:** Melhoria na estética dos menus, ícones e responsividade geral.
* **Teoria Musical Avançada:** Expansão da fábrica de escalas, adição de tétrades (acordes de sétima: 7M, m7, m7b5) e suporte a escalas exóticas.
* **Otimização Pygame/Áudio:** Melhorias no DSP (processamento digital de sinais) com NumPy e PyAudio para tornar o detector de afinação (Pitch Detection) mais preciso.
* **Treinador Rítmico:** Criação de um módulo de exercícios interativos integrados ao `modulo_metronomo.py`.

## 🚀 4. Passo a Passo para o Pull Request
1. Faça um **Fork** deste repositório.
2. Clone o seu fork para a sua máquina local: `git clone https://github.com/SEU_USUARIO/EIGUIT.git`
3. Crie um branch para a sua modificação: `git checkout -b feature/minha-nova-feature` ou `git checkout -b fix/correcao-bug`
4. Faça suas alterações seguindo os padrões acima.
5. Faça o commit das suas alterações com mensagens claras e descritivas: `git commit -m "Adiciona suporte para acordes de 7ª no Campo Harmônico"`
6. Faça o push para o seu branch: `git push origin feature/minha-nova-feature`
7. Abra um **Pull Request** detalhando o que foi alterado, o motivo da mudança e se testou as alterações (com e sem áudio ativado).

---
*Estamos ansiosos para ver o que podemos construir juntos para a comunidade de músicos!*