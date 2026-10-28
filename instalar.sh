#!/usr/bin/env bash
# =============================================================================
# instalar.sh - Instala o EIGUIT no Linux
#
# Uso (na pasta do EIGUIT):
#     bash instalar.sh                 instala tudo e cria o atalho no menu
#     bash instalar.sh --sem-sistema   pula os pacotes do sistema (sem sudo)
#     bash instalar.sh --desinstalar   remove atalho, comando e ambiente .venv
#
# O que faz, em ordem:
#   1. Instala os pacotes do sistema que o app precisa (apt, dnf, pacman ou
#      zypper): compilador + PortAudio para o pyaudio, Tk, OpenGL e ffmpeg
#   2. Instala o uv (gerenciador de Python do projeto), se ainda nao houver
#   3. Cria o ambiente .venv com o Python 3.12 e as versoes do uv.lock
#   4. Pergunta a URL do banco (login) e grava em ~/.config/EIGUIT/banco.txt
#   5. Cria o comando "eiguit" e o atalho no menu de aplicativos
# =============================================================================
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_USUARIO="$HOME/.local/bin"
COMANDO="$BIN_USUARIO/eiguit"
ATALHO="$HOME/.local/share/applications/eiguit.desktop"
PASTA_CONFIG="$HOME/.config/EIGUIT"   # o mesmo lugar que BD/gerenciador_remoto_db.py le
PATH_ORIGINAL="$PATH"

passo() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
aviso() { printf '\033[1;33m%s\033[0m\n' "$*"; }
erro()  { printf '\n\033[1;31mERRO: %s\033[0m\n' "$*" >&2; exit 1; }

# --------------------------------------------------------------- desinstalar
if [[ "${1:-}" == "--desinstalar" ]]; then
    passo "Removendo o EIGUIT do sistema"
    rm -f "$COMANDO" "$ATALHO"
    rm -rf "$RAIZ/.venv"
    command -v update-desktop-database >/dev/null && \
        update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
    echo "Atalho, comando 'eiguit' e .venv removidos."
    echo "Seus perfis e a URL do banco continuam em $PASTA_CONFIG (apague a pasta se quiser)."
    exit 0
fi

[[ -f "$RAIZ/main.py" && -f "$RAIZ/pyproject.toml" ]] || \
    erro "rode este script de dentro da pasta do EIGUIT"
[[ $EUID -ne 0 ]] || erro "nao rode como root; o script pede sudo so quando precisa"

# ------------------------------------------------------- 1. pacotes do sistema
if [[ "${1:-}" != "--sem-sistema" ]]; then
    passo "Instalando pacotes do sistema (pode pedir sua senha)"
    if command -v apt-get >/dev/null; then
        sudo apt-get update
        sudo apt-get install -y build-essential python3-dev portaudio19-dev \
            libportaudio2 libsndfile1 python3-tk libgl1 libglib2.0-0 ffmpeg curl git
    elif command -v dnf >/dev/null; then
        sudo dnf install -y gcc gcc-c++ make python3-devel portaudio-devel \
            libsndfile python3-tkinter mesa-libGL glib2 curl git
        sudo dnf install -y ffmpeg-free 2>/dev/null || \
            aviso "ffmpeg nao instalado (opcional; so o download de referencias do Analisador usa)"
    elif command -v pacman >/dev/null; then
        sudo pacman -S --needed --noconfirm base-devel portaudio libsndfile tk \
            mesa glib2 ffmpeg curl git
    elif command -v zypper >/dev/null; then
        sudo zypper install -y gcc gcc-c++ make python3-devel portaudio-devel \
            libsndfile1 python3-tk Mesa-libGL1 glib2 curl git
        sudo zypper install -y ffmpeg 2>/dev/null || sudo zypper install -y ffmpeg-7 2>/dev/null || \
            aviso "ffmpeg nao instalado (opcional; so o download de referencias do Analisador usa)"
    else
        aviso "Gerenciador de pacotes nao reconhecido. Instale manualmente: compilador C,"
        aviso "PortAudio (com cabecalhos de desenvolvimento), Tk, libGL e ffmpeg."
    fi
fi

# ------------------------------------------------------------------- 2. uv
passo "Conferindo o uv"
export PATH="$BIN_USUARIO:$HOME/.cargo/bin:$PATH"
if ! command -v uv >/dev/null; then
    echo "Instalando o uv (https://docs.astral.sh/uv/)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$BIN_USUARIO:$HOME/.cargo/bin:$PATH"
fi
command -v uv >/dev/null || erro "o uv nao ficou disponivel; instale-o e rode de novo"
uv --version

# ---------------------------------------------------------- 3. dependencias
passo "Instalando as dependencias Python (primeira vez demora alguns minutos)"
cd "$RAIZ"
uv sync --frozen || uv sync
.venv/bin/python -c "import pygame, cv2, sounddevice, soundfile, customtkinter, librosa, tinysoundfont" \
    >/dev/null 2>&1 || erro "as dependencias foram instaladas, mas alguma nao carrega (veja acima)"
echo "Dependencias OK."

# ---------------------------------------------------------------- 4. banco
passo "Banco de dados do login"
ARQ_BANCO="$PASTA_CONFIG/banco.txt"
if [[ -s "$ARQ_BANCO" || -n "${EIGUIT_DB_URL:-}" ]]; then
    echo "URL do banco ja configurada."
else
    echo "O EIGUIT pede login, que usa um banco PostgreSQL na nuvem."
    read -r -p "Cole a URL do banco (postgresql://...) ou Enter para pular: " URL || URL=""
    if [[ -n "$URL" ]]; then
        mkdir -p "$PASTA_CONFIG"
        printf '%s\n' "$URL" > "$ARQ_BANCO"
        chmod 600 "$ARQ_BANCO"
        echo "Gravado em $ARQ_BANCO"
    else
        aviso "Pulado. Sem a URL o login nao conecta; crie $ARQ_BANCO depois."
    fi
fi

# --------------------------------------------------------------- 5. atalhos
passo "Criando o comando 'eiguit' e o atalho no menu"
mkdir -p "$BIN_USUARIO" "$(dirname "$ATALHO")"
cat > "$COMANDO" <<EOF
#!/usr/bin/env bash
# Gerado pelo instalar.sh: o app usa caminhos relativos a pasta do projeto
cd "$RAIZ" && exec "$RAIZ/.venv/bin/python" main.py "\$@"
EOF
chmod +x "$COMANDO"

cat > "$ATALHO" <<EOF
[Desktop Entry]
Type=Application
Name=EIGUIT
GenericName=Estudio de guitarra
Comment=Braco interativo, campo harmonico, tablatura, estudos e jogos
Exec=$COMANDO
Path=$RAIZ
Icon=$RAIZ/assets/images/icone.png
Terminal=false
Categories=AudioVideo;Audio;Music;
EOF
chmod +x "$ATALHO"
command -v update-desktop-database >/dev/null && \
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

passo "Pronto!"
echo "Abra pelo menu de aplicativos (EIGUIT) ou digite: eiguit"
case ":$PATH_ORIGINAL:" in
    *":$BIN_USUARIO:"*) ;;
    *) aviso "Obs.: $BIN_USUARIO nao esta no seu PATH; abra um terminal novo ou use $COMANDO" ;;
esac
