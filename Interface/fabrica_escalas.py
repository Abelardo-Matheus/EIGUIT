import Modulos.modulos_penta as modulos_penta
import Modulos.modulos_penta_maior as modulos_penta_maior
import Modulos.modulos_escala_maior as modulos_escala_maior
import Modulos.modulos_escala_menor as modulos_escala_menor
import Modulos.modulos_teoria_avancada as teoria
import Modulos.modulos_modos as modos
import Modulos.modulos_harmonica_melodica as harm_melo
import Modulos.modulos_exoticas as exoticas
import Modulos.modulos_acordes as acordes
from Core.constantes_ui import BRANCO
from Interface.ui_componentes import DesenhoEscala
from Interface.Componentes.config_componentes import CARDS_GAP_HORIZONTAL, CARDS_GAP_VERTICAL, CARDS_ESC_LARGURA, CARDS_OFFSET_X_INICIAL, FABRICA_Y_BASE_OFFSET, FABRICA_LARG_UTIL_MARGIN

def gerar_modulos(estado, configs):
    """
        Como funciona: Executa o fluxo lógico necessário para a operação 'gerar modulos'.
        Para que serve: Realiza as tarefas fundamentais de 'gerar modulos' dentro do contexto do módulo.
        Onde é usada: Utilizado internamente para gerenciar comportamentos de 'gerar modulos'.
    """
    dicionario = {'maior': [], 'menor': [], 'penta_maior': [], 'penta_menor': [], 'blues': [], 'modos': [], 'harmonica': [], 'melodica': [], 'exoticas': [], 'caged': [], 'triades_maior': [], 'triades_menor': [], 'setimas': [], 'power': []}
    x_base = estado.dragger_painel_inferior.x if hasattr(estado, 'dragger_painel_inferior') else 100
    largura_max = estado.dragger_painel_inferior.largura if hasattr(estado, 'dragger_painel_inferior') else 1100
    y_base_painel = estado.Y_AREA_DESENHO + FABRICA_Y_BASE_OFFSET
    gap_horizontal = CARDS_GAP_HORIZONTAL
    gap_vertical = CARDS_GAP_VERTICAL
    nomes_shapes = ['Shape 1', 'Shape 2', 'Shape 3', 'Shape 4', 'Shape 5', 'Completo']
    nomes_modos = ['Jônico', 'Dórico', 'Frígio', 'Lídio', 'Mixolídio', 'Eólio', 'Lócrio']
    nomes_acordes_maiores = ['C Major', 'A Major', 'G Major', 'E Major', 'D Major']
    nomes_acordes_menores = ['C Minor', 'A Minor', 'E Minor']
    nomes_setimas = ['C7', 'A7', 'G7', 'E7', 'D7']
    nomes_power = ['C5', 'A5', 'E5']
    cor_base = configs.get_cor_notas() if configs else BRANCO

    def carregar(chave, matrizes, nomes, aba_origem, sub_aba_origem):
        """
            Como funciona: Lê dados de disco, banco de dados ou estado salvo.
            Para que serve: Popula as estruturas em memória com as informações persistidas.
            Onde é usada: Chamado a partir do módulo ou classe base de 'fabrica_escalas'.
        """
        largura_util_painel = largura_max - FABRICA_LARG_UTIL_MARGIN
        largura_coluna = largura_util_painel / 4
        contador_grid = 0
        for i, padrao in enumerate(matrizes):
            nome_label = nomes[i] if i < len(nomes) else f'Shape {i + 1}'
            if nome_label == 'Completo':
                continue
            coluna = contador_grid % 4
            linha = contador_grid // 4
            offset_x_atual = x_base + CARDS_OFFSET_X_INICIAL + coluna * largura_coluna
            offset_y_atual = y_base_painel + linha * gap_vertical
            modulo = DesenhoEscala(x_painel=offset_x_atual, y_painel=offset_y_atual, espaco_casas=estado.ESPACO_CASAS, espaco_cordas=estado.ESPACO_CORDAS, altura_braco=estado.ALTURA_BRACO, offset_x=x_base, num_casas_total=estado.NUM_CASAS, padrao=padrao, nome=nome_label, cor_base=cor_base)
            modulo.y_relativo = offset_y_atual - y_base_painel
            modulo.x_original_relativo = offset_x_atual - x_base
            modulo.aba = aba_origem
            modulo.sub_aba = sub_aba_origem
            dicionario[chave].append(modulo)
            contador_grid += 1
    carregar('maior', modulos_escala_maior.TODOS_OS_SHAPES, nomes_shapes, aba_origem=0, sub_aba_origem=0)
    carregar('menor', modulos_escala_menor.TODOS_OS_SHAPES, nomes_shapes, aba_origem=0, sub_aba_origem=1)
    carregar('penta_maior', modulos_penta_maior.TODOS_OS_SHAPES_PENTA_MAIOR, nomes_shapes, aba_origem=0, sub_aba_origem=2)
    carregar('penta_menor', modulos_penta.TODOS_OS_SHAPES, nomes_shapes, aba_origem=0, sub_aba_origem=3)
    carregar('blues', teoria.TODOS_OS_SHAPES_BLUES, nomes_shapes, aba_origem=0, sub_aba_origem=4)
    carregar('modos', modos.TODOS_OS_MODOS, nomes_modos, aba_origem=0, sub_aba_origem=5)
    carregar('harmonica', harm_melo.TODOS_OS_SHAPES_HARM, nomes_shapes, aba_origem=0, sub_aba_origem=6)
    carregar('melodica', harm_melo.TODOS_OS_SHAPES_MELO, nomes_shapes, aba_origem=0, sub_aba_origem=7)
    carregar('exoticas', exoticas.TODOS_OS_SHAPES_EXOTICOS, ['Whole Tone', 'Diminuta'], aba_origem=0, sub_aba_origem=8)
    carregar('caged', acordes.TODOS_AS_TRIADES_MAIORES, nomes_acordes_maiores, aba_origem=1, sub_aba_origem=0)
    carregar('triades_maior', acordes.TODOS_AS_TRIADES_MAIORES, nomes_acordes_maiores, aba_origem=1, sub_aba_origem=1)
    carregar('triades_menor', acordes.TODOS_AS_TRIADES_MENORES, nomes_acordes_menores, aba_origem=1, sub_aba_origem=2)
    carregar('setimas', acordes.TODOS_OS_SETIMA, nomes_setimas, aba_origem=1, sub_aba_origem=3)
    carregar('power', acordes.TODOS_OS_POWER, nomes_power, aba_origem=1, sub_aba_origem=4)
    return dicionario