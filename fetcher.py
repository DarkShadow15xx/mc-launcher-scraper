import urllib.request
import urllib.parse
import re
import json
import time
import os

def fetch_page(url, data=None, retries=3):
    """Fetches a page with a longer timeout and retry logic."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0'}
    encoded_data = urllib.parse.urlencode(data).encode('utf-8') if data else None
    
    for i in range(retries):
        try:
            # Increased timeout to 30 seconds
            req = urllib.request.Request(url, data=encoded_data, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode('utf-8', errors='ignore')
        except Exception as e:
            if i < retries - 1:
                print(f"Retry {i+1} for {url} due to: {e}")
                time.sleep(2) # Wait 2 seconds before trying again
            else:
                print(f"Final error at {url}: {e}")
                return ""

def download_file(url, folder="vanilla"):
    """Downloads the file from the URL into the specified folder."""
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    filename = url.split('/')[-1]
    filepath = os.path.join(folder, filename)
    
    print(f"Downloading to {filepath}...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0'}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        # Using a longer timeout for the actual download too
        with urllib.request.urlopen(req, timeout=60) as response, open(filepath, 'wb') as out_file:
            out_file.write(response.read())
        print("Download complete!")
        return filepath
    except Exception as e:
        print(f"Failed to download: {e}")
        return None

def get_direct_apk_link(target_version):
    JSON_URL = "https://mc-launcher-scraper.vercel.app/mc_versions.json"
    
    json_raw = fetch_page(JSON_URL)
    if not json_raw: return "Could not reach version database."
    
    versions = json.loads(json_raw)
    article_url = next((v['link'] for v in versions if v['version'] == target_version), None)
    
    if not article_url: return "Version not in JSON."
    print(f"Step 1: Article -> {article_url}")

    article_html = fetch_page(article_url)
    if not article_html: return "Failed to load article page."
    
    form_match = re.search(r'action="(/getfile/[^"]+)"', article_html)
    if not form_match: return "Could not find download form."
    
    getfile_url = "https://mcpedl.org" + form_match.group(1)
    hidden_inputs = re.findall(r'name="([^"]+)"\s+value="([^"]*)"', article_html)
    form_data = {name: val for name, val in hidden_inputs}
    
    print(f"Step 2: Submitting Form to -> {getfile_url}")

    download_page_html = fetch_page(getfile_url, data=form_data)
    if not download_page_html: return "Failed to load download gateway."
    
    final_link_match = re.search(r"https://mcpedl\.org/uploads_files/[^']+?\.apk", download_page_html)
    
    final_link = None
    if final_link_match:
        final_link = final_link_match.group(0)
    else:
        final_link_match = re.search(r'https://mcpedl\.org/uploads_files/[^"]+?\.apk', download_page_html)
        if final_link_match:
            final_link = final_link_match.group(0)

    if final_link:
        print(f"Step 3: Success! Snipped from JS -> {final_link}")
        return download_file(final_link)

    return "Failed to find final APK link."

if __name__ == "__main__":
    result = get_direct_apk_link("0.1.0")
    print(f"Result: {result}")
