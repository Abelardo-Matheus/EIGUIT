import os

def fix_imports2(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    replacements = {
        'from ui import': 'from ui import',
        'import ui': 'import ui',
        'from core.modulos import': 'from core.modulos import',
        'import core.modulos': 'import core.modulos',
        'from audio import': 'from audio import',
        'import audio': 'import audio',
        'from core import': 'from core import',
        'import core': 'import core'
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
            fix_imports2(os.path.join(root, file))
print("Third pass import fix completed.")