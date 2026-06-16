import os
import shutil

def mkdir(p): os.makedirs(p, exist_ok=True)

# Create Clean Architecture directories
mkdir('config')
mkdir('ui/components')
mkdir('ui/blocks')
mkdir('core')
mkdir('core/modulos')
mkdir('audio')
mkdir('services/transcription')
mkdir('utils')
mkdir('scripts')
mkdir('assets/images')
mkdir('assets/audio')
mkdir('assets/fonts')

print("1. Tarefa 1: O 'Cofre' de Constantes (Design Tokens)")
if os.path.exists('Core/constantes_ui.py'):
    with open('Core/constantes_ui.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    themes, metrics, settings = [], [], []
    for line in lines:
        if '=' in line:
            var_name = line.split('=')[0].strip()
            if var_name.startswith('COR_') or var_name.startswith('FUNDO_') or 'AZUL_' in var_name or 'VERMELHO_' in var_name or 'VERDE_' in var_name or 'BRANCO' in var_name or 'PRETO' in var_name or 'MADEIRA' in var_name or 'CORES_' in var_name:
                themes.append(line)
            elif 'RADIUS' in var_name or 'PADDING' in var_name or 'ALTURA_' in var_name or 'LARGURA_' in var_name or 'OFFSET' in var_name:
                metrics.append(line)
            else:
                settings.append(line)
        else:
            settings.append(line)

    with open('config/theme.py', 'w', encoding='utf-8') as f: f.write("".join(themes))
    with open('config/ui_metrics.py', 'w', encoding='utf-8') as f: f.write("".join(metrics))
    with open('config/app_settings.py', 'w', encoding='utf-8') as f: f.write("".join(settings))

print("2. Tarefa 2: Fragmentação Atômica da Interface")
if os.path.exists('Interface/Componentes'):
    blocks = ['tablatura_view.py', 'guitar_neck.py']
    for item in os.listdir('Interface/Componentes'):
        if item.endswith('.py') and item != '__init__.py':
            src = os.path.join('Interface/Componentes', item)
            if item in blocks:
                shutil.move(src, os.path.join('ui/blocks', item))
            else:
                shutil.move(src, os.path.join('ui/components', item))

if os.path.exists('Interface'):
    for item in os.listdir('Interface'):
        if os.path.isfile(os.path.join('Interface', item)) and item != '__init__.py':
            shutil.move(os.path.join('Interface', item), os.path.join('ui', item))

print("3. Tarefa 3: Modularização de Domínios Core e Backend")
if os.path.exists('Core'):
    for item in os.listdir('Core'):
        if item.endswith('.py') and item != 'constantes_ui.py' and item != '__init__.py':
            shutil.move(os.path.join('Core', item), os.path.join('core', item))

if os.path.exists('AudioEngine'):
    for item in os.listdir('AudioEngine'):
        if item.endswith('.py') and item != '__init__.py':
            shutil.move(os.path.join('AudioEngine', item), os.path.join('audio', item))

if os.path.exists('TranscriptionService'):
    for item in os.listdir('TranscriptionService'):
        if item == 'Start-IA.ps1':
            shutil.move(os.path.join('TranscriptionService', item), os.path.join('scripts', item))
        elif item not in ['__pycache__', 'venv_ia']:
            shutil.move(os.path.join('TranscriptionService', item), os.path.join('services/transcription', item))

if os.path.exists('Tools'):
    for item in os.listdir('Tools'):
        if item.endswith('.py') and item != 'refactor_clean_arch.py':
            shutil.move(os.path.join('Tools', item), os.path.join('utils', item))

if os.path.exists('Modulos'):
    for item in os.listdir('Modulos'):
        if item.endswith('.py') and item != '__init__.py':
            shutil.move(os.path.join('Modulos', item), os.path.join('core/modulos', item))

print("4. Tarefa 4: Gestão de Ambientes e Assets")
if os.path.exists('Imagens'):
    for item in os.listdir('Imagens'):
        shutil.move(os.path.join('Imagens', item), os.path.join('assets/images', item))

if os.path.exists('Audios'):
    for item in os.listdir('Audios'):
        shutil.move(os.path.join('Audios', item), os.path.join('assets/audio', item))

with open('.gitignore', 'a', encoding='utf-8') as f:
    f.write('\n# Novos Ignores\nvenv*\n__pycache__/\n.env\nnode_modules/\ntemp_audio/\n')

print("5. Resolvendo Imports e Referências...")
def replace_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    replacements = {
        'from config.theme import *
from config.ui_metrics import *
from config.app_settings import *': 'from config.theme import *\nfrom config.ui_metrics import *\nfrom config.app_settings import *',
        'config.theme': 'config.theme',
        'from core.': 'from core.',
        'import core.': 'import core.',
        'from ui.blocks.guitar_neck': 'from ui.blocks.guitar_neck',
        'from ui.blocks.tablatura_view': 'from ui.blocks.tablatura_view',
        'from ui.components.': 'from ui.components.',
        'import ui.components.': 'import ui.components.',
        'from ui.components import': 'from ui.components import',
        'from ui.': 'from ui.',
        'import ui.': 'import ui.',
        'from core.modulos.': 'from core.modulos.',
        'import core.modulos.': 'import core.modulos.',
        'from audio.': 'from audio.',
        'import audio.': 'import audio.',
        'from services.transcription.': 'from services.transcription.',
        'import services.transcription.': 'import services.transcription.',
        'assets/images/': 'assets/images/',
        'assets/audio/': 'assets/audio/',
        'utils.': 'utils.',
    }
    
    new_content = content
    for old, new in replacements.items():
        new_content = new_content.replace(old, new)
        
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

for root, dirs, files in os.walk('.'):
    if 'venv' in root or '__pycache__' in root or '.git' in root or 'node_modules' in root:
        continue
    for file in files:
        if file.endswith('.py') or file.endswith('.json') or file.endswith('.md'):
            replace_in_file(os.path.join(root, file))

# Remover pastas antigas que ficaram vazias
for d in ['Core', 'Interface/Componentes', 'Interface', 'AudioEngine', 'TranscriptionService', 'Tools', 'Imagens', 'Audios', 'Modulos']:
    try:
        if os.path.exists(d) and not os.listdir(d):
            os.rmdir(d)
    except:
        pass

print("Reestruturação concluída com sucesso!")