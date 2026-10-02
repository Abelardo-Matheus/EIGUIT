# -*- coding: utf-8 -*-
"""
Base comum das pedaleiras integradas ao Analisador IA.

Cada pedaleira e um "driver" que sabe:
    - ler e gravar o arquivo de preset que o software da pedaleira exporta;
    - (opcional) ler e gravar o arquivo de EQ global;
    - descrever o preset em modulos/parametros legiveis (para conferir na tela);
    - traduzir as sugestoes do Analisador em mudancas nesse preset.

O Analisador so conversa com esta interface; para integrar outra pedaleira
basta criar um pacote em pedaleiras/<id>/ com uma subclasse de
DriverPedaleira e registra-la em pedaleiras/registro.py.

Estruturas usadas pela tela (todas dicionarios simples):
    modulo   = {'id', 'nome', 'ligado', 'modelo', 'modelo_nome', 'params': [param, ...]}
    param    = {'indice', 'nome', 'valor', 'texto'}
    mudanca  = {'chave', 'modulo', 'campo', 'antes', 'depois', 'texto_antes', 'texto_depois',
                'motivo', 'origem', 'aplicar'}
"""
import copy


class ErroFormato(ValueError):
    """Arquivo que nao e do formato esperado pela pedaleira."""


class DriverPedaleira:
    id = ''
    nome = ''
    fabricante = ''
    implementado = False
    software = ''                         # programa oficial que importa/exporta os arquivos
    ext_preset = ''                       # ex.: '.dzh'
    ext_eq_global = ''                    # '' = sem EQ global por arquivo
    observacao = ''

    # ------------------------------------------------------------- arquivos
    def ler_preset(self, caminho):
        raise NotImplementedError

    def salvar_preset(self, preset, caminho):
        raise NotImplementedError

    def ler_eq_global(self, caminho):
        raise NotImplementedError

    def salvar_eq_global(self, eq, caminho):
        raise NotImplementedError

    # ------------------------------------------------------------- leitura
    def descrever_preset(self, preset):
        """Lista de modulos (na ordem da cadeia) para a tela."""
        raise NotImplementedError

    def descrever_eq_global(self, eq):
        """Lista de param (mesmo formato dos modulos) do EQ global."""
        return []

    def comparar(self, a, b):
        """Diferencas campo a campo entre dois presets (para conferir a importacao)."""
        raise NotImplementedError

    # ------------------------------------------------------------- analisador
    def planejar(self, preset, sugestoes, eq_global=None, opcoes=None):
        """
            Traduz as sugestoes do Analisador em uma lista de mudancas
            (nada e alterado ainda). Cada mudanca pode ser desmarcada na tela.
        """
        raise NotImplementedError

    def aplicar(self, preset, mudancas, eq_global=None):
        """Devolve (preset_novo, eq_global_novo) com as mudancas marcadas."""
        raise NotImplementedError

    # ------------------------------------------------------------- util
    def info(self):
        return {'id': self.id, 'nome': self.nome, 'fabricante': self.fabricante,
                'implementado': self.implementado, 'software': self.software,
                'ext_preset': self.ext_preset, 'ext_eq_global': self.ext_eq_global,
                'observacao': self.observacao}

    @staticmethod
    def copiar(obj):
        return copy.deepcopy(obj)


class PedaleiraPlanejada(DriverPedaleira):
    """Pedaleira listada na tela, mas ainda sem leitor/gravador de arquivo."""

    implementado = False

    def __init__(self, id_, nome, fabricante, software='', ext_preset=''):
        self.id, self.nome, self.fabricante = id_, nome, fabricante
        self.software, self.ext_preset = software, ext_preset
        self.observacao = 'Integração ainda não implementada.'
