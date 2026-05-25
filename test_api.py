import urllib.request, json, os

test_img = r'C:\Users\dayzi\.openclaw\media\outbound\jugg_main_girl_00001.png'
if not os.path.exists(test_img):
    test_img = r'C:\Users\dayzi\.openclaw\media\outbound\jugg_boutique_00001.png'

try:
    import requests
    with open(test_img, 'rb') as f:
        r = requests.post('http://127.0.0.1:8000/caption', files={'file': ('test.png', f, 'image/png')}, timeout=10)
    print(f'HTTP {r.status_code}')
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f'Error: {e}')
