import urllib.request
from bs4 import BeautifulSoup
import re
import os
import json
import warnings
from bs4 import XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

papers = {
    "et.pdf": "https://dailyepaper.in/economic-times-newspaper-today-2026/",
    "bs.pdf": "https://dailyepaper.in/business-standard-epaper-feb-2026/",
    "fe.pdf": "https://dailyepaper.in/financial-express-newspaper-free-download-2026/",
    "mint.pdf": "https://dailyepaper.in/live-mint-epaper-feb-2026/",
    "eenadu.pdf": "https://dailyepaper.in/eenadu-epaper-free-download-2026/"
}

def fetch_paper(filename, url):
    print(f"\nFetching {filename} from {url} ...")
    
    slug = url.strip('/').split('/')[-1]
    api_url = f"https://dailyepaper.in/wp-json/wp/v2/posts?slug={slug}"
    
    req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        response = urllib.request.urlopen(req).read()
        data = json.loads(response)
        html = data[0]['content']['rendered']
        soup = BeautifulSoup(html, 'html.parser')
        
        links = soup.find_all('a', href=True)
        drive_link = None
        for a in links:
            if 'drive.google' in a['href'] and 'Download' in a.text:
                drive_link = a['href']
                break
                
        if drive_link:
            match = re.search(r'/d/([a-zA-Z0-9_-]+)', drive_link)
            if match:
                file_id = match.group(1)
                direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                print(f"Downloading {filename}...")
                urllib.request.urlretrieve(direct_url, filename)
                size = os.path.getsize(filename)
                print(f"Success! Downloaded {filename} ({size / 1024 / 1024:.2f} MB)")
            else:
                print(f"Could not extract file ID for {filename}.")
        else:
            print(f"No drive link found for {filename}.")
    except Exception as e:
        print(f"Error fetching {filename}: {e}")

def fetch_gold_rate():
    print("\nFetching 24K Gold Rate from goodreturns.in ...")
    url = "https://www.goodreturns.in/gold-rates/"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req).read()
        soup = BeautifulSoup(html, 'html.parser')
        
        tables = soup.find_all('table')
        for t in tables:
            if '24K' in t.text and 'Gram' in t.text:
                tds = t.find_all('td')
                for td in tds:
                    if '₹' in td.text:
                        price = td.text.strip().replace(',', '')
                        match = re.search(r'₹\s*(\d+)', price)
                        if match:
                            rate = f"₹{int(match.group(1)):,}"
                            with open('gold_rate.json', 'w', encoding='utf-8') as f:
                                json.dump({'rate': rate}, f)
                            print(f"Success! Gold Rate is {rate.encode('ascii', 'ignore').decode('ascii')}")
                            return
        print("Could not find the gold rate in the tables.")
    except Exception as e:
        print(f"Error fetching gold rate: {e}")

