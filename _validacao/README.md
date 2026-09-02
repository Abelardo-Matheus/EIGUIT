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
| `teste_editor.py` | criacao musical: escrever, andar, exportar |
| `teste_blocos.py` | blocos extras: valores, limites e cliques em tres tamanhos |
| `auditoria.py` | contraste, alvos da barra superior e regioes vazias |
| `preview2/3/ritmo.py` | geram os PNGs de `_preview_design/` nos dois temas |

O `teste_blocos.py` prova que nenhum bloco pinta fora do proprio retangulo:
desenha o bloco duas vezes, uma com conteudo e outra so com a moldura, e
compara pixel a pixel tudo o que esta fora dele.
