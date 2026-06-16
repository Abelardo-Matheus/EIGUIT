import re
import os

html_path = r'C:\Users\Usuario\.gemini\tmp\eiguit\tool-outputs\session-f29da994-3d93-4fca-9f9f-8fb716965b4e\run_shell_command_1779310308010_0.txt'
if not os.path.exists(html_path):
    # Fallback to local file if path is different
    html_path = 'revisions.html'

with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

urls = re.findall(r'https?://[^\s\"\'<>]+?\.(?:gp5|gp|mid|midi)', content)
for url in urls:
    print(url)

# Also check for data-download-url or similar
matches = re.findall(r'data-download-url=\"(.*?)\"', content)
for m in matches:
    print(f"Data-Download-URL: {m}")
