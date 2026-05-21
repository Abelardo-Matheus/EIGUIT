import re
import json

def search():
    with open('song_page.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Static JSON files
    urls = re.findall(r'https://static\.songsterr\.com/[^\"\'\s]+\.json', content)
    print(f"JSON URLs: {urls}")
    
    # Look for any script with JSON-like blobs
    # Songsterr sometimes stores tab data in a script tag with a specific ID or type
    # Search for "measures" or "notes" in the text
    if "measures" in content:
        print("Found 'measures' in HTML")
    
    # Let's extract the state and look deeper
    match = re.search(r'<script id="state" type="application/json">(.*?)</script>', content)
    if match:
        state = json.loads(match.group(1))
        # Recurse and find where a large list of dicts with 'f' or 'fret' is
        def find_tab_data(obj, path=""):
            if isinstance(obj, dict):
                if 'f' in obj and 's' in obj and isinstance(obj['f'], (int, float)):
                    # Might be a note {f: fret, s: string}
                    return [(path, obj)]
                results = []
                for k, v in obj.items():
                    results.extend(find_tab_data(v, f"{path}.{k}" if path else k))
                return results
            elif isinstance(obj, list):
                if len(obj) > 20 and isinstance(obj[0], dict) and ('f' in obj[0] or 'm' in obj[0]):
                    return [(path, "Potential list of notes/measures")]
                results = []
                for i, item in enumerate(obj):
                    results.extend(find_tab_data(item, f"{path}[{i}]"))
                return results
            return []

        potential = find_tab_data(state)
        print(f"Potential tab data paths: {len(potential)}")
        for p in potential[:10]:
            print(f"  {p}")

if __name__ == "__main__":
    search()
