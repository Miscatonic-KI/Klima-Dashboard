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

    # Zeitstempel (MEZ/MESZ)
    now = datetime.now(timezone(timedelta(hours=1)))
    next_run = now + timedelta(hours=4)
    
    meta_info = {
        "last_updated": now.strftime("%d.%m.%Y, %H:%M Uhr"),
        "next_update": next_run.strftime("%d.%m.%Y, %H:%M Uhr")
    }

    # 1. JSON speichern
    final_output = {
        "meta": meta_info,
        "feeds": output_data
    }

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    # 2. Statische Text-Unterseite (summary.html) generieren
    generate_summary_html(meta_info, output_data)

def generate_summary_html(meta, feeds):
    categories = {}
    for feed in feeds:
        cat = feed.get("category", "Allgemein")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(feed)

    html_content = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crisis-Tracker | KI-Digest & Klartext-Übersicht</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f3f4f6; color: #111827; margin: 0; padding: 20px; line-height: 1.5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: #ffffff; padding: 25px; border-radius: 10px; border: 1px solid #e5e7eb; }}
        h1 {{ color: #8b0000; font-size: 1.6rem; margin-top: 0; }}
        .meta {{ color: #4b5563; font-size: 0.85rem; border-bottom: 2px solid #8b0000; padding-bottom: 10px; margin-bottom: 20px; }}
        h2 {{ color: #8b0000; font-size: 1.2rem; margin-top: 25px; border-bottom: 1px solid #e5e7eb; padding-bottom: 5px; }}
        h3 {{ font-size: 1rem; margin-top: 15px; margin-bottom: 8px; color: #111827; }}
        ul {{ padding-left: 20px; margin: 0 0 15px 0; font-size: 0.9rem; }}
        li {{ margin-bottom: 4px; }}
        a {{ color: #990000; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .back-link {{ display: inline-block; margin-bottom: 15px; font-weight: bold; color: #8b0000; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="container">
        <a href="index.html" class="back-link">← Zurück zum Haupt-Dashboard</a>
        <h1>🌍 Crisis-Tracker: Feed-Digest & Text-Archiv</h1>
        <div class="meta">
            Datenstand: <strong>{meta['last_updated']}</strong> | Nächste Aktualisierung: <strong>{meta['next_update']}</strong>
        </div>
        <p><em>Diese Seite enthält alle aktuellen Meldungen als strukturierten Klartext – optimal geeignet zum Überfliegen oder Kopieren für KI-Analysen.</em></p>
    """

    for cat_name, cat_feeds in categories.items():
        html_content += f"\n<h2>📌 {cat_name}</h2>"
        for feed in cat_feeds:
            html_content += f"\n<h3>{feed['title']}</h3>"
            if feed['items']:
                html_content += "\n<ul>"
                for item in feed['items']:
                    html_content += f"\n  <li><a href=\"{item['link']}\" target=\"_blank\">{item['title']}</a></li>"
                html_content += "\n</ul>"
            else:
                html_content += "\n<p><em>Keine aktuellen Meldungen.</em></p>"

    html_content += """
    </div>
</body>
</html>"""

    with open('summary.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

if __name__ == '__main__':
    fetch_all()
