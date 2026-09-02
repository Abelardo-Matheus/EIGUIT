from .top_bar import desenhar_painel_superior
from .instrument_controls import desenhar_controles_instrumento
from .chord_selector import desenhar_acordes_arrastaveis
from .playback_controls import desenhar_controles_playback
from .audio_sidebar import desenhar_painel_cores, desenhar_bloco_nota_atual
from .bottom_nav import desenhar_secoes_inferiores_expansiveis
from .session_panel import desenhar_painel_sessao
from .blocos_extras import (BLOCOS_EXTRAS, PROGRESSOES_RAPIDAS,
                            alternar_drone, alternar_gravacao_ideia,
                            aplicar_grau, aplicar_progressao,
                            desenhar_bloco_capo, desenhar_bloco_circulo,
                            desenhar_bloco_cordas, desenhar_bloco_drone,
                            desenhar_bloco_graus, desenhar_bloco_historico,
                            desenhar_bloco_ideias, desenhar_bloco_progressoes,
                            desenhar_blocos_extras, registrar_nota_historico,
                            tratar_clique_blocos)
from .gaveteiro import (GAVETAS as GAVETAS_LATERAIS, desenhar_gaveteiro,
                        guardar_bloco, soltar_bloco, alternar_bloco,
                        bloco_visivel, tratar_evento_gaveteiro)
