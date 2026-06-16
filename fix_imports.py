import os

def fix_imports(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    replacements = {
        'from core ': 'from core ',
        'import core ': 'import core ',
        'from core.': 'from core.',
        'import core.': 'import core.',
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
            fix_imports(os.path.join(root, file))
print("Second pass import fix completed.")