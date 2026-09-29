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
| `teste_blocos.py` | blocos extras: valores, limites e cliques em tres tamanhos, mais o gaveteiro lateral |
| `auditoria.py` | contraste, alvos da barra superior e regioes vazias |
| `preview2/3/ritmo.py` | geram os PNGs de `_preview_design/` nos dois temas |
| `preview_pedais.py` | PNGs do estudo de pedais (lista, pedais abertos, 720p e a sub-aba) |

O `teste_blocos.py` cobre tambem a coluna lateral: tudo comeca guardado, a
coluna abre no hover, a gaveta tira e guarda o bloco por clique e por arrasto,
largar em cima da coluna guarda de volta, e um bloco guardado nao deixa alvo
de clique para tras.

O `teste_blocos.py` prova que nenhum bloco pinta fora do proprio retangulo:
desenha o bloco duas vezes, uma com conteudo e outra so com a moldura, e
compara pixel a pixel tudo o que esta fora dele.
