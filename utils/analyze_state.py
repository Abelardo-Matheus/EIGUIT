import json
import re

with open('song_page.html', 'r', encoding='utf-8') as f:
    content = f.read()

match = re.search(r'<script id="state" type="application/json">(.*?)</script>', content)
if match:
    state = json.loads(match.group(1))
    with open('state_dump.json', 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)
    print("State dumped to state_dump.json")
else:
    print("State not found")
