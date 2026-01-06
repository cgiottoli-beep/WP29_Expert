import requests
try:
    from bs4 import BeautifulSoup
    print("BS4 available")
except ImportError:
    print("BS4 NOT available")

try:
    import pandas as pd
    print("Pandas available")
except ImportError:
    print("Pandas NOT available")

url = "https://globalautoregs.com/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        html = response.text
        idx = html.find("Upcoming Meetings")
        if idx != -1:
            print("FOUND Upcoming Meetings at index", idx)
            print("--- HTML CONTEXT ---")
            print(html[idx:idx+2000]) # Print next 2000 chars
        else:
            print("Upcoming Meetings NOT FOUND in text.")
                
except Exception as e:
    print(f"Error: {e}")
