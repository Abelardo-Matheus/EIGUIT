from .top_bar import desenhar_painel_superior
from .instrument_controls import desenhar_controles_instrumento
from .chord_selector import desenhar_acordes_arrastaveis
from .playback_controls import desenhar_controles_playback
from .audio_sidebar import desenhar_painel_cores, desenhar_bloco_nota_atual
from .bottom_nav import desenhar_secoes_inferiores_expansiveis
from .session_panel import desenhar_painel_sessao
from .blocos_extras import (desenhar_bloco_circulo, desenhar_bloco_historico,
                            desenhar_bloco_ideias, registrar_nota_historico,
                            alternar_gravacao_ideia, desenhar_bloco_drone,
                            alternar_drone, desenhar_bloco_progressoes,
                            aplicar_progressao, PROGRESSOES_RAPIDAS)
