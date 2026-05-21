import re
import json

with open('state_dump.json', 'r', encoding='utf-8') as f:
    state = f.read()

urls = re.findall(r'https?://[^\s\"\'<>]+', state)
for url in urls:
    print(url)
