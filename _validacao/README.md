# Validacao

As suites que rodam antes de qualquer commit. Sem janela e sem placa de som:
os drivers de video e audio sobem em modo dummy, entao tudo isso roda igual em
qualquer maquina, inclusive sem microfone.

    python3 _validacao/smoke2.py
    python3 _validacao/teste_blocos.py
    python3 _validacao/auditoria.py
    ...

| arquivo | o que cobre |
| --- | --- |
| `harness.py` | base comum: sobe o programa, monta o estado e compara quadros |
| `smoke2.py` | workspace inteiro em quatro resolucoes e nos dois temas |
| `teste_responsivo.py` | layout padrao em sete resolucoes |
| `teste_jogos.py` | abertura e quadros dos jogos |
| `teste_audio.py` | frequencia -> nota, motor sem placa de som |
| `teste_acordes.py` | notas e cifras de cada acorde, shapes CAGED, campo harmonico |
| `teste_instrumentos.py` | afinacoes, medidas do braco, bloco de cordas |
| `teste_estudos_novos.py` | todos os estudos abrem e aceitam clique |
| `teste_estudo_notas.py` | partida completa do estudo de notas |
| `teste_ciclo.py` | estudo do ciclo das quintas e a teoria por tras do bloco |
| `teste_pedais.py` | estudo de pedais: cada efeito e cada parametro mudam o som, whammy/delay/gate conferidos pela fisica, loop sem estalo e a tela em tres resolucoes |
| `teste_editor.py` | criacao musical: escrever, andar, exportar |
| `teste_paleta_acordes.py` | paleta de acordes: forma CAGED da soltura, clique liga/desliga, varios acordes com cores distintas, previa e soltura no braco, chip que tira e muda de regiao, foco, arrasto vindo da aba ACORDES, limites do bloco, perfil e o bloco de graus |
| `teste_blocos.py` | blocos extras: valores, limites e cliques em tres tamanhos, mais o gaveteiro lateral |
| `teste_cabecalho.py` | barra superior: todo item de menu tem acao, atalhos (Ctrl+N/O/S/E/Q, F1-F3, F11, F12, zoom), navegacao por teclado, projeto .eiguit (novo/salvar/abrir/formato antigo), exportar txt/MIDI, captura PNG, modais centrados com a camera longe, entrada de audio, idioma, modo de tela, perfil e trocar de conta |
| `teste_preferencias.py` | teclas de atalho (gravar pelo painel, conflito, letra sozinha recusada, Esc/Backspace, padrao, a tecla nova dispara a funcao, abas e metronomo), desempenho (presets, opcao avulsa, efeitos aplicados), perfil com teclas+desempenho+perfil antigo, auto-salvar, zoom do pedaco visivel igual ao da mesa inteira, editor tocando som |
| `auditoria.py` | contraste, alvos da barra superior e regioes vazias |
| `preview2/3/ritmo.py` | geram os PNGs de `_preview_design/` nos dois temas |
| `preview_pedais.py` | PNGs do estudo de pedais (lista, pedais abertos, 720p e a sub-aba) |
| `teste_estudo_tempo.py` | estudo de tempo pelo gerenciador (cartao, sub-aba, clique, loop, ESC, PDF) em tres resolucoes e dois temas, mais o motor da tablatura (modos, instrumentos, botao de som, leitura da celula) |
| `teste_leitor_tempo.py` | leitura ritmica: MIDI -> compassos/tempos/subdivisoes, quialteras, bend, digitacao sugerida, JSON do PDF, soma que nao fecha, audio |
| `teste_analisador.py` | Analisador IA: efeito conhecido -> detectado com parametro na tolerancia (delay +-10%, tremolo/vibrato +-15%), audio limpo sem falso positivo, "Falta: Delay", invariancia a volume, alinhamento com latencia simulada, calibracao, validacao do take, biblioteca/BPM/MIDI, preset sugerido (fase 2), detector treinado (fase 3) e a tela em tres resolucoes e dois temas |
| `preview_analisador.py` | PNGs do Analisador IA (cada etapa, cada aba do resultado, 720p e a sub-aba) |
| `sinais_analisador.py` | guitarras de teste (sintetizada "humana" e sampler DI) com efeitos conhecidos, usadas pelas duas acima e pelo treino local |
| `demo_timbres.py` | gera `_validacao/previews/demo_timbres.wav` com o mesmo riff em cada timbre |

O `teste_blocos.py` cobre tambem a coluna lateral: tudo comeca guardado, a
coluna abre no hover, a gaveta tira e guarda o bloco por clique e por arrasto,
largar em cima da coluna guarda de volta, e um bloco guardado nao deixa alvo
de clique para tras.

O `teste_blocos.py` prova que nenhum bloco pinta fora do proprio retangulo:
desenha o bloco duas vezes, uma com conteudo e outra so com a moldura, e
compara pixel a pixel tudo o que esta fora dele.