def fetch_headlines():
    print("\nFetching Top Headlines ...")
    headlines_data = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }

    # 1. Economic Times (RSS)
    try:
        req = urllib.request.Request('https://economictimes.indiatimes.com/rssfeedsdefault.cms', headers=headers)
        xml = urllib.request.urlopen(req, timeout=10).read()
        soup = BeautifulSoup(xml, 'html.parser')
        items = soup.find_all('item')[:10]
        for item in items:
            title = item.title.text.strip() if item.title else ""
            title = title.replace("<![CDATA[", "").replace("]]>", "").strip()
            if title: headlines_data.append({"paper": "ECONOMIC TIMES", "title": title})
        print(f"Fetched {len(items)} headlines from Economic Times")
    except Exception as e:
        print(f"Error fetching ET headlines: {e}")

    # 2. Business Standard (via Google News RSS to bypass Cloudflare and Bing blocks)
    try:
        bs_query = urllib.parse.quote('site:business-standard.com')
        req = urllib.request.Request(f'https://news.google.com/rss/search?q={bs_query}&hl=en-IN&gl=IN&ceid=IN:en', headers=headers)
        xml = urllib.request.urlopen(req, timeout=10).read()
        soup = BeautifulSoup(xml, 'html.parser')
        items = soup.find_all('item')[:10]
        for item in items:
            title = item.title.text.strip() if item.title else ""
            title = title.replace("<![CDATA[", "").replace("]]>", "").strip()
            if title: headlines_data.append({"paper": "BUSINESS STANDARD", "title": title})
        print(f"Fetched {len(items)} headlines from Business Standard")
    except Exception as e:
        print(f"Error fetching Business Standard headlines: {e}")

    # 3. Mint (RSS)
    try:
        req = urllib.request.Request('https://www.livemint.com/rss/news', headers=headers)
        xml = urllib.request.urlopen(req, timeout=10).read()
        soup = BeautifulSoup(xml, 'html.parser')
        items = soup.find_all('item')[:10]
        for item in items:
            title = item.title.text.strip() if item.title else ""
            title = title.replace("<![CDATA[", "").replace("]]>", "").strip()
            if title: headlines_data.append({"paper": "MINT", "title": title})
        print(f"Fetched {len(items)} headlines from Mint")
    except Exception as e:
        print(f"Error fetching Mint headlines: {e}")

    # 4. Financial Express (via Google News RSS to bypass Cloudflare and Bing blocks)
    try:
        fe_query = urllib.parse.quote('site:financialexpress.com')
        req = urllib.request.Request(f'https://news.google.com/rss/search?q={fe_query}&hl=en-IN&gl=IN&ceid=IN:en', headers=headers)
        xml = urllib.request.urlopen(req, timeout=10).read()
        soup = BeautifulSoup(xml, 'html.parser')
        items = soup.find_all('item')[:10]
        for item in items:
            title = item.title.text.strip() if item.title else ""
            title = title.replace("<![CDATA[", "").replace("]]>", "").strip()
            if title: headlines_data.append({"paper": "FINANCIAL EXPRESS", "title": title})
        print(f"Fetched {len(items)} headlines from Financial Express")
    except Exception as e:
        print(f"Error fetching Financial Express headlines: {e}")

    with open('headlines.json', 'w', encoding='utf-8') as f:
        json.dump(headlines_data, f, indent=2)
    print(f"Saved {len(headlines_data)} total headlines to headlines.json")

def fetch_market_stats():
    print("\nFetching Live Market Stats from Yahoo Finance...")
    symbols = {
        "NIFTY 50": "^NSEI",
        "SENSEX": "^BSESN",
        "USD/INR": "INR=X",
        "BRENT CRUDE": "BZ=F",
        "S&P 500": "^GSPC",
        "US 10Y BOND": "^TNX",
        "VIX": "^VIX",
        "GOLD": "GC=F",
        "MOODY'S": "MCO",
        "BANK OF AMERICA": "BAC"
    }
    
    market_data = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    for display_name, symbol in symbols.items():
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        req = urllib.request.Request(url, headers=headers)
        try:
            res = urllib.request.urlopen(req, timeout=10).read()
            data = json.loads(res)
            meta = data['chart']['result'][0]['meta']
            price = meta['regularMarketPrice']
            prev_close = meta['chartPreviousClose']
            change = price - prev_close
            pct_change = (change / prev_close) * 100
            
            direction = "up" if change >= 0 else "down"
            
            # Format outputs
            if symbol == "INR=X":
                formatted_price = f"₹{price:.2f}"
            elif symbol == "^TNX":
                formatted_price = f"{price:.3f}%"
            elif symbol in ["^NSEI", "^BSESN", "^GSPC", "MCO"]:
                formatted_price = f"{price:,.2f}"
            else:
                formatted_price = f"${price:,.2f}"
                
            formatted_change = f"{change:+.2f} ({pct_change:+.2f}%)"
            if symbol == "^TNX":
                formatted_change = f"{change:+.3f}% ({pct_change:+.2f}%)"
                
            market_data.append({
                "name": display_name,
                "value": formatted_price,
                "change": formatted_change,
                "direction": direction
            })
            print(f"Fetched {display_name}: {formatted_price.replace('₹', 'Rs.')} ({formatted_change})")
        except Exception as e:
            print(f"Error fetching {display_name}: {e}")
            
    with open('market_stats.json', 'w', encoding='utf-8') as f:
        json.dump(market_data, f, indent=2)
    print("Saved market stats to market_stats.json")

if __name__ == "__main__":
    for filename, url in papers.items():
        fetch_paper(filename, url)
    fetch_gold_rate()
    fetch_headlines()
    fetch_market_stats()
