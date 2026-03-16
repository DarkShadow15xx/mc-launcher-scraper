import urllib.request
import re
import json
import time
import os

def fetch_page(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0 Safari/537.36'}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8', errors='ignore')
    except:
        return ""

def identify_type(version_str, title_text):
    title_low = title_text.lower()
    parts = version_str.split('.')
    if len(parts) >= 4:
        return "Beta"
    if 'hotfix' in title_low or 'patch' in title_low:
        return "Hotfix"
    if any(word in title_low for word in ['beta', 'preview', 'pre-release']):
        return "Beta"
    return "Full Release"

def scrape_all_versions():
    filename = 'mc_versions.json'
    existing_data = []
    
    # 1. Load existing data if it exists
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        max_pages = 1  # Only scrape page 1 if we already have data
        print(f"Existing file found. Scraping only page 1 to update...")
    else:
        max_pages = 62 # First time run
        print(f"No existing file. Performing deep scrape of {max_pages} pages...")

    new_results = []
    seen_links = set()
    
    # Track links we already have in the file so we don't duplicate
    for item in existing_data:
        seen_links.add(item['link'])

    for page in range(1, max_pages + 1):
        url = f"https://mcpedl.org/downloading/page/{page}/" if page > 1 else "https://mcpedl.org/downloading/"
        print(f"Scanning Page {page}...")
        
        html = fetch_page(url)
        if not html: break

        blocks = re.findall(r'<article.*?>.*?</article>', html, re.DOTALL)
        if not blocks:
            blocks = [html] 

        for block in blocks:
            version_finds = re.findall(r'(\d+\.\d+\.\d+(?:\.\d+)?)', block)
            link_match = re.search(r'href="([^"]+)"', block)
            
            if version_finds and link_match:
                v_num = version_finds[0]
                link = link_match.group(1)
                if not link.startswith('http'):
                    link = "https://mcpedl.org" + link
                
                if link not in seen_links:
                    title_search = re.search(r'>(.*?)</a>', block)
                    title = title_search.group(1) if title_search else f"Minecraft PE {v_num}"
                    title = re.sub('<[^<]+?>', '', title).strip()
                    v_type = identify_type(v_num, title)
                    
                    new_results.append({
                        "title": title,
                        "version": v_num,
                        "type": v_type,
                        "link": link
                    })
                    seen_links.add(link)
        time.sleep(1)

    # 2. Combine old and new
    final_data = existing_data + new_results

    # 3. Sort everything (Newest versions at the top)
    final_data.sort(key=lambda x: [int(i) for i in x['version'].split('.') if i.isdigit()], reverse=True)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=4)
    
    print(f"Done! Added {len(new_results)} new versions. Total: {len(final_data)}")

if __name__ == "__main__":
    scrape_all_versions()
