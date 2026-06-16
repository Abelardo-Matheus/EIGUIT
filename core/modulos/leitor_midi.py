import struct

class LeitorMIDI:
    """
        Como funciona: Define a estrutura e estado do componente 'LeitorMIDI'.
        Para que serve: Atua como o modelo principal para instâncias de 'LeitorMIDI'.
        Onde é usada: Chamado a partir do módulo ou classe base de 'leitor_midi'.
    """

    def __init__(self, caminho_arquivo):
        """
            Como funciona: Inicializa os atributos e o estado inicial da instância.
            Para que serve: Prepara o objeto para ser utilizado no ciclo de vida da aplicação.
            Onde é usada: Chamado a partir do módulo ou classe base de 'leitor_midi'.
        """
        self.caminho = caminho_arquivo
        self.notas = []
        self.tracks = []
        self.division = 480

    def ler(self):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'ler'.
            Para que serve: Realiza as tarefas fundamentais de 'ler' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'ler'.
        """
        try:
            if not os.path.exists(self.caminho):
                print(f'Erro: Arquivo {self.caminho} não encontrado.')
                return False
            tamanho = os.path.getsize(self.caminho)
            if tamanho < 4:
                print(f'Erro: Arquivo {self.caminho} é muito pequeno ({tamanho} bytes).')
                return False
            with open(self.caminho, 'rb') as f:
                data = f.read()
            if data[:4] != b'MThd':
                if data.startswith(b'{'):
                    try:
                        import json
                        err_data = json.loads(data.decode('utf-8', errors='ignore'))
                        print(f"Erro: O arquivo baixado é um JSON de erro do Songsterr: {err_data.get('error', 'Unknown error')}")
                    except:
                        print(f'Erro: O arquivo {self.caminho} não é um MIDI válido (Header: {data[:4]}).')
                else:
                    print(f'Erro: O arquivo {self.caminho} não possui o header MThd (Header: {data[:4]}).')
                return False
            header_len = struct.unpack('>I', data[4:8])[0]
            format, n_tracks, division = struct.unpack('>HHH', data[8:14])
            self.division = division
            offset = 8 + header_len
            for _ in range(n_tracks):
                if data[offset:offset + 4] != b'MTrk':
                    break
                track_len = struct.unpack('>I', data[offset + 4:offset + 8])[0]
                track_data = data[offset + 8:offset + 8 + track_len]
                self.processar_track(track_data)
                offset += 8 + track_len
            return True
        except Exception as e:
            print(f'Erro ao ler MIDI: {e}')
            return False

    def processar_track(self, data):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'processar track'.
            Para que serve: Realiza as tarefas fundamentais de 'processar track' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'processar track'.
        """
        notas_abertas = {}
        tempo_acumulado = 0
        i = 0
        while i < len(data):
            delta, bytes_read = self.read_vlv(data[i:])
            i += bytes_read
            tempo_acumulado += delta
            status = data[i]
            if status < 128:
                pass
            else:
                i += 1
            event_type = status & 240
            channel = status & 15
            if event_type == 144:
                pitch = data[i]
                velocity = data[i + 1]
                i += 2
                if velocity > 0:
                    notas_abertas[pitch] = tempo_acumulado
                elif pitch in notas_abertas:
                    inicio = notas_abertas.pop(pitch)
                    self.notas.append({'tempo': inicio, 'duracao': tempo_acumulado - inicio, 'pitch': pitch, 'canal': channel})
            elif event_type == 128:
                pitch = data[i]
                i += 2
                if pitch in notas_abertas:
                    inicio = notas_abertas.pop(pitch)
                    self.notas.append({'tempo': inicio, 'duracao': tempo_acumulado - inicio, 'pitch': pitch, 'canal': channel})
            elif status == 255:
                type = data[i]
                i += 1
                length, bytes_read = self.read_vlv(data[i:])
                i += bytes_read + length
            elif event_type in [160, 176, 224]:
                i += 2
            elif event_type in [192, 208]:
                i += 1
            else:
                pass

    def read_vlv(self, data):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'read vlv'.
            Para que serve: Realiza as tarefas fundamentais de 'read vlv' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'read vlv'.
        """
        value = 0
        i = 0
        while True:
            byte = data[i]
            value = value << 7 | byte & 127
            i += 1
            if not byte & 128:
                break
        return (value, i)

    def converter_para_tab(self, tuning):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'converter para tab'.
            Para que serve: Realiza as tarefas fundamentais de 'converter para tab' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'converter para tab'.
        """
        tab_data = []
        self.notas.sort(key=lambda x: x['tempo'])
        for n in self.notas:
            pitch = n['pitch']
            possibilidades = []
            for s_idx, s_pitch in enumerate(tuning):
                fret = pitch - s_pitch
                if 0 <= fret <= 24:
                    possibilidades.append((s_idx, fret))
            if possibilidades:
                s_idx, fret = possibilidades[0]
                tab_data.append({'tempo': n['tempo'], 'string': s_idx, 'fret': fret, 'duracao': n['duracao']})
        return tab_data