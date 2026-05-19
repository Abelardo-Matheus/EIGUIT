# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Sistema de Tradução Dinâmica via API com Cache Local e Threading
# =============================================================================

import builtins
import json
import os
import threading
import queue
try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

CACHE_FILE = "translation_cache.json"

class TradutorDinamico:
    def __init__(self):
        self.idioma_alvo = 'pt' 
        self.cache = self._carregar_cache()
        self.lock = threading.Lock()
        self.tradutor = None
        
        # Fila para processamento em background (evita travar o jogo)
        self.fila_traducoes = queue.Queue()
        self.em_processamento = set()
        
        self.atualizar_configuracao('pt')
        
        # Inicia a thread de worker
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def _carregar_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _salvar_cache(self):
        with self.lock:
            try:
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.cache, f, ensure_ascii=False, indent=4)
            except:
                pass

    def atualizar_configuracao(self, novo_idioma):
        """Muda o idioma alvo e reinicia o tradutor."""
        if self.idioma_alvo == novo_idioma:
            return
            
        self.idioma_alvo = novo_idioma
        if novo_idioma != 'pt' and GoogleTranslator:
            self.tradutor = GoogleTranslator(source='pt', target=novo_idioma)
        else:
            self.tradutor = None
        
        print(f"[I18N] Idioma alterado para: {novo_idioma}")

    def traduzir(self, texto):
        if not texto or self.idioma_alvo == 'pt' or not GoogleTranslator:
            return texto

        chave = f"{self.idioma_alvo}:{texto}"
        
        # 1. Verifica Cache (Rápido)
        with self.lock:
            if chave in self.cache:
                return self.cache[chave]

        # 2. Se não estiver no cache, coloca na fila para traduzir em background
        if chave not in self.em_processamento:
            self.em_processamento.add(chave)
            self.fila_traducoes.put((self.idioma_alvo, texto, chave))
            
        # Retorna o texto original enquanto a tradução não chega
        return texto

    def _worker_loop(self):
        """Loop que roda em outra CPU thread, sem travar o Pygame."""
        while True:
            try:
                idioma, texto, chave = self.fila_traducoes.get()
                
                # Cria um tradutor local para a thread se necessário
                temp_translator = GoogleTranslator(source='pt', target=idioma)
                
                try:
                    traducao = temp_translator.translate(texto)
                    with self.lock:
                        self.cache[chave] = traducao
                    self._salvar_cache()
                except Exception as e:
                    print(f"[I18N Worker] Erro: {e}")
                
                self.fila_traducoes.task_done()
                # Remove do set de processamento após terminar (sucesso ou erro)
                # self.em_processamento.remove(chave) # Removido para evitar spam se der erro constante
            except Exception as e:
                print(f"[I18N Critical] Worker crash: {e}")

# Inicializa o tradutor global
sistema_traducao = TradutorDinamico()

def _t(texto):
    """Função global de tradução."""
    return sistema_traducao.traduzir(texto)

# Injeta no builtins para que todos os arquivos vejam
builtins._t = _t
