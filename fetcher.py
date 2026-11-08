import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

def fetch_all():
    with open('feeds.json', 'r', encoding='utf-8') as f:
        feeds = json.load(f)
    
    output_data = []

    for feed in feeds:
        feed_result = {
            "category": feed.get("category", "Allgemein"),
            "title": feed.get("title"),
            "desc": feed.get("desc", ""),
            "url": feed.get("url"),
            "items": []
        }
        try:
            req = urllib.request.Request(feed["url"], headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                
                entries = root.findall('atom:entry', ns)
                for entry in entries[:20]:
                    entry_title = entry.find('atom:title', ns)
                    entry_link = entry.find('atom:link', ns)
                    
                    if entry_title is not None and entry_title.text:
                        t_text = entry_title.text.strip()
                        if t_text and t_text.lower() != "null":
                            l_href = entry_link.attrib.get('href', '#') if entry_link is not None else '#'
                            
                            feed_result["items"].append({
                                "title": t_text,
                                "link": l_href
                            })
        except Exception as e:
            print(f"Fehler bei {feed['title']}: {e}")

        output_data.append(feed_result)

    # Zeitstempel für den aktuellen Stand und das nächste Update (+4 Stunden)
    now = datetime.now(timezone(timedelta(hours=1))) # MEZ/MESZ (Beispiel Berlin, oder UTC nutzen)
    next_run = now + timedelta(hours=4)
    
    meta_info = {
        "last_updated": now.strftime("%d.%m.%Y, %H:%M Uhr"),
        "next_update": next_run.strftime("%d.%m.%Y, %H:%M Uhr")
    }

    final_output = {
        "meta": meta_info,
        "feeds": output_data
    }

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    fetch_all()
