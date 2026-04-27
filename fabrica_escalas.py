import Modulos.modulos_penta as modulos_penta
import Modulos.modulos_escala_maior as modulos_escala_maior
import Modulos.modulos_escala_menor as modulos_escala_menor
import Modulos.modulos_teoria_avancada as teoria
import Modulos.modulos_acordes as acordes

from constantes_ui import BRANCO
from ui_componentes import DesenhoEscala

def gerar_modulos(estado, configs):
    """Gera todas as listas de desenhos e retorna um dicionário organizado"""
    dicionario = {
        'maior': [], 'menor': [], 'penta': [], 'blues': [], 
        'modos': [], 'triades_maior': [], 'triades_menor': []
    }
    
    offset_x_atual = estado.OFFSET_X + 20     
    y_painel = estado.Y_CAIXA + 150 
    espaco = 30 
    
    nomes_shapes = ["Shape 1", "Shape 2", "Shape 3", "Shape 4", "Shape 5", "Completo"]
    nomes_modos = ["Jônico", "Dórico", "Frígio", "Lídio", "Mixolídio", "Eólio", "Lócrio"]
    nomes_acordes_maiores = ["C Major", "A Major", "G Major", "E Major", "D Major"]
    nomes_acordes_menores = ["C Minor", "A Minor", "G Minor", "E Minor", "D Minor"]

    cor_base = configs.get_cor_notas() if configs else BRANCO

    def carregar(chave, matrizes, nomes, aba_origem, sub_aba_origem):
        nonlocal offset_x_atual
        offset_x_atual = estado.OFFSET_X + 20 # Reinicia a linha
        
        for i, padrao in enumerate(matrizes):
            nome_label = nomes[i] if i < len(nomes) else f"Shape {i+1}"
            modulo = DesenhoEscala(
                x_painel=offset_x_atual, y_painel=y_painel, espaco_casas=estado.ESPACO_CASAS,
                espaco_cordas=estado.ESPACO_CORDAS, altura_braco=estado.ALTURA_BRACO, 
                offset_x=estado.OFFSET_X, num_casas_total=estado.NUM_CASAS, 
                padrao=padrao, nome=nome_label, cor_base=cor_base 
            )
            
            # ==========================================
            # --- O CARIMBO (AQUI ESTAVA FALTANDO!) ---
            # ==========================================
            modulo.aba = aba_origem
            modulo.sub_aba = sub_aba_origem
            
            dicionario[chave].append(modulo)
            offset_x_atual += modulo.imagem_painel.get_width() + espaco

    # Fabrica tudo carimbando a Aba e Sub-Aba correta!
    
    # ==========================================
    # ABA 0: ESCALAS 
    # ==========================================
    # Todas têm aba_origem=0. O que muda é a sub_aba (0, 1, 2, 3, 4)
    carregar('maior', modulos_escala_maior.TODOS_OS_SHAPES, nomes_shapes, aba_origem=0, sub_aba_origem=0)
    carregar('menor', modulos_escala_menor.TODOS_OS_SHAPES, nomes_shapes, aba_origem=0, sub_aba_origem=1)
    carregar('penta', modulos_penta.TODOS_OS_SHAPES, nomes_shapes,        aba_origem=0, sub_aba_origem=2)
    carregar('blues', teoria.TODOS_OS_SHAPES_BLUES, nomes_shapes,         aba_origem=0, sub_aba_origem=3)
    carregar('modos', teoria.TODOS_OS_MODOS, nomes_modos,                 aba_origem=0, sub_aba_origem=4)

    # ==========================================
    # ABA 1: ACORDES
    # ==========================================
    # Ambas têm aba_origem=1. O que muda é a sub_aba (0 e 1)
    carregar('triades_maior', acordes.TODOS_AS_TRIADES_MAIORES, nomes_acordes_maiores, aba_origem=1, sub_aba_origem=0)
    carregar('triades_menor', acordes.TODOS_AS_TRIADES_MENORES, nomes_acordes_menores, aba_origem=1, sub_aba_origem=1)

    return dicionario