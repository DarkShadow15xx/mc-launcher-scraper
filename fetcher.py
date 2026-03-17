import urllib.request
import urllib.parse
import re
import json
import time
import os

def fetch_page(url, data=None, retries=3):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0'}
    encoded_data = urllib.parse.urlencode(data).encode('utf-8') if data else None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, data=encoded_data, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode('utf-8', errors='ignore')
        except Exception as e:
            if i < retries - 1:
                time.sleep(2)
            else:
                return ""

def download_file(url, folder="vanilla"):
    if not os.path.exists(folder):
        os.makedirs(folder)
    filename = url.split('/')[-1]
    filepath = os.path.join(folder, filename)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0'}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as response, open(filepath, 'wb') as out_file:
            out_file.write(response.read())
        return filepath
    except Exception as e:
        return None

def get_direct_apk_link(target_version):
    JSON_URL = "https://mc-launcher-scraper.vercel.app/mc_versions.json"
    json_raw = fetch_page(JSON_URL)
    if not json_raw: return "Error: DB Unreachable"
    
    versions = json.loads(json_raw)
    article_url = next((v['link'] for v in versions if v['version'] == target_version), None)
    
    if not article_url: return f"Error: Version {target_version} not found in JSON"

    article_html = fetch_page(article_url)
    form_match = re.search(r'action="(/getfile/[^"]+)"', article_html)
    if not form_match: return "Error: No form"
    
    getfile_url = "https://mcpedl.org" + form_match.group(1)
    hidden_inputs = re.findall(r'name="([^"]+)"\s+value="([^"]*)"', article_html)
    form_data = {name: val for name, val in hidden_inputs}
    
    download_page_html = fetch_page(getfile_url, data=form_data)
    final_link_match = re.search(r"https://mcpedl\.org/uploads_files/[^']+?\.apk", download_page_html)
    
    final_link = None
    if final_link_match:
        final_link = final_link_match.group(0)
    
    if final_link:
        # Rename the downloaded file to exactly the version number for clone_mc.py
        target_path = os.path.join("vanilla", f"{target_version}.apk")
        downloaded_path = download_file(final_link)
        if downloaded_path:
            os.rename(downloaded_path, target_path)
            return target_path

    return "Error: Final Link not found"

if __name__ == "__main__":
    # GET VERSION FROM GITHUB ACTION ENV
    target = os.getenv("TARGET_VERSION", "1.20.10") 
    print(f"Workflow triggered for version: {target}")
    result = get_direct_apk_link(target)
    print(f"Result: {result}")
