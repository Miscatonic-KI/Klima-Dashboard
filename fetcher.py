import json
import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from google import genai

def fetch_all():
    with open('feeds.json', 'r', encoding='utf-8') as f:
        feeds = json.load(f)
    
    output_data = []
    all_titles_for_ai = []

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
                for entry in entries[:15]:
                    entry_title = entry.find('atom:title', ns)
                    entry_link = entry.find('atom:link', ns)
                    
                    if entry_title is not None and entry_title.text:
                        t_text = entry_title.text.strip()
                        if t_text and t_text.lower() != "null":
                            l_href = entry_link.attrib.get('href', '#') if entry_link is not None else '#'
                            clean_t = t_text.replace('<b>', '').replace('</b>', '').replace('&#39;', "'")
                            
                            feed_result["items"].append({
                                "title": clean_t,
                                "link": l_href
                            })
                            all_titles_for_ai.append(f"- {clean_t} (Link: {l_href})")
        except Exception as e:
            print(f"Fehler bei {feed['title']}: {e}")

        output_data.append(feed_result)

    now = datetime.now(timezone(timedelta(hours=1)))
    next_run = now + timedelta(hours=4)
    
    meta_info = {
        "last_updated": now.strftime("%d.%m.%Y, %H:%M Uhr"),
        "next_update": next_run.strftime("%d.%m.%Y, %H:%M Uhr")
    }

    final_output = {
        "meta": meta_info,
        "feeds": output_data
    }

    # 1. data.json speichern
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    # 2. KI-Zusammenfassung via Gemini generieren
    ai_summary_html = generate_ai_summary(all_titles_for_ai)

    # 3. summary.html speichern
    save_summary_html(meta_info, output_data, ai_summary_html)

def generate_ai_summary(titles_list):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Kein GEMINI_API_KEY gefunden. KI-Zusammenfassung wird übersprungen.")
        return "<p><em>KI-Zusammenfassung derzeit nicht verfügbar (API-Key fehlt).</em></p>"

    try:
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
Du bist ein professioneller Klima-Analyst. Analysiere die folgenden aktuellen Schlagzeilen und erstelle einen kompakten Krisen-Lagebericht in genau 3 Absätzen (Formatierung in sauberm HTML mit <p> und inline <a> Links zu den passenden Quellen aus den Daten):

1. Absatz: Die kritischsten Extremwetter-Ereignisse
2. Absatz: Fortschritte oder Rückschläge in der Klimaforschung
3. Absatz: Wirtschaftliche und politische Reaktionen

WICHTIG: 
- Verwende ausschließlich HTML-Tags (<p>, <a href="...">).
- Binde die entsprechenden Hyperlinks direkt im Text auf relevante Schlagwörter ein.
- Antworte direkt mit dem HTML-Code für die 3 Absätze, ohne ```html Fences.

Hier sind die aktuellen Schlagzeilen:
""" + "\n".join(titles_list[:60])

        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"Fehler bei der Gemini-API-Generierung: {e}")
        return f"<p><em>Fehler bei der KI-Generierung: {e}</em></p>"

def save_summary_html(meta_info, output_data, ai_summary_html):
    html_content = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Klima-Dashboard - Lagebericht & Feed</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; line-height: 1.6; background: #0f172a; color: #e2e8f0; }}
        h1, h2, h3 {{ color: #f8fafc; }}
        a {{ color: #38bdf8; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .meta {{ color: #94a3b8; font-size: 0.9em; margin-bottom: 25px; border-bottom: 1px solid #334155; padding-bottom: 15px; }}
        .ai-report {{ background: #1e293b; padding: 25px; border-radius: 8px; border-left: 4px solid #38bdf8; margin-bottom: 40px; }}
        ul {{ margin-bottom: 30px; }}
        li {{ margin-bottom: 8px; }}
    </style>
</head>
<body>
    <a href="index.html">← Zurück zum Dashboard</a>
    <h1>🌍 Klima Crisis-Tracker: Automatisch generierter Lagebericht</h1>
    <div class="meta">Datenstand: <strong>{meta_info["last_updated"]}</strong></div>

    <h2>🤖 KI-Krisen-Lagebericht (by Google Gemini)</h2>
    <div class="ai-report">
        {ai_summary_html}
    </div>

    <h2>📌 Rohdaten-Feeds</h2>
"""

    for feed in output_data:
        if feed["items"]:
            html_content += f"<h3>{feed['title']}</h3>\n<ul>\n"
            for item in feed["items"]:
                html_content += f'  <li><a href="{item["link"]}" target="_blank">{item["title"]}</a></li>\n'
            html_content += "</ul>\n"

    html_content += """
</body>
</html>
"""
    with open('summary.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

if __name__ == '__main__':
    fetch_all()
