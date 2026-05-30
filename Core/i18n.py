import builtins
import json
import os
import threading
import queue
try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None
CACHE_FILE = 'translation_cache.json'

class TradutorDinamico:
    """
        Como funciona: Define a estrutura e estado do componente 'TradutorDinamico'.
        Para que serve: Atua como o modelo principal para instâncias de 'TradutorDinamico'.
        Onde é usada: Chamado a partir do módulo ou classe base de 'i18n'.
    """

    def __init__(self):
        """
            Como funciona: Inicializa os atributos e o estado inicial da instância.
            Para que serve: Prepara o objeto para ser utilizado no ciclo de vida da aplicação.
            Onde é usada: Chamado a partir do módulo ou classe base de 'i18n'.
        """
        self.idioma_alvo = 'pt'
        self.cache = self._carregar_cache()
        self.lock = threading.Lock()
        self.tradutor = None
        self.fila_traducoes = queue.Queue()
        self.em_processamento = set()
        self.atualizar_configuracao('pt')
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def _carregar_cache(self):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação ' carregar cache'.
            Para que serve: Realiza as tarefas fundamentais de ' carregar cache' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de ' carregar cache'.
        """
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _salvar_cache(self):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação ' salvar cache'.
            Para que serve: Realiza as tarefas fundamentais de ' salvar cache' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de ' salvar cache'.
        """
        with self.lock:
            try:
                with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.cache, f, ensure_ascii=False, indent=4)
            except:
                pass

    def atualizar_configuracao(self, novo_idioma):
        """
            Como funciona: Recalcula dimensões, estados e processa alterações temporais.
            Para que serve: Garante que os dados e a interface reflitam as últimas mudanças.
            Onde é usada: Chamado a partir do módulo ou classe base de 'i18n'.
        """
        if self.idioma_alvo == novo_idioma:
            return
        self.idioma_alvo = novo_idioma
        if novo_idioma != 'pt' and GoogleTranslator:
            self.tradutor = GoogleTranslator(source='pt', target=novo_idioma)
        else:
            self.tradutor = None
        print(f'[I18N] Idioma alterado para: {novo_idioma}')

    def traduzir(self, texto):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'traduzir'.
            Para que serve: Realiza as tarefas fundamentais de 'traduzir' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'traduzir'.
        """
        if not texto or self.idioma_alvo == 'pt' or (not GoogleTranslator):
            return texto
        chave = f'{self.idioma_alvo}:{texto}'
        with self.lock:
            if chave in self.cache:
                return self.cache[chave]
        if chave not in self.em_processamento:
            self.em_processamento.add(chave)
            self.fila_traducoes.put((self.idioma_alvo, texto, chave))
        return texto

    def _worker_loop(self):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação ' worker loop'.
            Para que serve: Realiza as tarefas fundamentais de ' worker loop' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de ' worker loop'.
        """
        while True:
            try:
                idioma, texto, chave = self.fila_traducoes.get()
                temp_translator = GoogleTranslator(source='pt', target=idioma)
                try:
                    traducao = temp_translator.translate(texto)
                    with self.lock:
                        self.cache[chave] = traducao
                    self._salvar_cache()
                except Exception as e:
                    print(f'[I18N Worker] Erro: {e}')
                self.fila_traducoes.task_done()
            except Exception as e:
                print(f'[I18N Critical] Worker crash: {e}')
sistema_traducao = TradutorDinamico()

def _t(texto):
    """
        Como funciona: Executa o fluxo lógico necessário para a operação ' t'.
        Para que serve: Realiza as tarefas fundamentais de ' t' dentro do contexto do módulo.
        Onde é usada: Utilizado internamente para gerenciar comportamentos de ' t'.
    """
    return sistema_traducao.traduzir(texto)
builtins._t = _t