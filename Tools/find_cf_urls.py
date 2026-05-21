import re
content = open('song_page.html', encoding='utf-8').read()
urls = re.findall(r'https://[^\s\"\'<>]+cloudfront\.net/[^\s\"\'<>]+', content)
for url in urls:
    print(url)
