# Pedaleiras integradas (Analisador IA > aba Pedaleira)

O Analisador lê o arquivo de preset que o software da pedaleira exporta, mostra todos os pedais e parâmetros, aplica as sugestões da análise e salva um arquivo novo para você importar de volta. Depois dá para exportar de novo e usar **Conferir importação** para comparar campo a campo.

Nada é enviado direto para a pedaleira: tudo passa pelo arquivo.

## MK-300 (M-VAVE, software M-EFCS)

| no M-EFCS | arquivo |
| --- | --- |
| Param > More > **Share current preset** | `.dzh` (448 bytes): preset atual |
| Param > More > **Import current preset** | grava o `.dzh` no slot atual |
| Param > EQ > **Share EQ** / **Import EQ** | `.dzheq` (22 bytes): EQ global |

O layout dos bytes está em `mk300/formato.py`. Os nomes dos módulos, modelos e knobs estão em `mk300/modelos.py`. Tudo foi mapeado exportando o mesmo preset várias vezes no M-EFCS, mudando um knob por vez; os arquivos estão em `_validacao/dados_pedaleiras/mk300/`.

O que a análise muda na MK-300:

| sugestão | onde |
| --- | --- |
| Delay (falta/ajuste/sobra) | DLY: liga/desliga, Time (ms), Fb, Mix; desliga o Sync |
| Reverb | REV: liga/desliga, Decay, Mix |
| Chorus, Flanger, Phaser, Tremolo, Vibrato | MOD: troca o modelo se for de outra família, liga, Speed (e Depth/Mix no Chorus) |
| Mais/menos ganho, falta/sobra de saturação | DS (Gain, liga com um OD/DS/FZ do tipo certo) ou o Gain do AMP |
| EQ (graves/médios/agudos) | EQ do preset (Guitar EQ 6, em passos de 0,5 dB) **ou** o EQ global, à sua escolha |
| Compressor | FX = Compress (Sustain), se o FX estiver livre |
| Noise gate | GATE: liga; se sobra, abaixa o Thd do Hard Gate ou desliga |
| Wah, Octaver, Whammy, Ring | WAH / FX |

Sugestões de baixa confiança aparecem **desmarcadas**: você decide se entram.

Os modelos de DS, AMP e CAB são "slots" da pedaleira. Se você importar outra captura ou IR por cima de um slot (abas Sounds ou Community do M-EFCS), o nome muda lá. Para mudar aqui também, atualize a lista em `mk300/modelos.py`. Importar uma captura grava por cima de um slot da pedaleira, então escolha um slot que você não usa.

Limites conhecidos:

- Os knobs de alguns modelos ainda não têm nome; a tela mostra P1, P2…
- O trecho 0x14A–0x1BF do preset (atribuições de pedal/expressão) é preservado sem mudança.

## Como integrar outra pedaleira

1. Crie `pedaleiras/<id>/driver.py` com uma subclasse de `base.DriverPedaleira` (`implementado = True`). Ela precisa de `ler_preset`, `salvar_preset`, `descrever_preset`, `cabecalho`, `comparar`, `planejar` e `aplicar`. O EQ global é opcional (`ext_eq_global = ''`).
2. Registre a pedaleira em `registro.py`, no lugar da `PedaleiraPlanejada` correspondente.
3. Mapeie o formato do mesmo jeito: exporte arquivos mudando um parâmetro por vez, coloque-os em `_validacao/dados_pedaleiras/<id>/` e escreva os casos em `_validacao/teste_pedaleiras.py`.

A tela (`Analisador/painel_pedaleira.py`) não precisa mudar.

```
python3 _validacao/teste_pedaleiras.py
```
