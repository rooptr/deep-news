import urllib.request
from bs4 import BeautifulSoup

def fetch_demo_headlines():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    test_feeds = {
        "BUSINESS STANDARD (Direct)": "https://www.business-standard.com/rss/latest.rss",
        "FINANCIAL EXPRESS (Direct)": "https://www.financialexpress.com/feed/",
        "MONEYCONTROL (Alternative)": "https://www.moneycontrol.com/rss/MCtopnews.xml"
    }

    for name, url in test_feeds.items():
        print(f"\n--- {name} ---")
        try:
            req = urllib.request.Request(url, headers=headers)
            xml = urllib.request.urlopen(req, timeout=10).read()
            soup = BeautifulSoup(xml, 'xml') # use xml parser to avoid warnings
            items = soup.find_all('item')[:2]
            
            if not items:
                print("No items found. Might be blocked or invalid XML.")
                continue
                
            for item in items:
                title = item.title.text.replace("<![CDATA[", "").replace("]]>", "").strip() if item.title else ""
                desc = item.description.text.replace("<![CDATA[", "").replace("]]>", "").strip() if item.description else "No description"
                
                # Clean HTML tags if any
                desc_soup = BeautifulSoup(desc, 'html.parser')
                clean_desc = desc_soup.get_text().strip()
                
                print(f"TITLE: {title}")
                print(f"DESC:  {clean_desc[:150]}...\n")
        except urllib.error.HTTPError as e:
            print(f"HTTP ERROR: {e.code} - {e.reason} (Likely blocked by Cloudflare)")
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    fetch_demo_headlines()
