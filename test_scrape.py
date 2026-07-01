import urllib.request
from bs4 import BeautifulSoup
import re
import os

url = "https://dailyepaper.in/economic-times-newspaper-today-2026/"
print(f"Fetching {url} ...")
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    html = urllib.request.urlopen(req).read()
    soup = BeautifulSoup(html, 'html.parser')
    
    links = soup.find_all('a', href=True)
    drive_link = None
    for a in links:
        # We look for the first link that says 'Download' and goes to Google Drive
        if 'drive.google' in a['href'] and 'Download' in a.text:
            drive_link = a['href']
            break
            
    if drive_link:
        print(f"Found Latest Drive Link (Today's Paper): {drive_link}")
        
        # Extract File ID from Google Drive URL
        match = re.search(r'/d/([a-zA-Z0-9_-]+)', drive_link)
        if match:
            file_id = match.group(1)
            # Convert to a direct download link
            direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            print(f"Direct Download URL: {direct_url}")
            
            # Download the file
            print("Downloading as et.pdf...")
            urllib.request.urlretrieve(direct_url, "et.pdf")
            
            size = os.path.getsize("et.pdf")
            print(f"Success! Downloaded et.pdf ({size / 1024 / 1024:.2f} MB)")
        else:
            print("Could not extract file ID.")
    else:
        print("No drive link found.")
except Exception as e:
    print(f"Error: {e}")
