import pygame
import os
import json
from core.modulos.modulos_config import *


def _mouse_no_viewport(estado):
    """Posicao real do mouse descontando a barra superior."""
    from config.ui_metrics import ALTURA_TOPBAR
    x, y = getattr(estado, 'pos_mouse_real', None) or pygame.mouse.get_pos()
    return (x, y - ALTURA_TOPBAR)


def _avisar(estado, texto, tipo='info'):
    try:
        from ui.components.notificacoes import notificar
        from core.i18n import _t
        notificar(estado, _t(texto) if ':' not in texto else
                  _t(texto.split(':', 1)[0]) + ':' + texto.split(':', 1)[1], tipo)
    except Exception:
        print(texto)

class GerenciadorPerfil:
    """
        Como funciona: Mantém instâncias ativas e delega tarefas aos submódulos de 'GerenciadorPerfil'.
        Para que serve: Orquestra recursos e o ciclo de vida do módulo.
        Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_perfil'.
    """

    def __init__(self):
        """
            Como funciona: Inicializa os atributos e o estado inicial da instância.
            Para que serve: Prepara o objeto para ser utilizado no ciclo de vida da aplicação.
            Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_perfil'.
        """
        self.pasta_padrao = 'Perfis'
        self.arquivo_config_global = 'config_eiguit.json'
        self.ativo = False
        self.modo = None
        self.texto_input = ''
        self.lista_perfis = []
        self.indice_selecionado = 0
        if not os.path.exists(self.pasta_padrao):
            os.makedirs(self.pasta_padrao)
        self.BRANCO = PERFIL_BRANCO
        self.FUNDO = PERFIL_FUNDO
        self.AZUL_BOTAO = PERFIL_AZUL_BOTAO
        self.CINZA = PERFIL_CINZA
        self.VERMELHO = PERFIL_VERMELHO
        self.VERMELHO_DARK = PERFIL_VERMELHO_DARK

    def abrir_modal_novo(self):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'abrir modal novo'.
            Para que serve: Realiza as tarefas fundamentais de 'abrir modal novo' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'abrir modal novo'.
        """
        self.ativo = True
        self.modo = 'salvar'
        self.texto_input = self.nome_perfil_atual() or 'Meu_Setup'

    def abrir_modal_carregar(self):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'abrir modal carregar'.
            Para que serve: Realiza as tarefas fundamentais de 'abrir modal carregar' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'abrir modal carregar'.
        """
        self.ativo = True
        self.modo = 'carregar'
        self.lista_perfis = [f for f in os.listdir(self.pasta_padrao) if f.endswith('.json')]
        self.indice_selecionado = 0

    def abrir_modal_conta(self, estado):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'abrir modal conta'.
            Para que serve: Realiza as tarefas fundamentais de 'abrir modal conta' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'abrir modal conta'.
        """
        self.ativo = True
        self.modo = 'conta'
        self.email_exibir = getattr(estado, 'email_usuario', '---')

    def fechar_modal(self):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'fechar modal'.
            Para que serve: Realiza as tarefas fundamentais de 'fechar modal' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'fechar modal'.
        """
        self.ativo = False
        self.modo = None
        self.texto_input = ''

    def restaurar_layout(self, estado):
        """Devolve so a posicao e o tamanho dos blocos ao layout padrao."""
        # Layout padrao vem do canvas de design (config/layout_padrao.py),
        # ja proporcional a resolucao atual.
        from config.ui_metrics import ALTURA_TOPBAR
        from config.layout_padrao import calcular as calcular_layout_padrao

        w_tela = getattr(estado, 'LARGURA_TELA', 1280)
        h_viewport = max(600, getattr(estado, 'ALTURA_TELA', 720) - ALTURA_TOPBAR)
        padroes = calcular_layout_padrao(w_tela, h_viewport)

        for nome, coords in padroes.items():
            if hasattr(estado, nome):
                obj = getattr(estado, nome)
                obj.largura = coords['w']
                obj.altura = coords['h']
                obj.x = coords['x']
                obj.y = coords['y']

                if nome == 'dragger_guitarra':
                    estado.LARGURA_BRACO = coords['w']
                    estado.ALTURA_BRACO = coords['h']
                elif nome == 'dragger_acordes':
                    estado.ALTURA_ACORDES = coords['h']

                if hasattr(obj, 'rect_caixa'):
                    obj.rect_caixa.x = obj.x
                    obj.rect_caixa.y = obj.y
                    obj.rect_caixa.width = obj.largura
                    obj.rect_caixa.height = obj.altura
        if hasattr(estado, 'atualizar_medidas'):
            estado.atualizar_medidas()

    def restaurar_padrao(self, estado, configs=None, campo=None):
        """
            Como funciona: Volta layout, instrumento, tom, cores e afinador ao
            padrao de fabrica e esquece o ultimo perfil carregado.
            Para que serve: Opcao "Voltar para o Padrão" do menu Perfil.
            Onde é usada: Menu superior (core/acoes_cabecalho.py).
        """
        self.restaurar_layout(estado)
        # Resetar variáveis de escala do braço no estado
        if estado:
            estado.LARGURA_BRACO = 1713
            estado.ALTURA_BRACO = 393
            estado.instrumento = 'guitarra'
            estado.NUM_CASAS = 18
            estado.tom_atual = 'C'
            estado.indice_afinacao = 0
            estado.indice_cor_tonica = 0
            estado.indice_cor_terca = 0
            estado.indice_cor_quinta = 0
            estado.afinador_suavizacao = 5
            estado.afinador_sensibilidade = 0.5
            if hasattr(estado, 'atualizar_medidas'):
                estado.atualizar_medidas()
        if campo:
            campo.tonica_campo = 'C'
            campo.indice_escala_campo = 0
            campo.tonica = 'C'
            campo.tipo_escala = 'Maior (Jônio)'
            campo.indice_acorde_selecionado = -1
        self._gravar_config_global(ultimo_perfil='')
        print('[PERFIL] Layout restaurado para o padrão centralizado!')

    # Atributos extras das Configuracoes que tambem vao para o perfil
    CAMPOS_CONFIGS_EXTRAS = ('indice_tema', 'cor_customizada', 'hex_texto', 'velocidade_jogo',
                             'volume_fx', 'particulas_habilitadas', 'tamanho_notas',
                             'indice_tamanho_fonte')

    def montar_dados(self, estado, configs, campo, gravador):
        """Tudo o que o perfil guarda: layout, braco, cores, teclas e desempenho."""
        dados = {'posicoes_draggers': {}, 'estado': {'instrumento': getattr(estado, 'instrumento', 'guitarra'), 'NUM_CASAS': getattr(estado, 'NUM_CASAS', 18), 'tom_atual': getattr(estado, 'tom_atual', 'C'), 'indice_afinacao': getattr(estado, 'indice_afinacao', 0), 'indice_cor_tonica': getattr(estado, 'indice_cor_tonica', 0), 'indice_cor_terca': getattr(estado, 'indice_cor_terca', 0), 'indice_cor_quinta': getattr(estado, 'indice_cor_quinta', 0), 'afinador_suavizacao': getattr(estado, 'afinador_suavizacao', 5), 'afinador_sensibilidade': getattr(estado, 'afinador_sensibilidade', 0.5), 'capo_casa': getattr(estado, 'capo_casa', 0), 'drone_nota': getattr(estado, 'drone_nota', 'C'), 'blocos_guardados': sorted(getattr(estado, 'blocos_guardados', []) or [])}, 'configs': {'transparencia': getattr(configs, 'transparencia', 100), 'cor_braco': getattr(configs, 'cor_braco', (80, 40, 15)), 'cor_notas': getattr(configs, 'cor_notas', (255, 255, 255)), 'indice_modo': getattr(configs, 'indice_modo', 0), 'indice_fonte': getattr(configs, 'indice_fonte', 0), 'indice_idioma': getattr(configs, 'indice_idioma', 0)}, 'campo_harmonico': {'tonica_campo': getattr(campo, 'tonica_campo', 'C'), 'indice_escala_campo': getattr(campo, 'indice_escala_campo', 0)}, 'gravador': {'device_id': getattr(gravador, 'device_id', None)}}
        if configs is not None:
            for nome in self.CAMPOS_CONFIGS_EXTRAS:
                if hasattr(configs, nome):
                    valor = getattr(configs, nome)
                    dados['configs'][nome] = list(valor) if isinstance(valor, tuple) else valor
        from config.design_system import TEMA
        import core.atalhos as atalhos
        import core.desempenho as desempenho
        dados['interface'] = {'tema': TEMA.modo}
        dados['atalhos'] = atalhos.diferentes_do_padrao(estado)
        dados['desempenho'] = dict(desempenho.obter(estado))
        lista_draggers = ['dragger_guitarra', 'dragger_acordes', 'dragger_controles_topo', 'dragger_painel_inferior', 'dragger_metronomo', 'dragger_cores', 'dragger_nota_atual', 'dragger_sessao', 'dragger_circulo', 'dragger_historico', 'dragger_ideias', 'dragger_drone', 'dragger_progressoes', 'dragger_graus', 'dragger_cordas', 'dragger_capo']
        for nome in lista_draggers:
            if hasattr(estado, nome):
                obj = getattr(estado, nome)
                dados['posicoes_draggers'][nome] = {'x': obj.x, 'y': obj.y, 'w': obj.largura, 'h': obj.altura}
        return dados

    def salvar_perfil(self, estado, configs, campo, gravador):
        """
            Como funciona: Grava o perfil com o nome digitado no modal (arquivo
            em Perfis/ + copia na nuvem quando ha conta).
            Para que serve: Opcao "Salvar perfil..." do botao da conta.
            Onde é usada: Modal de perfil (tratar_eventos).
        """
        nome_arquivo = self.texto_input.strip()
        if not nome_arquivo:
            return
        if not nome_arquivo.endswith('.json'):
            nome_arquivo += '.json'
        caminho = os.path.join(self.pasta_padrao, nome_arquivo)
        dados = self.montar_dados(estado, configs, campo, gravador)
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=4)
        if hasattr(estado, 'usuario_id_logado') and estado.usuario_id_logado:
            try:
                from BD.gerenciador_remoto_db import GerenciadorDB
                db = GerenciadorDB()
                sucesso = db.salvar_perfil(estado.usuario_id_logado, nome_arquivo.replace('.json', ''), dados)
                if sucesso:
                    print(f"[CLOUD] Perfil '{nome_arquivo}' sincronizado com sucesso!")
                else:
                    print(f"[CLOUD] Erro ao sincronizar perfil '{nome_arquivo}'")
            except Exception as e:
                print(f'[CLOUD] Falha na conexão com o banco: {e}')
        self.salvar_ultimo_perfil_config(caminho)
        print(f'[PERFIL] Perfil completo salvo em: {caminho}')
        _avisar(estado, f"Perfil salvo: {nome_arquivo.replace('.json', '')}", 'sucesso')
        self.fechar_modal()

    def carregar_perfil(self, caminho, estado, configs, campo, gravador):
        """
            Como funciona: Lê dados de disco, banco de dados ou estado salvo.
            Para que serve: Popula as estruturas em memória com as informações persistidas.
            Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_perfil'.
        """
        if not os.path.exists(caminho):
            return
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            if 'posicoes_draggers' in dados:
                for nome, coords in dados['posicoes_draggers'].items():
                    if hasattr(estado, nome):
                        obj = getattr(estado, nome)
                        obj.x = coords['x']
                        obj.y = coords['y']
                        if 'w' in coords: obj.largura = coords['w']
                        if 'h' in coords: obj.altura = coords['h']
                        if hasattr(obj, 'rect_caixa'):
                            obj.rect_caixa.x = obj.x
                            obj.rect_caixa.y = obj.y
                            obj.rect_caixa.width = obj.largura
                            obj.rect_caixa.height = obj.altura
                        
                        # Sincronizar braço da guitarra especificamente
                        if nome == 'dragger_guitarra':
                            estado.LARGURA_BRACO = obj.largura
                            estado.ALTURA_BRACO = obj.altura
            if 'estado' in dados:
                d_est = dados['estado']
                estado.instrumento = d_est.get('instrumento', 'guitarra')
                estado.NUM_CASAS = d_est.get('NUM_CASAS', 18)
                estado.tom_atual = d_est.get('tom_atual', 'C')
                estado.indice_afinacao = d_est.get('indice_afinacao', 0)
                estado.indice_cor_tonica = d_est.get('indice_cor_tonica', 0)
                estado.indice_cor_terca = d_est.get('indice_cor_terca', 0)
                estado.indice_cor_quinta = d_est.get('indice_cor_quinta', 0)
                estado.afinador_suavizacao = d_est.get('afinador_suavizacao', 5)
                # Blocos extras: capotraste e nota de referencia do drone
                estado.capo_casa = d_est.get('capo_casa', 0)
                estado.drone_nota = d_est.get('drone_nota', 'C')
                # Gaveteiro: quais blocos ficaram guardados na coluna
                from ui.components.gaveteiro import NOMES as NOMES_GAVETAS
                guardados = d_est.get('blocos_guardados')
                if guardados is not None:
                    estado.blocos_guardados = {n for n in guardados
                                               if n in NOMES_GAVETAS}
                estado.afinador_sensibilidade = d_est.get('afinador_sensibilidade', 0.5)
            if 'configs' in dados:
                d_cfg = dados['configs']
                configs.transparencia = d_cfg.get('transparencia', 100)
                configs.cor_braco = tuple(d_cfg.get('cor_braco', (80, 40, 15)))
                configs.cor_notas = tuple(d_cfg.get('cor_notas', (255, 255, 255)))
                configs.indice_modo = d_cfg.get('indice_modo', 0)
                configs.indice_fonte = d_cfg.get('indice_fonte', 0)
                configs.indice_idioma = d_cfg.get('indice_idioma', 0)
                if hasattr(configs, 'idiomas'):
                    codigo = configs.idiomas[configs.indice_idioma]['code']
                    from core.i18n import sistema_traducao
                    sistema_traducao.atualizar_configuracao(codigo)
                    estado.idioma = codigo
            if 'configs' in dados and configs is not None:
                for nome in self.CAMPOS_CONFIGS_EXTRAS:
                    if nome in dados['configs'] and hasattr(configs, nome):
                        valor = dados['configs'][nome]
                        if isinstance(getattr(configs, nome), tuple) and isinstance(valor, list):
                            valor = tuple(valor)
                        setattr(configs, nome, valor)
            import core.atalhos as atalhos
            import core.desempenho as desempenho
            estado.atalhos = atalhos.normalizar(dados.get('atalhos'))
            estado._indice_atalhos = None
            estado.desempenho = desempenho.normalizar(dados.get('desempenho'))
            desempenho.aplicar(estado)
            tema = (dados.get('interface') or {}).get('tema')
            if tema:
                from config.design_system import TEMA
                import config.theme as tema_legado
                if TEMA.modo != tema:
                    TEMA.definir_modo(tema)
                    tema_legado.sincronizar_tema()
            if 'campo_harmonico' in dados:
                d_ch = dados['campo_harmonico']
                campo.tonica_campo = d_ch.get('tonica_campo', 'C')
                campo.indice_escala_campo = d_ch.get('indice_escala_campo', 0)
                campo.tonica = campo.tonica_campo
                if hasattr(campo, 'escalas_campo') and 0 <= campo.indice_escala_campo < len(campo.escalas_campo):
                    campo.tipo_escala = campo.escalas_campo[campo.indice_escala_campo]['nome']
                campo.indice_acorde_selecionado = -1
            if 'gravador' in dados and gravador:
                novo_id = dados['gravador'].get('device_id', None)
                if novo_id is not None and hasattr(gravador, 'mudar_dispositivo'):
                    try:
                        gravador.mudar_dispositivo(novo_id)
                    except:
                        pass
            if hasattr(estado, 'atualizar_medidas'):
                estado.atualizar_medidas()
            print(f'[PERFIL] Setup global carregado: {caminho}')
            self.salvar_ultimo_perfil_config(caminho)
            if self.ativo:
                _avisar(estado, 'Perfil carregado: '
                        + os.path.splitext(os.path.basename(caminho))[0], 'sucesso')
        except Exception as e:
            print(f'[PERFIL] Erro ao carregar perfil: {e}')
            _avisar(estado, f'Erro ao carregar perfil: {e}', 'erro')

    def caminho_perfil_atual(self):
        """Arquivo do ultimo perfil salvo/carregado, ou '' se nao houver."""
        try:
            with open(self.arquivo_config_global, 'r', encoding='utf-8') as f:
                ultimo = json.load(f).get('ultimo_perfil', '')
        except Exception:
            return ''
        return ultimo if ultimo and os.path.exists(ultimo) else ''

    def nome_perfil_atual(self):
        caminho = self.caminho_perfil_atual()
        return os.path.splitext(os.path.basename(caminho))[0] if caminho else ''

    def deletar_perfil_atual(self):
        """
            Como funciona: Apaga o arquivo do perfil atual e esquece a referencia.
            Para que serve: Opcao "Excluir perfil atual" do menu Perfil.
            Onde é usada: core/acoes_cabecalho.py (com confirmacao antes).
            Devolve o nome do perfil apagado, ou '' se nao havia perfil.
        """
        caminho = self.caminho_perfil_atual()
        if not caminho:
            return ''
        try:
            os.remove(caminho)
            print(f'[PERFIL] Perfil deletado: {caminho}')
            self._gravar_config_global(ultimo_perfil='')
        except OSError:
            return ''
        return os.path.splitext(os.path.basename(caminho))[0]

    def _gravar_config_global(self, **valores):
        """Atualiza config_eiguit.json sem apagar o resto (o tema mora la)."""
        dados = {}
        try:
            with open(self.arquivo_config_global, 'r', encoding='utf-8') as f:
                dados = json.load(f)
        except Exception:
            dados = {}
        dados.update(valores)
        try:
            with open(self.arquivo_config_global, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False)
        except OSError:
            pass

    def salvar_ultimo_perfil_config(self, caminho):
        """Lembra qual perfil abrir na proxima vez."""
        self._gravar_config_global(ultimo_perfil=caminho)

    # ------------------------------------------------------ auto-salvar ----
    INTERVALO_AUTO_SALVAR = 20.0      # segundos entre conferencias
    ESPERA_APOS_MUDANCA = 1.0         # agrupa varias mudancas seguidas
    NOME_PERFIL_PADRAO = 'Padrão'

    def caminho_auto_salvar(self):
        """Perfil atual; se nao houver, o perfil 'Padrão' (criado na hora)."""
        return self.caminho_perfil_atual() or os.path.join(self.pasta_padrao,
                                                           self.NOME_PERFIL_PADRAO + '.json')

    def salvar_automatico(self, estado, configs, campo, gravador, forcar=False):
        """
            Grava o estado atual no perfil, so se algo mudou desde a ultima vez.
            Devolve True quando gravou.
        """
        try:
            dados = self.montar_dados(estado, configs, campo, gravador)
            texto = json.dumps(dados, indent=4, ensure_ascii=False, default=str)
        except Exception as erro:
            print(f'[PERFIL] Auto-salvar falhou ao montar os dados: {erro}')
            return False
        caminho = self.caminho_auto_salvar()
        if not forcar and texto == getattr(self, '_ultimo_auto_salvo', None) \
                and os.path.exists(caminho):
            return False
        try:
            os.makedirs(os.path.dirname(caminho) or '.', exist_ok=True)
            temporario = caminho + '.tmp'
            with open(temporario, 'w', encoding='utf-8') as f:
                f.write(texto)
            os.replace(temporario, caminho)       # nunca deixa o perfil pela metade
        except OSError as erro:
            print(f'[PERFIL] Auto-salvar falhou: {erro}')
            return False
        self._ultimo_auto_salvo = texto
        if not self.caminho_perfil_atual():
            self.salvar_ultimo_perfil_config(caminho)
        return True

    def tick_auto_salvar(self, estado, configs, campo, gravador, agora=None):
        """Chamado a cada quadro: barato, so olha o relogio."""
        import time as _time
        agora = agora if agora is not None else _time.time()
        if getattr(estado, 'perfil_alterado', False):
            if not getattr(self, '_mudanca_desde', 0):
                self._mudanca_desde = agora
            if agora - self._mudanca_desde >= self.ESPERA_APOS_MUDANCA:
                estado.perfil_alterado = False
                self._mudanca_desde = 0
                self.salvar_automatico(estado, configs, campo, gravador)
                self._ultima_conferencia = agora
            return
        if agora - getattr(self, '_ultima_conferencia', 0) >= self.INTERVALO_AUTO_SALVAR:
            self._ultima_conferencia = agora
            if self.ativo:
                return            # modal aberto: espera terminar
            self.salvar_automatico(estado, configs, campo, gravador)

    def sincronizar_nuvem(self, estado, configs, campo, gravador, espera=4.0):
        """Ao sair: manda o perfil atual para a conta, sem travar mais que 'espera'."""
        usuario = getattr(estado, 'usuario_id_logado', None)
        if not usuario:
            return
        import threading
        nome = os.path.splitext(os.path.basename(self.caminho_auto_salvar()))[0]
        dados = self.montar_dados(estado, configs, campo, gravador)

        def _enviar():
            try:
                from BD.gerenciador_remoto_db import GerenciadorDB
                GerenciadorDB().salvar_perfil(usuario, nome, dados)
            except Exception as erro:
                print(f'[CLOUD] Perfil nao sincronizado: {erro}')

        t = threading.Thread(target=_enviar, daemon=True)
        t.start()
        t.join(espera)

    def carregar_ultimo_perfil(self, estado, configs, campo, gravador):
        """
            Como funciona: Lê dados de disco, banco de dados ou estado salvo.
            Para que serve: Popula as estruturas em memória com as informações persistidas.
            Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_perfil'.
        """
        if os.path.exists(self.arquivo_config_global):
            try:
                with open(self.arquivo_config_global, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    ultimo = config.get('ultimo_perfil', '')
                    if ultimo and os.path.exists(ultimo):
                        self.carregar_perfil(ultimo, estado, configs, campo, gravador)
                        return
            except Exception:
                pass
        padrao = os.path.join(self.pasta_padrao, self.NOME_PERFIL_PADRAO + '.json')
        if os.path.exists(padrao):
            self.carregar_perfil(padrao, estado, configs, campo, gravador)

    def tratar_eventos(self, eventos, estado, configs, campo, gravador):
        """
            Como funciona: Verifica colisões e processa inputs do mouse/teclado.
            Para que serve: Mapeia ações do usuário para atualizações de estado.
            Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_perfil'.
        """
        if not self.ativo:
            return False
        for evento in eventos:
            if evento.type == pygame.QUIT:
                estado.solicitou_saida = True
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE or (self.modo == 'conta' and evento.key == pygame.K_RETURN):
                    self.fechar_modal()
                    return True
                elif self.modo == 'salvar':
                    if evento.key == pygame.K_RETURN:
                        self.salvar_perfil(estado, configs, campo, gravador)
                    elif evento.key == pygame.K_BACKSPACE:
                        self.texto_input = self.texto_input[:-1]
                    elif len(self.texto_input) < 20 and evento.unicode.isprintable():
                        self.texto_input += evento.unicode
                elif self.modo == 'carregar' and evento.key == pygame.K_RETURN:
                    if len(self.lista_perfis) > 0:
                        caminho = os.path.join(self.pasta_padrao, self.lista_perfis[self.indice_selecionado])
                        self.carregar_perfil(caminho, estado, configs, campo, gravador)
                        self.fechar_modal()
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                # O modal e desenhado no viewport fixo (abaixo da barra), fora da
                # camera: o clique tem de usar o mouse real, nao o virtual.
                pos_mouse = _mouse_no_viewport(estado)
                if hasattr(self, 'btn_cancelar') and self.btn_cancelar.collidepoint(pos_mouse):
                    self.fechar_modal()
                    return True
                if self.modo == 'salvar':
                    if hasattr(self, 'btn_acao') and self.btn_acao.collidepoint(pos_mouse):
                        self.salvar_perfil(estado, configs, campo, gravador)
                elif self.modo == 'carregar':
                    if hasattr(self, 'btn_esq') and self.btn_esq.collidepoint(pos_mouse) and (len(self.lista_perfis) > 0):
                        self.indice_selecionado = (self.indice_selecionado - 1) % len(self.lista_perfis)
                    elif hasattr(self, 'btn_dir') and self.btn_dir.collidepoint(pos_mouse) and (len(self.lista_perfis) > 0):
                        self.indice_selecionado = (self.indice_selecionado + 1) % len(self.lista_perfis)
                    elif hasattr(self, 'btn_acao') and self.btn_acao.collidepoint(pos_mouse) and (len(self.lista_perfis) > 0):
                        caminho = os.path.join(self.pasta_padrao, self.lista_perfis[self.indice_selecionado])
                        self.carregar_perfil(caminho, estado, configs, campo, gravador)
                        self.fechar_modal()
                elif self.modo == 'conta':
                    if hasattr(self, 'btn_acao') and self.btn_acao.collidepoint(pos_mouse):
                        self.fechar_modal()
                    elif hasattr(self, 'btn_deletar_conta') and self.btn_deletar_conta.collidepoint(pos_mouse):
                        from tkinter import messagebox, Tk
                        root = Tk()
                        root.withdraw()
                        if messagebox.askyesno('CONFIRMAÇÃO CRÍTICA', 'Deseja REALMENTE deletar sua conta permanentemente?\n\nIsso apagará todos os seus perfis e projetos na nuvem!'):
                            from BD.gerenciador_remoto_db import GerenciadorDB
                            db = GerenciadorDB()
                            if db.deletar_conta(estado.usuario_id_logado):
                                if os.path.exists('sessao_cache.json'):
                                    try:
                                        os.remove('sessao_cache.json')
                                    except:
                                        pass
                                messagebox.showinfo('Sucesso', 'Conta deletada com sucesso. O programa será fechado.')
                                estado.solicitou_saida = True
                            else:
                                messagebox.showerror('Erro', 'Não foi possível deletar a conta. Tente novamente.')
                        root.destroy()
        return True

    def desenhar(self, tela, fonte_titulo, fonte_ui, estado=None):
        """
            Como funciona: Utiliza funções de renderização do Pygame para desenhar na tela.
            Para que serve: Apresenta o elemento visual 'desenhar' na interface gráfica.
            Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_perfil'.
        """
        if not self.ativo:
            return
        overlay = pygame.Surface((tela.get_width(), tela.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        tela.blit(overlay, (0, 0))
        largura_modal = 450
        altura_modal = 300 if self.modo == 'conta' else 250
        cx = tela.get_width() // 2 - largura_modal // 2
        cy = tela.get_height() // 2 - altura_modal // 2
        rect_modal = pygame.Rect(cx, cy, largura_modal, altura_modal)
        pygame.draw.rect(tela, self.FUNDO, rect_modal, border_radius=10)
        pygame.draw.rect(tela, self.CINZA, rect_modal, width=2, border_radius=10)
        if self.modo == 'salvar':
            txt_tit = fonte_titulo.render('Salvar Novo Perfil', True, self.BRANCO)
            tela.blit(txt_tit, (cx + 20, cy + 20))
            tela.blit(fonte_ui.render('Nome do Perfil:', True, self.CINZA), (cx + 20, cy + 70))
            rect_input = pygame.Rect(cx + 20, cy + 95, largura_modal - 40, 40)
            pygame.draw.rect(tela, (20, 20, 20), rect_input, border_radius=5)
            pygame.draw.rect(tela, self.AZUL_BOTAO, rect_input, width=2, border_radius=5)
            txt_digitado = fonte_titulo.render(self.texto_input + '_', True, self.BRANCO)
            tela.blit(txt_digitado, (rect_input.x + 10, rect_input.y + 10))
            texto_btn_acao = 'Salvar Setup'
            cor_acao = self.AZUL_BOTAO if len(self.texto_input) > 0 else self.CINZA
        elif self.modo == 'carregar':
            txt_tit = fonte_titulo.render('Carregar Perfil Existente', True, self.BRANCO)
            tela.blit(txt_tit, (cx + 20, cy + 20))
            tela.blit(fonte_ui.render('Selecione o arquivo salvo:', True, self.CINZA), (cx + 20, cy + 70))
            self.btn_esq = pygame.Rect(cx + 20, cy + 95, 40, 40)
            self.btn_dir = pygame.Rect(cx + largura_modal - 60, cy + 95, 40, 40)
            rect_meio = pygame.Rect(cx + 70, cy + 95, largura_modal - 140, 40)
            pygame.draw.rect(tela, self.AZUL_BOTAO, self.btn_esq, border_radius=5)
            pygame.draw.rect(tela, self.AZUL_BOTAO, self.btn_dir, border_radius=5)
            tela.blit(fonte_titulo.render('<', True, self.BRANCO), (self.btn_esq.centerx - 6, self.btn_esq.centery - 12))
            tela.blit(fonte_titulo.render('>', True, self.BRANCO), (self.btn_dir.centerx - 6, self.btn_dir.centery - 12))
            pygame.draw.rect(tela, (20, 20, 20), rect_meio, border_radius=5)
            pygame.draw.rect(tela, self.CINZA, rect_meio, width=2, border_radius=5)
            if len(self.lista_perfis) > 0:
                nome_exibir = self.lista_perfis[self.indice_selecionado]
            else:
                nome_exibir = 'Nenhum Perfil Encontrado'
            txt_nome = fonte_titulo.render(nome_exibir, True, self.BRANCO)
            tela.blit(txt_nome, (rect_meio.centerx - txt_nome.get_width() // 2, rect_meio.centery - txt_nome.get_height() // 2))
            texto_btn_acao = 'Carregar'
            cor_acao = self.AZUL_BOTAO if len(self.lista_perfis) > 0 else self.CINZA
        elif self.modo == 'conta':
            txt_tit = fonte_titulo.render('Minha Conta (Cloud)', True, self.BRANCO)
            tela.blit(txt_tit, (cx + 20, cy + 20))
            tela.blit(fonte_ui.render('Email Logado:', True, self.CINZA), (cx + 20, cy + 70))
            txt_email = fonte_titulo.render(self.email_exibir, True, self.AZUL_BOTAO)
            tela.blit(txt_email, (cx + 20, cy + 95))
            self.btn_deletar_conta = pygame.Rect(cx + 20, cy + 150, largura_modal - 40, 45)
            pygame.draw.rect(tela, self.VERMELHO_DARK, self.btn_deletar_conta, border_radius=5)
            txt_del = fonte_ui.render('DELETAR MINHA CONTA PERMANENTEMENTE', True, self.BRANCO)
            tela.blit(txt_del, (self.btn_deletar_conta.centerx - txt_del.get_width() // 2, self.btn_deletar_conta.centery - txt_del.get_height() // 2))
            texto_btn_acao = 'Ok'
            cor_acao = self.AZUL_BOTAO
        if self.modo != 'conta':
            txt_dir = fonte_ui.render(f'Pasta Base: ./EIGUIT/{self.pasta_padrao}/', True, (150, 150, 150))
            tela.blit(txt_dir, (cx + 20, cy + 150))
        self.btn_cancelar = pygame.Rect(cx + 20, cy + altura_modal - 60, 150, 40)
        self.btn_acao = pygame.Rect(cx + largura_modal - 170, cy + altura_modal - 60, 150, 40)
        pygame.draw.rect(tela, self.VERMELHO if self.modo != 'conta' else self.CINZA, self.btn_cancelar, border_radius=5)
        txt_canc = fonte_ui.render('Sair' if self.modo == 'conta' else 'Cancelar', True, self.BRANCO)
        tela.blit(txt_canc, (self.btn_cancelar.centerx - txt_canc.get_width() // 2, self.btn_cancelar.centery - txt_canc.get_height() // 2))
        pygame.draw.rect(tela, cor_acao, self.btn_acao, border_radius=5)
        txt_acao_render = fonte_ui.render(texto_btn_acao, True, self.BRANCO)
        tela.blit(txt_acao_render, (self.btn_acao.centerx - txt_acao_render.get_width() // 2, self.btn_acao.centery - txt_acao_render.get_height() // 2))