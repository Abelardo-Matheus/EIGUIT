import struct

class LeitorMIDI:
    def __init__(self, caminho_arquivo):
        self.caminho = caminho_arquivo
        self.notas = [] # Lista de (tempo, pitch, duration)
        self.tracks = []
        self.division = 480 # Default
        
    def ler(self):
        try:
            if not os.path.exists(self.caminho):
                print(f"Erro: Arquivo {self.caminho} não encontrado.")
                return False
                
            tamanho = os.path.getsize(self.caminho)
            if tamanho < 4:
                print(f"Erro: Arquivo {self.caminho} é muito pequeno ({tamanho} bytes).")
                return False

            with open(self.caminho, 'rb') as f:
                data = f.read()
            
            # Header validation
            if data[:4] != b'MThd':
                # Check if it's a JSON error file
                if data.startswith(b'{'):
                    try:
                        import json
                        err_data = json.loads(data.decode('utf-8', errors='ignore'))
                        print(f"Erro: O arquivo baixado é um JSON de erro do Songsterr: {err_data.get('error', 'Unknown error')}")
                    except:
                        print(f"Erro: O arquivo {self.caminho} não é um MIDI válido (Header: {data[:4]}).")
                else:
                    print(f"Erro: O arquivo {self.caminho} não possui o header MThd (Header: {data[:4]}).")
                return False
            
            header_len = struct.unpack('>I', data[4:8])[0]
            format, n_tracks, division = struct.unpack('>HHH', data[8:14])
            self.division = division
            
            offset = 8 + header_len
            for _ in range(n_tracks):
                if data[offset:offset+4] != b'MTrk':
                    break
                track_len = struct.unpack('>I', data[offset+4:offset+8])[0]
                track_data = data[offset+8:offset+8+track_len]
                self.processar_track(track_data)
                offset += 8 + track_len
            return True
        except Exception as e:
            print(f"Erro ao ler MIDI: {e}")
            return False

    def processar_track(self, data):
        notas_abertas = {} # pitch -> tempo_inicio
        tempo_acumulado = 0
        i = 0
        
        while i < len(data):
            # Delta-time (variable length)
            delta, bytes_read = self.read_vlv(data[i:])
            i += bytes_read
            tempo_acumulado += delta
            
            status = data[i]
            if status < 0x80: # Running status (not handling fully for simplicity)
                # For Songsterr midis, they usually repeat the status
                pass
            else:
                i += 1
            
            event_type = status & 0xF0
            channel = status & 0x0F
            
            if event_type == 0x90: # Note On
                pitch = data[i]
                velocity = data[i+1]
                i += 2
                if velocity > 0:
                    notas_abertas[pitch] = tempo_acumulado
                else:
                    if pitch in notas_abertas:
                        inicio = notas_abertas.pop(pitch)
                        self.notas.append({
                            'tempo': inicio,
                            'duracao': tempo_acumulado - inicio,
                            'pitch': pitch,
                            'canal': channel
                        })
            elif event_type == 0x80: # Note Off
                pitch = data[i]
                i += 2
                if pitch in notas_abertas:
                    inicio = notas_abertas.pop(pitch)
                    self.notas.append({
                        'tempo': inicio,
                        'duracao': tempo_acumulado - inicio,
                        'pitch': pitch,
                        'canal': channel
                    })
            elif status == 0xFF: # Meta event
                type = data[i]
                i += 1
                length, bytes_read = self.read_vlv(data[i:])
                i += bytes_read + length
            elif event_type in [0xA0, 0xB0, 0xE0]: # Aftertouch, Control Change, Pitch Bend
                i += 2
            elif event_type in [0xC0, 0xD0]: # Program Change, Channel Pressure
                i += 1
            else:
                # Unknown or sysex
                pass

    def read_vlv(self, data):
        value = 0
        i = 0
        while True:
            byte = data[i]
            value = (value << 7) | (byte & 0x7F)
            i += 1
            if not (byte & 0x80):
                break
        return value, i

    def converter_para_tab(self, tuning):
        """
        Converte as notas MIDI para (string, fret) baseado na afinação.
        tuning: lista de pitches MIDI para cada corda (ex: [64, 59, 55, 50, 45, 40] para EADGBE)
        """
        tab_data = []
        # Ordena por tempo
        self.notas.sort(key=lambda x: x['tempo'])
        
        for n in self.notas:
            pitch = n['pitch']
            # Tenta encontrar a corda mais adequada (preferindo cordas mais agudas/altas no braço se necessário)
            # No MIDI do Songsterr, às vezes o canal indica a corda, mas vamos usar lógica de proximidade
            possibilidades = []
            for s_idx, s_pitch in enumerate(tuning):
                fret = pitch - s_pitch
                if 0 <= fret <= 24: # Casa válida
                    possibilidades.append((s_idx, fret))
            
            if possibilidades:
                # Escolha simples: a que der a menor casa (mais perto do nut) ou algo assim
                # Para simplificar, pegamos a primeira válida
                s_idx, fret = possibilidades[0]
                tab_data.append({
                    'tempo': n['tempo'],
                    'string': s_idx,
                    'fret': fret,
                    'duracao': n['duracao']
                })
        return tab_data
