import modulos_penta 
import modulos_escala_maior
import modulos_escala_menor
import modulos_teoria_avancada as teoria
import modulos_acordes as acordes
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

    def carregar(chave, matrizes, nomes):
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
            dicionario[chave].append(modulo)
            offset_x_atual += modulo.imagem_painel.get_width() + espaco

    # Fabrica tudo!
    carregar('penta', modulos_penta.TODOS_OS_SHAPES, nomes_shapes)
    carregar('maior', modulos_escala_maior.TODOS_OS_SHAPES, nomes_shapes)
    carregar('menor', modulos_escala_menor.TODOS_OS_SHAPES, nomes_shapes)
    carregar('blues', teoria.TODOS_OS_SHAPES_BLUES, nomes_shapes)
    carregar('modos', teoria.TODOS_OS_MODOS, nomes_modos)
    carregar('triades_maior', acordes.TODOS_AS_TRIADES_MAIORES, nomes_acordes_maiores)
    carregar('triades_menor', acordes.TODOS_AS_TRIADES_MENORES, nomes_acordes_menores)

    return dicionario