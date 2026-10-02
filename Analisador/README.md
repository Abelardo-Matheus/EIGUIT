# Analisador IA (set/2026)

Nova sub-aba **ANÁLISE DE IA > Analisador** (cartão "Analisador IA", abre em tela cheia pelo `GerenciadorEstudos`).

O usuário toca por cima de uma música com a pedaleira e recebe uma comparação do **timbre** do preset com o da guitarra (ou baixo/violão) da música: ganho, EQ, compressão, modulação, ambiência e os 20 efeitos do estudo de Pedais. Não confere notas. Tudo roda localmente, sem chave de API: a única rede é a pesquisa/download opcional de áudio (yt-dlp).

## Fluxo (assistente em 5 etapas)

1. **Áudio**: entrada (pedaleira) e canal processado, canal DI opcional, saída, taxa, buffer, medidor com clip/sinal fraco, monitoramento e calibração de latência (loopback ou "tocar junto"). A latência fica salva por par entrada|saída.
2. **Instrumento**: guitarra / violão / baixo, captador, afinação e a calibração opcional de 15 s de som limpo (timbre base).
3. **Música**: busca na pasta de referências e nas partituras do EIGUIT, importar arquivo (MP3/WAV/FLAC/OGG, também por arrastar), pesquisa online opcional, tipo (isolado/mix/separado), separação com Demucs opcional, seleção do trecho na forma de onda, BPM e compassos do MIDI (o MIDI só dá estrutura; o timbre vem sempre do áudio).
4. **Gravação**: contagem, metrônomo, repetições; toca o trecho e grava o(s) canal(is) da pedaleira ao mesmo tempo; takes com validação (silêncio, clipping, curto, música vazando na entrada).
5. **Resultado**: índice geral e por categoria, sugestões Falta/Sobra/Ajuste/Timbre base (com "Abrir pedal" em ESTUDOS > Pedais já com os valores), gráficos (espectro médio, envelope, decaimento), A/B com volume igualado (tecla A), medidas, histórico por música, preset sugerido (Fase 2), detector local (Fase 3) e exportação (Markdown + PDF).

## Arquivos

| arquivo | o que faz |
| --- | --- |
| `Analisador/analisador_ia.py` | tela (5 etapas + resultado); tarefas longas em thread com progresso e Cancelar |
| `audio/dispositivos.py` | listar/validar dispositivos, `ConfigAudio`, medidor e monitor, calibração de latência |
| `audio/gravacao_playalong.py` | playback + gravação sincronizados (duplex ou dois streams), takes, validação, `ReprodutorAB`, `BackendSimulado` para os testes |
| `audio/referencia.py` | biblioteca/índice, importar, yt-dlp, Demucs, BPM, forma de onda, compassos do MIDI, `TarefaFundo` |
| `audio/analise_timbre.py` | pré-processamento (mono, 32 kHz, sem DC), LUFS BS.1770, ataques (SuperFlux), alinhamento, YIN, `AnaliseSinal`, perfil de timbre |
| `audio/detectores_efeitos.py` | um detector por efeito (regras de DSP) + interações entre efeitos |
| `audio/sugestoes_timbre.py` | comparação, índices, regras de sugestão, relatório, histórico, `analisar()` |
| `audio/config_analise/*.json` | bandas, faixas e **todos os limiares** (`_padrao.json` + um arquivo por instrumento) |
| `audio/cadeia_pedais.py` | Fase 2: análise por síntese (busca da cadeia e dos knobs no som limpo) |
| `audio/treinar_detector.py` | Fase 3: dataset sintético + floresta aleatória (scikit-learn), `reforcar()` |
| `audio/efeitos_pedais.py` | ganhou `aplicar_efeito()` e `renderizar_cadeia()` (áudio linear); o loop do estudo de Pedais não mudou |
| `_validacao/teste_analisador.py` | suíte (21 testes); `preview_analisador.py` gera os PNGs; `sinais_analisador.py` monta os sinais de teste |

Dados do usuário ficam em `%APPDATA%/EIGUIT/analisador/` (configuração, perfis de instrumento, cache de referências, takes, histórico, relatórios).

Dependências opcionais (se faltarem, o botão fica desabilitado com a explicação): `yt-dlp` + ffmpeg (pesquisa/download), `demucs` (separação; também é procurado no `venv_ia` do serviço de transcrição), `scikit-learn` (Fase 3). O restante usa o que o projeto já tem (numpy, scipy, sounddevice, soundfile/librosa só para ler formatos).

## Como adicionar um detector

1. Em `audio/detectores_efeitos.py`, escreva `caracteristicas_<nome>(an)` (use `an._memo` para calcular uma vez só) e a decisão `detectar_<nome>(an, medidas)`, que devolve `_resultado(score, cfg, parametros, motivo)`. Parâmetros estimados usam os mesmos ids do currículo de pedais.
2. Chame o detector em `detectar_todos()`. Se ele imitar ou for imitado por outro efeito, trate isso em `_aplicar_interacoes()`.
3. Coloque os limiares em `audio/config_analise/_padrao.json`, em `detectores.<nome>` (inclua `limiar_sim` e `limiar_nao`). Nenhum número de decisão fica no código.
4. Se for um efeito comparado por presença, acrescente-o em `EFEITOS_PRESENCA`, `CATEGORIA_EFEITO`, `IMPACTO_EFEITO` e `_texto_falta()` (em `audio/sugestoes_timbre.py`).
5. Crie um caso em `CASOS` no `teste_analisador.py` (efeito conhecido → detectado, com tolerância) e confira se o áudio limpo continua sem falso positivo.

## Como adicionar um instrumento

Crie `audio/config_analise/<id>.json` só com o que muda em relação ao `_padrao.json`: `nome`, `faixa_f0`, `faixa_espectro`, `bandas_macro`/`nomes_bandas`, `afinacoes` e, se quiser, limiares próprios em `detectores`. O instrumento aparece sozinho na Etapa 2 (`listar_instrumentos()`). Para a calibração separar guitarra de preset, acrescente `modelo_di_db` (espectro médio de um DI limpo, em dB por banda).

## Limites conhecidos (a interface avisa)

- Reverb e noise gate só são medidos quando o trecho tem pausas; sem elas ficam "incerto".
- Phaser e flanger se confundem: a "varredura" é detectada e o tipo aparece como "possível".
- O ganho é contínuo (índice 0–1); boost/overdrive/distorção/fuzz são faixas desse índice. Delay ou reverb num só dos lados reduzem a confiança do ganho e do sustain.
- A referência inclui amp, gabinete, microfone, mix e master: o objetivo é aproximar, não igualar. Com Demucs, a confiança de ambiência e modulação cai.

## Aba Pedaleira (exportar o ajuste para a pedaleira)

Em **Resultado > Pedaleira** (ou, sem análise, pelo botão "Pedaleira (ver/conferir preset)"):

1. escolha a pedaleira (por enquanto só a M-VAVE MK-300 funciona; as outras aparecem como "em breve");
2. abra o preset exportado pelo M-EFCS (`More > Share current preset`, arquivo `.dzh`) e, se quiser, o EQ global (`EQ > Share EQ`, `.dzheq`);
3. confira as mudanças que a análise gerou (dá para desmarcar cada uma) e o quadro com todos os pedais e parâmetros antes → depois;
4. clique em **Salvar preset ajustado** e importe no M-EFCS (`More > Import current preset`);
5. exporte de novo e clique em **Conferir importação** para ver se ficou tudo igual.

O código fica em `pedaleiras/` (um driver por pedaleira). Detalhes em `pedaleiras/README.md`; a suíte é `_validacao/teste_pedaleiras.py`.
