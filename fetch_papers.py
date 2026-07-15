import urllib.request
from bs4 import BeautifulSoup
import re
import os
import json
import warnings
from bs4 import XMLParsedAsHTMLWarning
import gdown

import urllib.parse
import tempfile
import hashlib
import subprocess

MAX_PDF_BYTES = 100 * 1024 * 1024
ALLOWED_DOWNLOAD_HOSTS = {'drive.google.com', 'drive.usercontent.google.com'}
MANIFEST_FILE = 'pdf_manifest.json'

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
    
    domain = urllib.parse.urlparse(url).netloc
    slug = url.strip('/').split('/')[-1]
    api_url = f"https://{domain}/wp-json/wp/v2/posts?slug={slug}"
    
    req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
    def validate_pdf(path):
        size = os.path.getsize(path)
        if size == 0 or size > MAX_PDF_BYTES:
            raise ValueError(f"PDF size {size} is outside the allowed range")
        with open(path, 'rb') as pdf:
            if pdf.read(5) != b'%PDF-':
                raise ValueError("downloaded file is not a PDF")
        detected_type = subprocess.check_output(
            ['file', '--brief', '--mime-type', path], text=True).strip()
        if detected_type != 'application/pdf':
            raise ValueError(f"detected MIME type is {detected_type}")

    def validate_redirect(url_to_check):
        parsed = urllib.parse.urlparse(url_to_check)
        if parsed.scheme != 'https' or parsed.hostname not in ALLOWED_DOWNLOAD_HOSTS:
            raise ValueError(f"download host is not allowlisted: {url_to_check}")
        request = urllib.request.Request(url_to_check, headers={'User-Agent': 'Mozilla/5.0', 'Range': 'bytes=0-0'})
        with urllib.request.urlopen(request, timeout=30) as response:
            final = urllib.parse.urlparse(response.geturl())
            if final.scheme != 'https' or final.hostname not in ALLOWED_DOWNLOAD_HOSTS:
                raise ValueError(f"redirected to an unapproved host: {response.geturl()}")
            content_type = (response.headers.get_content_type() or '').lower()
            content_length = response.headers.get('Content-Length')
            # Google Drive may return an HTML confirmation page before gdown follows
            # through to the PDF. The final magic-byte check below remains mandatory.
            if content_type not in {'application/pdf', 'application/octet-stream', 'text/html'}:
                raise ValueError(f"unexpected content type: {content_type}")
            if content_length and int(content_length) > MAX_PDF_BYTES:
                raise ValueError("remote PDF exceeds size limit")

    def record_manifest(source_url, path):
        digest = hashlib.sha256()
        with open(path, 'rb') as pdf:
            for chunk in iter(lambda: pdf.read(1024 * 1024), b''):
                digest.update(chunk)
        manifest = {}
        if os.path.exists(MANIFEST_FILE):
            with open(MANIFEST_FILE, 'r', encoding='utf-8') as existing:
                manifest = json.load(existing)
        manifest[filename] = {
            'source_url': source_url,
            'source_sha256': digest.hexdigest(),
            'size_bytes': os.path.getsize(path)
        }
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False, dir='.', suffix='.manifest') as output:
            json.dump(manifest, output, indent=2)
            temp_manifest = output.name
        os.replace(temp_manifest, MANIFEST_FILE)

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
                
        # FALLBACK: If WP-JSON fails (like careerswave.in), scrape raw HTML for dates
        if not drive_link:
            raw_req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            raw_html = urllib.request.urlopen(raw_req).read().decode('utf-8', errors='ignore')
            matches = re.findall(r'(\d{2}-\d{2}-\d{4}).*?(https://drive\.google\.com/[^\s"\'<>]+)', raw_html, re.DOTALL)
            if matches:
                drive_link = matches[0][1]

        if drive_link:
            match = re.search(r'/d/([a-zA-Z0-9_-]+)', drive_link)
            if match:
                file_id = match.group(1)
                direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                print(f"Downloading {filename}...")
                validate_redirect(direct_url)
                temp_path = None
                try:
                    with tempfile.NamedTemporaryFile(suffix='.download', delete=False) as temp:
                        temp_path = temp.name
                    downloaded = gdown.download(direct_url, temp_path, quiet=False)
                    if not downloaded:
                        raise ValueError("download failed")
                    validate_pdf(temp_path)
                    os.replace(temp_path, filename)
                    temp_path = None
                    record_manifest(drive_link, filename)
                finally:
                    if temp_path and os.path.exists(temp_path):
                        os.remove(temp_path)
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

if __name__ == "__main__":
    for filename, url in papers.items():
        fetch_paper(filename, url)
    fetch_gold_rate()
    fetch_headlines()
